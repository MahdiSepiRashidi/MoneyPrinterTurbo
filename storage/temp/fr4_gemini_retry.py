"""Retry gemini-3.8-flash until we catch a clean JSON response (or give up).

The free-tier key intermittently returns 503 'high demand'. This just hammers
it with sleeps until a real response comes back, so we can judge the Farsi
quality of a genuine gemini output.

Run:  uv run python -X utf8 storage/temp/fr4_gemini_retry.py
"""

from __future__ import annotations

import time
from pathlib import Path
from sys import argv

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import config as app_config
from app.services.llm import _generate_response
from supervisor.scriptgen import build_system_prompt, build_user_prompt
from supervisor.store import IdeaCardStore

MAX_ATTEMPTS = int(argv[1]) if len(argv) > 1 else 10
SLEEP = 8


def main() -> int:
    card = IdeaCardStore("storage/temp/fr4_test_store").all()[0]
    prompt = f"{build_system_prompt()}\n\n{build_user_prompt(card, 'stat', [])}"
    probe = {**dict(app_config.app), "llm_provider": "gemini", "gemini_model_name": "gemini-3.8-flash"}

    for i in range(1, MAX_ATTEMPTS + 1):
        raw = _generate_response(prompt, probe)
        failed = (not raw or not raw.strip()) or raw.startswith("Error: ")
        if failed:
            first = (raw or "<EMPTY>").splitlines()[0][:80]
            print(f"attempt {i}/{MAX_ATTEMPTS}: FAILED -> {first}")
            time.sleep(SLEEP)
            continue

        has_json = "{" in raw
        print(f"attempt {i}/{MAX_ATTEMPTS}: OK (len={len(raw)}, has_json={has_json})")
        print(raw[:1500])
        break

    return 0


if __name__ == "__main__":
    sys.exit(main())
