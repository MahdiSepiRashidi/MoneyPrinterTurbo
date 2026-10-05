"""FR-6 live verification: the real TTS stage against MPT's generate_audio.

Runs `flow.make_tts_stage` (the default `_default_generate_audio` seam, i.e. the
module-level `app.services.task.generate_audio`) with a ~180-word Farsi script
and asserts the measured duration lands in the 60-90s band at rate 1.0 — proving
the card's "TTS MP3 generated with duration 60-90s for a 150-220-word script".

Exits 0 on success. No MPT source files are modified.

    uv run python -X utf8 -m supervisor.fr6_check
"""

from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "test"))

# A ~180-word Farsi script that passes the FR-17 validator: one prosody mark
# (،) every 12 words, 15 chunks x 12 words = 180 words.
_WORDS_PER_CHUNK = 12
_CHUNKS = 15
_FARSI_SCRIPT = "، ".join(" ".join(["موفقیت"] * _WORDS_PER_CHUNK) for _ in range(_CHUNKS))
_WORD_COUNT = len(_FARSI_SCRIPT.replace("،", " ").split())


def main() -> int:
    os.chdir(REPO_ROOT)
    import tempfile
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from supervisor import flow
    from supervisor.config import load_supervisor_config
    from supervisor.store import DailyRun, DailyRunStore

    cfg = load_supervisor_config()
    print(f"FR-6 live check: tts_voice={cfg.tts_voice!r}")
    print(f"script word count (spaced tokens): {_WORD_COUNT}")

    # Gemini TTS free tier is ~10 req/day; a transient server-disconnect failure
    # leaves enough quota to retry the same task id later today (R-1 note).
    run_id = f"fr6-live-{datetime.now(ZoneInfo('Asia/Tehran')).strftime('%H%M%S')}"

    with tempfile.TemporaryDirectory() as tmp:
        store = DailyRunStore(Path(tmp))
        run = DailyRun(
            run_id=run_id,
            date_tehran="2026-10-04",
            checkpoint="script_approved",
            script_farsi=_FARSI_SCRIPT,
        )
        store.upsert_run(run)

        stage = flow.make_tts_stage(cfg, store=store)
        print("running the real TTS stage (MPT generate_audio + voice dispatch) ...")
        for attempt in (1, 2):
            try:
                stage.run(run)
                break
            except Exception as exc:
                print(f"attempt {attempt} failed: {exc}")
                if attempt == 2:
                    raise
                time.sleep(30)

        print(f"\nnarration_file = {run.narration_file}")
        print(f"size = {os.path.getsize(run.narration_file) if run.narration_file and os.path.exists(run.narration_file) else 0} bytes")

    if run.narration_file and os.path.exists(run.narration_file):
        from app.services import voice as mpt_voice

        measured = math.ceil(mpt_voice.get_audio_duration(run.narration_file))
        print(f"measured duration = {measured}s")
    else:
        measured = 0
        print("no audio produced")

    print("\nRESULT:", "PASS - in [60,90]s band" if (run.narration_file and 60 <= measured <= 90) else "CHECK OUTPUT ABOVE")
    return 0 if (run.narration_file and 60 <= measured <= 90) else 1


if __name__ == "__main__":
    sys.exit(main())
