"""Diagnostic: call the raw supervisor LLM with a gemini config and print the
raw response for one card, so we can see exactly what gemini returns.

Run:  uv run python -X utf8 storage/temp/fr4_gemini_diag.py
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import config as app_config
from app.services.llm import _generate_response
from supervisor.scriptgen import build_system_prompt, build_user_prompt
from supervisor.store import IdeaCardStore


def main() -> int:
    card = IdeaCardStore("storage/temp/fr4_test_store").all()[0]
    system = build_system_prompt()
    user = build_user_prompt(card, "stat", [])

    cfg = dict(app_config.app)

    for provider in ("gemini", "agnes"):
        probe = {**cfg, "llm_provider": provider}
        print(f"===== provider={provider} model={probe.get('llm_model')} =====")
        raw = _generate_response(f"{system}\n\n{user}", probe)
        print(f"--- raw response ({len(raw or '')} chars) ---")
        print((raw or "<EMPTY>")[:2000])
        print(f"--- starts with 'Error: ' ? {bool(raw and raw.startswith('Error: '))} ---\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
