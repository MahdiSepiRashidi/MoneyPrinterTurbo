"""FR-4 manual test: generate a Farsi reel script for 5 unused idea cards.

Run:  uv run python -X utf8 storage/temp/fr4_five_cards_test.py
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from supervisor.daily import _recent_hooks, choose_hook_type, HOOK_TYPES
from supervisor.scriptgen import count_farsi_words, generate_script
from supervisor.store import HookRotationStore, IdeaCardStore


def shift_date(iso_date: str, days: int) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=days)).isoformat()


def main() -> int:
    idea_store = IdeaCardStore()
    cards = idea_store.unused(limit=5)
    if len(cards) < 5:
        print(f"only {len(cards)} unused cards available")
        return 1

    hook_store = HookRotationStore()
    start_day = date.today() - timedelta(days=len(cards))
    print(f"generating FR-4 scripts for {len(cards)} cards\n")

    summary = []
    full = []
    for i, card in enumerate(cards):
        test_date = shift_date(start_day.isoformat(), i + 1)
        hook_type = choose_hook_type(test_date, hook_store=hook_store, rng=random.Random(test_date))
        recent_hooks = _recent_hooks(hook_store, test_date)

        print(f"--- card {i + 1}/{len(cards)}: {card.id}")
        print(f"    book={card.book}  lesson={card.lesson or '-'}")
        print(f"    claim={card.claim[:100]}")
        print(f"    hook_type={hook_type}  (rotated for {test_date})")

        result = generate_script(card, hook_type, recent_hooks)
        words = count_farsi_words(result.script_farsi)

        print(f"    llm_status={result.status}  approved={result.approved}  words={words}")
        print(f"    flags={result.flags}")
        print(f"    target_seconds={result.target_seconds}")
        print(f"    opening_line={result.opening_line}")
        print("    script_farsi:")
        for line in result.script_farsi.splitlines():
            print(f"      {line}")
        print(f"    caption={result.caption}")
        print(f"    hashtags={result.hashtags}")
        print()

        full.append(
            {
                "card": card.to_dict(),
                "test_date": test_date,
                "result": asdict(result),
                "approved": result.approved,
                "word_count": words,
            }
        )

        summary.append(
            {
                "card_id": card.id,
                "hook_type": hook_type,
                "status": result.status,
                "approved": result.approved,
                "words": words,
                "flags": result.flags,
            }
        )

    out = Path("storage/temp/fr4_five_cards_result.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "cards": [c.id for c in cards],
                "summary": summary,
                "approved_count": sum(1 for s in summary if s["approved"]),
                "results": full,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print(f"approved: {sum(1 for s in summary if s['approved'])} / {len(summary)}")
    for s in summary:
        print(f"  {s['card_id']}: {s['status']} words={s['words']} hook={s['hook_type']} flags={s['flags']}")
    print(f"detail saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
