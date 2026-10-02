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
from supervisor.store import upsert_card, IdeaCard
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
    """Ingest book text file into idea cards."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1
    
    text = file_path.read_text(encoding="utf-8")
    
    # Split into ~3000-char chunks with 500-char overlap
    chunk_size = 3000
    overlap = 500
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk.strip()) > 100:  # Skip tiny chunks
            chunks.append(chunk)
    
    print(f"Split book into {len(chunks)} chunks")
    
    # TODO: Call LLM per chunk via supervisor.llm.complete
    # For now, just show the structure
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i+1}: {len(chunk)} chars - {chunk[:100]}...")
    
    if len(chunks) > 3:
        print(f"... and {len(chunks) - 3} more chunks")
    
    # TODO: Parse LLM JSON array, validate, generate deterministic IDs, upsert
    print("LLM ingestion not yet implemented")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a DailyRun from checkpoint."""
    run_id = args.run_id
    print(f"Resuming run: {run_id}")
    # TODO: Load DailyRun, continue at checkpoint
    print("Resume not yet implemented")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m supervisor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # serve
    serve_parser = subparsers.add_parser("serve", help="Run scheduler + Telegram bot")
    
    # ingest-books
    ingest_parser = subparsers.add_parser("ingest-books", help="Ingest book text into idea cards")
    ingest_parser.add_argument("file", help="Path to book text file")
    
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