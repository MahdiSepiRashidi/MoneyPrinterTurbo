"""Print the RAW gemini response + what parse_json_object extracts, for card 1."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import config as app_config
from app.services.llm import _generate_response
from supervisor.scriptgen import build_system_prompt, build_user_prompt, parse_json_object
from supervisor.store import IdeaCardStore


def main() -> int:
    card = IdeaCardStore("storage/temp/fr4_test_store").all()[0]
    prompt = f"{build_system_prompt()}\n\n{build_user_prompt(card, 'stat', [])}"
    probe = {**dict(app_config.app), "llm_provider": "gemini", "gemini_model_name": "gemini-3.8-flash"}

    for i in range(8):
        raw = _generate_response(prompt, probe)
        if raw and raw.strip() and not raw.startswith("Error: "):
            print(f"=== attempt {i+1}: raw ({len(raw)} chars) ===")
            print(raw)
            print("\n=== parse_json_object result ===")
            try:
                data = parse_json_object(raw)
                print(type(data))
                print(repr(data)[:800])
            except Exception as e:
                print(f"PARSE FAILED: {e}")
            return 0
        print(f"attempt {i+1}: transient -> {(raw or '<EMPTY>').splitlines()[0][:60]}")

    print("never got a clean response in 8 attempts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
