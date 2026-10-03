"""FR-4 on 5 REAL *The Game* cards after the skill's reframe rule change.

Uses the production default llm_fn (supervisor.llm.complete: gemini primary).

Run:  uv run python -X utf8 storage/temp/fr4_real_cards_test.py
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from supervisor.daily import _recent_hooks, choose_hook_type
from supervisor.scriptgen import count_farsi_words, generate_script
from supervisor.store import HookRotationStore, IdeaCardStore


def shift_date(iso_date: str, days: int) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=days)).isoformat()


def main() -> int:
    cards = IdeaCardStore().unused(limit=5)
    print(f"real store: {len(cards)} unused cards (book={cards[0].book})\n")

    hook_store = HookRotationStore()
    start_day = date.today() - timedelta(days=len(cards))
    summary = []
    full = []
    for i, card in enumerate(cards):
        test_date = shift_date(start_day.isoformat(), i + 1)
        hook_type = choose_hook_type(test_date, hook_store=hook_store, rng=random.Random(test_date))
        recent_hooks = _recent_hooks(hook_store, test_date)

        result = generate_script(card, hook_type, recent_hooks)  # default llm_fn = production path
        words = count_farsi_words(result.script_farsi)

        print(f"--- card {i + 1}/{len(cards)}: {card.id}  hook={hook_type}")
        print(f"    claim: {card.claim}")
        print(f"    status={result.status} approved={result.approved} words={words} flags={result.flags}")
        if result.script_farsi:
            print(f"    opening: {result.opening_line}")
        print()

        summary.append(
            {
                "card_id": card.id,
                "book": card.book,
                "claim": card.claim,
                "hook_type": hook_type,
                "status": result.status,
                "approved": result.approved,
                "words": words,
                "flags": result.flags,
            }
        )
        full.append({"card": card.to_dict(), "result": asdict(result)})

    out = Path("storage/temp/fr4_real_cards_result.json")
    out.write_text(
        json.dumps(
            {
                "approved_count": sum(1 for s in summary if s["approved"]),
                "summary": summary,
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
        print(f"  {s['card_id']}: {s['status']} words={s['words']} flags={s['flags']}")
    print(f"detail saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
