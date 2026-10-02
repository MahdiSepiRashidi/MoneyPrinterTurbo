"""Supervisor CLI entry point.

Commands:
- serve: Run the scheduler + Telegram bot (FR-16)
- ingest-books <file>: Ingest book text into idea cards (FR-1)
- resume <run_id>: Resume a non-terminal DailyRun from checkpoint (FR-13)
"""

import sys
import argparse
from pathlib import Path

from supervisor.daily import create_daily_run
from supervisor.store import IdeaCard, IdeaCardStore
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
    
    # TODO: Start scheduler and Telegram bot (FR-16)
    # from supervisor.scheduler import start_scheduler
    # from supervisor.telegram_bot import start_bot
    # start_scheduler()
    # start_bot()
    
    print("Supervisor started (scheduler + bot not yet implemented)")
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
        print(f"  Re-run the same command to auto-resume (no --from-chunk needed).")

    return 0 if result.llm_errors == 0 else 1


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
    serve_parser = subparsers.add_parser("serve", help="Run scheduler + Telegram bot")
    
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
    
    # resume
    resume_parser = subparsers.add_parser("resume", help="Resume a DailyRun from checkpoint")
    resume_parser.add_argument("run_id", help="DailyRun ID to resume")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        return cmd_serve(args)
    elif args.command == "ingest-books":
        return cmd_ingest_books(args)
    elif args.command == "resume":
        return cmd_resume(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())