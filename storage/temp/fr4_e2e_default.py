"""End-to-end: generate_script with the DEFAULT llm_fn (supervisor.llm.complete:
gemini-primary -> agnes-fallback), confirming the production path now approves.

Run:  uv run python -X utf8 storage/temp/fr4_e2e_default.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import config as app_config
from supervisor.scriptgen import count_farsi_words, generate_script
from supervisor.store import IdeaCardStore


def main() -> int:
    print(f"primary={app_config.app.get('llm_provider')} "
          f"fallback={app_config.app.get('llm_fallback_provider')} "
          f"gemini_model={app_config.app.get('gemini_model_name')}")
    card = IdeaCardStore("storage/temp/fr4_test_store").all()[0]
    result = generate_script(card, "stat")  # default llm_fn = supervisor.llm.complete
    print(f"status={result.status} approved={result.approved} words={count_farsi_words(result.script_farsi)}")
    print(f"flags={result.flags}")
    print("opening:", result.opening_line)
    return 0 if result.approved else 1


if __name__ == "__main__":
    sys.exit(main())
