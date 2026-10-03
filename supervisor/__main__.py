"""Supervisor CLI entry point.

Commands:
- serve: Run the scheduler + Telegram bot (FR-16)
- ingest-books <file>: Ingest book text into idea cards (FR-1)
- pick-send: FR-2 manual bridge — pick 5 unused cards, send the numbered shortlist to Telegram, print the run_id
- lock-pick <run_id> <1-5>: FR-2 manual bridge — lock the operator's 1-5 choice on the day's run
- approve <run_id>: FR-5 manual bridge — pass the script gate so media stages may start
- rewrite <run_id>: FR-5 manual bridge — re-generate the script once, re-enter the gate
- reject <run_id>: FR-5 manual bridge — reject the reel, release the cards, flag day-missed
- resume <run_id>: Resume a non-terminal DailyRun from checkpoint (FR-13)
"""

import sys
import argparse
from pathlib import Path

from supervisor.daily import (
    lock_pick,
    register_deadline_job,
    register_pick_job,
    run_pick_job,
)
from supervisor.config import load_supervisor_config


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the supervisor: scheduler + Telegram bot."""
    cfg = load_supervisor_config()
    if not cfg.enabled:
        print("Supervisor is disabled (supervisor.enabled=false)")
        return 1
    if not cfg.telegram_bot_token or not cfg.telegram_chat_id:
        print("Telegram bot token and chat_id are required")
        return 1
    
    print("Starting supervisor...")
    print(f"  TTS voice: {cfg.tts_voice}")
    print(f"  Candidates LLM ranking: {cfg.candidates_llm_ranking}")
    print(f"  Candidates count: {cfg.candidates_count}")
    print(f"  Pick deadline (weekday): {cfg.pick_deadline_weekday}")
    print(f"  Pick deadline (Friday): {cfg.pick_deadline_friday}")
    print(f"  Post time (weekday): {cfg.post_time_weekday}")
    print(f"  Post time (Friday): {cfg.post_time_friday}")

    from supervisor.scheduler import Scheduler

    scheduler = Scheduler(tick_interval=cfg.poll_interval_seconds)
    register_pick_job(scheduler)
    register_deadline_job(scheduler)
    scheduler.start()
    print("Scheduler started; 08:00 Tehran pick job + deadline job registered (FR-2/FR-3).")

    # FR-15: full long-poll command bot (approve/rewrite/reject/ack-post/...).
    # from supervisor.telegram_bot import start_bot
    # start_bot()

    print("Supervisor started.")
    try:
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        scheduler.stop()
        return 0


def cmd_ingest_books(args: argparse.Namespace) -> int:
    """Ingest book text/PDF file into idea cards."""
    from supervisor.ingest import ingest_book

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    book_name = getattr(args, "book", None)
    skip_chunks = [int(x) for x in getattr(args, "skip_chunk", "").split(",") if x.strip()]
    result = ingest_book(
        file_path=file_path,
        book_name=book_name,
        max_chunks=args.max_chunks,
        from_chunk=args.from_chunk,  # None = auto-resume from checkpoint
        skip_chunks=skip_chunks,
    )

    print(f"\nBook: {result.book}")
    if args.from_chunk is None and result.start_chunk > 0 and result.processed_chunks > 0:
        print(f"  Resumed from checkpoint at chunk {result.start_chunk}")
    print(f"  Chunks: processed {result.processed_chunks} of {result.total_chunks} (start {result.start_chunk})")
    print(f"  New cards: {result.cards_created}")
    print(f"  Needs review: {result.cards_review}")
    print(f"  Vague cards dropped: {result.vague_dropped}")
    print(f"  Chunks rejected: {result.chunks_rejected}")
    print(f"  LLM errors: {result.llm_errors}")
    if result.skipped_chunks:
        print(f"  Skipped chunks: {result.skipped_chunks}")

    remaining = result.total_chunks - result.start_chunk - result.processed_chunks
    if remaining > 0:
        print(f"\n  Remaining: {remaining} chunk(s)")
        print("  Re-run the same command to auto-resume (no --from-chunk needed).")

    return 0 if result.llm_errors == 0 else 1


def cmd_pick_send(args: argparse.Namespace) -> int:
    """FR-2 manual bridge: pick 5 unused cards, send the numbered shortlist to Telegram."""
    from supervisor.store import DailyRunStore, IdeaCardStore as _ICS

    run = run_pick_job(store=DailyRunStore(), idea_store=_ICS())
    print(f"run_id: {run.run_id}")
    print(f"candidates: {len(run.candidate_card_ids)}")
    if run.last_error:
        print(f"warning: {run.last_error}")
    print("Check your Telegram for the numbered cards, then lock the pick with:")
    print(f"  uv run python -X utf8 -m supervisor lock-pick {run.run_id} <1-{max(len(run.candidate_card_ids), 1)}>")
    return 0


def cmd_lock_pick(args: argparse.Namespace) -> int:
    """FR-2 manual bridge: lock the operator's 1-5 choice on the day's run."""
    from supervisor.store import DailyRunStore

    try:
        run = lock_pick(args.run_id, args.number, store=DailyRunStore())
    except (KeyError, ValueError) as exc:
        print(str(exc))
        return 1
    print(f"locked: {run.run_id} -> card {run.picked_card_id} (picked_by={run.picked_by})")
    print(f"checkpoint: {run.checkpoint} (FR-5's 'approve' advances it)")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    """FR-5 manual bridge: pass the script gate so media stages may start."""
    from supervisor import approval
    from supervisor.store import DailyRunStore, IdeaCardStore

    try:
        run = approval.resolve_run(DailyRunStore(), run_id=args.run_id)
    except KeyError as exc:
        print(str(exc))
        return 1
    approval.approve(run, store=DailyRunStore(), idea_store=IdeaCardStore())
    print(f"approved: {run.run_id} -> checkpoint={run.checkpoint} (media gate released)")
    return 0


def cmd_rewrite(args: argparse.Namespace) -> int:
    """FR-5 manual bridge: re-generate the script once, re-enter the gate."""
    from supervisor import approval
    from supervisor.store import DailyRunStore, IdeaCardStore

    try:
        run = approval.resolve_run(DailyRunStore(), run_id=args.run_id)
    except KeyError as exc:
        print(str(exc))
        return 1
    approval.rewrite(run, store=DailyRunStore(), idea_store=IdeaCardStore())
    print(f"rewrote: {run.run_id} -> script_status={run.script_status} "
          f"rewrite_count={run.rewrite_count}")
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    """FR-5 manual bridge: reject the reel, release the cards, flag day-missed."""
    from supervisor import approval
    from supervisor.store import DailyRunStore, IdeaCardStore

    try:
        run = approval.resolve_run(DailyRunStore(), run_id=args.run_id)
    except KeyError as exc:
        print(str(exc))
        return 1
    approval.reject(run, store=DailyRunStore(), idea_store=IdeaCardStore())
    print(f"rejected: {run.run_id} -> post_status={run.post_status} "
          f"({len(run.candidate_card_ids)} cards released to unused)")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a DailyRun from checkpoint (FR-13)."""
    from supervisor.flow import TERMINAL_CHECKPOINT, resume_run

    cfg = load_supervisor_config()
    run_id = args.run_id
    print(f"Resuming run: {run_id}")
    try:
        run = resume_run(run_id, cfg=cfg)
    except KeyError as exc:
        print(f"  {exc}")
        return 1

    print(
        "  checkpoint={} post_status={} retry_count={} last_error={!r}".format(
            run.checkpoint, run.post_status, run.retry_count, run.last_error
        )
    )
    if run.checkpoint == TERMINAL_CHECKPOINT and run.post_status in ("posted", "scheduled"):
        print("  done - run is terminal.")
        return 0
    if run.last_error:
        print(f"  stopped at stage: {run.last_error}")
        print("  Retry later with: python -m supervisor resume " + run.run_id)
        return 1
    print("  nothing left to do (already terminal or no stages pending).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m supervisor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # serve
    subparsers.add_parser("serve", help="Run scheduler + Telegram bot")
    
    # ingest-books
    ingest_parser = subparsers.add_parser("ingest-books", help="Ingest book text/PDF into idea cards")
    ingest_parser.add_argument("file", help="Path to book file (.txt, .md, .pdf)")
    ingest_parser.add_argument("--book", default=None, help="Book name override (default: file stem)")
    ingest_parser.add_argument("--max-chunks", type=int, default=None, help="Process at most N chunks")
    ingest_parser.add_argument("--from-chunk", type=int, default=None,
                               help="Start at chunk index N (0-based). Omit to auto-resume from the last saved checkpoint.")
    ingest_parser.add_argument("--skip-chunk", default="",
                               help="Comma-separated 0-based chunk indices to skip WITHOUT calling the LLM "
                                    "(use for chunks the LLM refuses on content, e.g. explicit text). "
                                    "They are recorded in the progress store so auto-resume moves past them.")

    # pick-send / lock-pick (FR-2 manual bridge)
    subparsers.add_parser("pick-send", help="Pick 5 unused cards, send the numbered shortlist to Telegram")
    lock_parser = subparsers.add_parser("lock-pick", help="Lock the operator's 1-5 choice on a day's run")
    lock_parser.add_argument("run_id", help="DailyRun ID from pick-send")
    lock_parser.add_argument("number", type=int, help="1-based index into the day's candidate cards")

    # resume
    resume_parser = subparsers.add_parser("resume", help="Resume a DailyRun from checkpoint")
    resume_parser.add_argument("run_id", help="DailyRun ID to resume")

    # FR-5 manual bridge: approve / rewrite / reject
    for name, help_text in (
        ("approve", "FR-5: pass the script gate so media stages may start"),
        ("rewrite", "FR-5: re-generate the script once, re-enter the gate"),
        ("reject", "FR-5: reject the reel, release the cards, flag day-missed"),
    ):
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("run_id", help="DailyRun ID to act on")

    args = parser.parse_args()

    if args.command == "serve":
        return cmd_serve(args)
    elif args.command == "ingest-books":
        return cmd_ingest_books(args)
    elif args.command == "pick-send":
        return cmd_pick_send(args)
    elif args.command == "lock-pick":
        return cmd_lock_pick(args)
    elif args.command == "approve":
        return cmd_approve(args)
    elif args.command == "rewrite":
        return cmd_rewrite(args)
    elif args.command == "reject":
        return cmd_reject(args)
    elif args.command == "resume":
        return cmd_resume(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())