"""Probe candidate Gemini model names: which one reliably returns the JSON
contract for the FR-4 prompt, and what its raw output looks like.

Run:  uv run python -X utf8 storage/temp/fr4_gemini_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import config as app_config
from app.services.llm import _generate_response
from supervisor.scriptgen import build_system_prompt, build_user_prompt
from supervisor.store import IdeaCardStore

CANDIDATES = [
    "gemini-3.5-flash",
    "gemini-3.8-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.8-flash",
]


def main() -> int:
    card = IdeaCardStore("storage/temp/fr4_test_store").all()[0]
    prompt = f"{build_system_prompt()}\n\n{build_user_prompt(card, 'stat', [])}"
    cfg = dict(app_config.app)

    for model in CANDIDATES:
        probe = {**cfg, "llm_provider": "gemini", "gemini_model_name": model}
        print(f"########## model={model} ##########")
        raw = _generate_response(prompt, probe)
        ok_json = "{" in (raw or "") and not (raw or "").startswith("Error: ")
        print(f"len={len(raw or '')} starts_error={(raw or '').startswith('Error: ')} has_json={ok_json}")
        print((raw or "<EMPTY>")[:400])
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
