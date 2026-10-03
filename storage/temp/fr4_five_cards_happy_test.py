"""FR-4 happy-path test: 5 wholesome (meta-safe) idea cards in a TEMP store.

The real store's cards all come from 'The Game' (PUA book) which the
meta-safety guardrail of the skill rejects, so this test uses a temp
IdeaCardStore to demonstrate actual script generation end-to-end.

Run:  uv run python -X utf8 storage/temp/fr4_five_cards_happy_test.py
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
from supervisor.store import HookRotationStore, IdeaCard, IdeaCardStore

TEMP_STORE_DIR = "storage/temp/fr4_test_store"

WHOLESALE_CARDS = [
    {
        "id": "happy-0001",
        "book": "How to Win Friends and Influence People",
        "claim": "Genuine interest in others is more socially effective than trying to be liked by impressing them.",
        "quote": "You can make more friends in two months by becoming interested in other people than you can in two years by trying to get other people interested in you.",
        "example": "A man who started asking each new colleague about their work history instead of pitching himself found the room felt warmer within a week.",
        "lesson": "Lead conversations with curiosity about the other person, not with self-presentation.",
        "type": "principle",
    },
    {
        "id": "happy-0002",
        "book": "Nonviolent Communication",
        "claim": "Listening to understand, not to reply, is a trainable skill that lowers social anxiety over time.",
        "quote": "Most people listen not to understand, but to reply.",
        "example": "Someone who practiced a silent self-check after a stressful conversation (what did I actually hear, what do I think?) reported the tension dropping.",
        "lesson": "Pause before replying; reflect back what you heard first.",
        "type": "tip",
    },
    {
        "id": "happy-0003",
        "book": "Deep Conversations",
        "claim": "Small, consistent social acts compound into general comfort with strangers.",
        "quote": "Comfort with strangers is built by reps, not by personality.",
        "example": "A quiet guy who greeted his barista by name for three months could later hold a five-minute chat at a coffee shop without thinking about it.",
        "lesson": "Pick one small daily social rep and do it until it feels normal.",
        "type": "principle",
    },
    {
        "id": "happy-0004",
        "book": "The Courage to Be Disliked",
        "claim": "Naming an emotion in the moment lowers its intensity (affect labeling).",
        "quote": "Putting a feeling into words calms the limbic system.",
        "example": "Saying to yourself 'I am nervous' before a meeting makes the nerves easier to work with than fighting them.",
        "lesson": "Label the emotion instead of fighting it.",
        "type": "insight",
    },
    {
        "id": "happy-0005",
        "book": "Atomic Habits",
        "claim": "Scheduling social time as an appointment makes it actually happen.",
        "quote": "You do not rise to the level of your goals; you fall to the level of your systems.",
        "example": "A guy who put 'walk with a friend' in his calendar on Thursday ended up going more often than when it was just a vague 'I should hang out'.",
        "lesson": "Put social time in the calendar, not in your thoughts.",
        "type": "tip",
    },
]


def shift_date(iso_date: str, days: int) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=days)).isoformat()


def main() -> int:
    idea_store = IdeaCardStore(TEMP_STORE_DIR)
    for c in WHOLESALE_CARDS:
        idea_store.upsert_card(IdeaCard(**c))

    cards = idea_store.unused(limit=5)
    hook_store = HookRotationStore()
    start_day = date.today() - timedelta(days=len(cards))
    print(f"FR-4 happy-path test: {len(cards)} wholesome cards (temp store {TEMP_STORE_DIR})\n")

    summary = []
    full = []
    for i, card in enumerate(cards):
        test_date = shift_date(start_day.isoformat(), i + 1)
        hook_type = choose_hook_type(test_date, hook_store=hook_store, rng=random.Random(test_date))
        recent_hooks = _recent_hooks(hook_store, test_date)

        print(f"--- card {i + 1}/{len(cards)}: {card.id} ({card.book})")
        print(f"    hook_type={hook_type}  (rotated for {test_date})")

        result = generate_script(card, hook_type, recent_hooks)
        words = count_farsi_words(result.script_farsi)

        print(f"    llm_status={result.status}  approved={result.approved}  words={words}")
        print(f"    flags={result.flags}")
        print(f"    target_seconds={result.target_seconds}")
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

    out = Path("storage/temp/fr4_happy_result.json")
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
