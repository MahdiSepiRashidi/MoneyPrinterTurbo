"""FR-4 with Gemini-only (3.8-flash), retrying transient 503s, so we can judge
Gemini's Farsi quality in isolation (the agnes fallback does not mask it).

Run:  uv run python -X utf8 storage/temp/fr4_gemini_quality.py
"""

from __future__ import annotations

import json
import random
import sys
import time
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import config as app_config
from app.services.llm import _generate_response
from supervisor.daily import _recent_hooks, choose_hook_type
from supervisor.scriptgen import count_farsi_words, generate_script
from supervisor.store import HookRotationStore, IdeaCardStore

MODEL = "gemini-3.5-flash-lite"
MAX_ATTEMPTS = 4
SLEEP = 4

_PROBE = {**dict(app_config.app), "llm_provider": "gemini", "gemini_model_name": MODEL}


def gemini_retry(system: str, user: str) -> str:
    """Call gemini until we get a non-error response (handles transient 503s)."""
    prompt = f"{system}\n\n{user}"
    for i in range(MAX_ATTEMPTS):
        raw = _generate_response(prompt, _PROBE)
        if raw and raw.strip() and not raw.startswith("Error: "):
            return raw
        time.sleep(SLEEP)
    return raw or ""


def shift_date(iso_date: str, days: int) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=days)).isoformat()


def main() -> int:
    cards = IdeaCardStore("storage/temp/fr4_test_store").all()[:5]
    hook_store = HookRotationStore()
    start_day = date.today() - timedelta(days=len(cards))
    print(f"FR-4 GEMINI-ONLY quality check: {len(cards)} cards, model={MODEL}\n")

    summary = []
    full = []
    for i, card in enumerate(cards):
        test_date = shift_date(start_day.isoformat(), i + 1)
        hook_type = choose_hook_type(test_date, hook_store=hook_store, rng=random.Random(test_date))
        recent_hooks = _recent_hooks(hook_store, test_date)

        result = generate_script(card, hook_type, recent_hooks, llm_fn=gemini_retry)
        words = count_farsi_words(result.script_farsi)

        print(f"--- card {i + 1}/{len(cards)}: {card.id} ({card.book})  hook={hook_type}")
        print(f"    status={result.status} approved={result.approved} words={words} flags={result.flags}")
        print("    script_farsi:")
        for line in result.script_farsi.splitlines():
            print(f"      {line}")
        print(f"    caption={result.caption}")
        print(f"    hashtags={result.hashtags}")
        print()

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
        full.append({"card": card.to_dict(), "result": asdict(result), "approved": result.approved, "word_count": words})

    out = Path("storage/temp/fr4_gemini_quality.json")
    out.write_text(
        json.dumps(
            {"model": MODEL, "cards": [c.id for c in cards], "summary": summary, "results": full},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print(f"approved: {sum(1 for s in summary if s['approved'])} / {len(summary)} (model={MODEL})")
    for s in summary:
        print(f"  {s['card_id']}: {s['status']} words={s['words']} hook={s['hook_type']} flags={s['flags']}")
    print(f"detail saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
