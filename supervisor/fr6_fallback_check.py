"""FR-6 live TTS-model-fallback verification.

Sets the primary [app] gemini_tts_model_name to a quota-exhausted model
(gemini-3.8-flash-tts) and drives the FR-6 TTS stage with the configured
fallback chain. The stage must walk the chain until one model with remaining
budget succeeds, persisting run.narration_file.

    uv run python -X utf8 -m supervisor.fr6_fallback_check
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "test"))

_FARSI_SCRIPT = "، ".join(
    " ".join(["موفقیت", "کار", "یادگیری", "رابطه", "هدف", "مهارت", "فکر", "زندگی", "قصد", "تجربه", "دانش", "نقش"])
    for _ in range(12)
)


def main() -> int:
    os.chdir(REPO_ROOT)
    import tempfile
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from supervisor import flow
    from supervisor.config import load_supervisor_config
    from supervisor.store import DailyRun, DailyRunStore

    cfg = load_supervisor_config()
    primary = flow._primary_tts_model(cfg)
    candidates = flow._tts_model_candidates(cfg)
    print(f"primary model: {primary}")
    print(f"fallback chain (ordered best->worst): {candidates}")
    assert primary == "gemini-3.8-flash-tts", f"expected primary to be the exhausted model, got {primary}"

    print(f"word count: {len(_FARSI_SCRIPT.replace(chr(0x060c), ' ').split())}")

    with tempfile.TemporaryDirectory() as tmp:
        store = DailyRunStore(Path(tmp))
        run = DailyRun(
            run_id=f"fr6-fallback-{datetime.now(ZoneInfo('Asia/Tehran')).strftime('%H%M%S')}",
            date_tehran="2026-10-05",
            checkpoint="script_approved",
            script_farsi=_FARSI_SCRIPT,
        )
        store.upsert_run(run)

        stage = flow.make_tts_stage(cfg, store=store)
        print("running FR-6 TTS stage with model fallback chain ...")
        stage.run(run)

    print(f"\nnarration_file: {run.narration_file}")
    print("RESULT:", "PASS - model fallback chain kept the reel moving" if run.narration_file else "FAIL")
    return 0 if run.narration_file else 1


if __name__ == "__main__":
    sys.exit(main())
