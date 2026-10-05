"""FR-6 full-flow live run: pick card → LLM script → FR-5 approve → FR-6 TTS → MPT subtitle+video.

Drives the real pipeline end-to-end against the operator's own Gemini key:

  1. pick an unused idea card (random) and create a DailyRun
  2. generate the Farsi script via the real supervisor LLM (supervisor/llm.py → MPT _generate_response)
  3. apply_to_run + approve (FR-5) to cross the approval gate
  4. run the FR-6 TTS stage (make_tts_stage, default real seam → MPT generate_audio + voice.tts)
  5. build the subtitle-burned 9:16 video via MPT (generate_subtitle, get_video_materials, generate_final_videos)

Exits 0 on success. No MPT source files are modified.

    uv run python -X utf8 -m supervisor.fr6_full
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "test"))


def main() -> int:
    os.chdir(REPO_ROOT)

    from app.models.schema import MaterialInfo, VideoParams
    from app.services import task as mpt_task
    from app.services import voice as mpt_voice
    from app.utils import utils

    from supervisor import flow, scriptgen, approval
    from supervisor.config import load_supervisor_config
    from supervisor.daily import choose_hook_type
    from supervisor.store import DailyRun, DailyRunStore, HookRotationStore, IdeaCard, IdeaCardStore

    cfg = load_supervisor_config()
    print(f"FR-6 full-flow live run: tts_voice={cfg.tts_voice!r}")

    # --- step 1: pick an unused card -------------------------------------------------
    idea_store = IdeaCardStore()
    unused = idea_store.unused(limit=100)
    if not unused:
        print("FAIL: no unused idea cards")
        return 1
    card = unused[0]
    print(f"picked card: {card.id} | {card.book} | {card.claim[:60]}...")

    today = datetime.now(ZoneInfo("Asia/Tehran")).date().isoformat()
    task_id = f"sup-full-{uuid4().hex[:8]}"
    print(f"task_id: {task_id}")

    store = DailyRunStore()
    run = DailyRun(
        run_id=f"full-{task_id[-8:]}",
        date_tehran=today,
        candidate_card_ids=[card.id],
        picked_card_id=card.id,
        picked_by="operator",
        checkpoint="cards_picked",
    )
    store.upsert_run(run)
    idea_store.mark_picked([card.id], run.run_id, today)

    # --- step 2: generate script via real LLM ---------------------------------------
    hook_store = HookRotationStore()
    hook_type = choose_hook_type(today, hook_store=hook_store)
    print(f"hook_type: {hook_type}")

    from supervisor.llm import complete as real_llm
    result = scriptgen.generate_script(card, hook_type, recent_hooks=[], llm_fn=real_llm)
    print(f"script status: {result.status} | words={len(result.script_farsi.split())} | flags={result.flags}")
    if result.status != "ok":
        print("note: LLM returned needs_review; continuing with generated text (live demo)")

    print("script (first 200 chars):", result.script_farsi[:200])
    print("caption:", result.caption[:120])
    print("hashtags:", result.hashtags)

    # --- step 3: apply + approve (FR-5) ----------------------------------------------
    scriptgen.apply_to_run(run, result, card, store=store, send_fn=lambda t: None, hook_store=hook_store)
    approval.approve(run, store=store, send_fn=lambda t: None)
    print(f"checkpoint after approve: {run.checkpoint}")
    assert run.checkpoint == "script_approved", f"expected script_approved, got {run.checkpoint}"

    # --- step 4: FR-6 TTS stage (real generate_audio seam) ---------------------------
    print("running FR-6 TTS stage (real MPT generate_audio + voice dispatch) ...")
    tts_stage = flow.make_tts_stage(cfg, store=store, idea_store=idea_store, hook_store=hook_store)
    for round_ in range(1, 6):
        print(f"TTS round {round_}:")
        try:
            tts_stage.run(run)
            print(f"  TTS stage succeeded: narration at {run.narration_file}")
            break
        except flow.TTSApprovalHeld as exc:
            # the duration gate regenerated the script and re-entered FR-5; the
            # operator (this harness) re-approves and continues.
            print(f"  held: {exc}")
            run = store.get_run(run.run_id)
            print(f"  regenerated script ({len((run.script_farsi or '').split())} words); re-approving ...")
            approval.approve(run, store=store, send_fn=lambda t: None)
            run = store.get_run(run.run_id)
            if run.checkpoint != "script_approved":
                print("FAIL: run not re-approved")
                return 1
            continue
        except Exception as exc:
            print(f"  TTS failed: {exc}")
            run = store.get_run(run.run_id)
            if run.narration_file:
                break
            if round_ == 5:
                raise
            time.sleep(30)

    print(f"narration_file: {run.narration_file}")
    if not run.narration_file:
        print("FAIL: no narration file produced")
        return 1
    audio_duration = mpt_voice.get_audio_duration(run.narration_file)
    print(f"narration duration: {audio_duration:.1f}s")

    # --- step 5: MPT subtitle + video ------------------------------------------------
    # Reuse the FR-6 TTS output directly so no extra Gemini TTS request is made:
    # generate_audio(task_id, params, script) with a pre-existing audio.mp3 in the
    # task dir returns (audio_file, duration, sub_maker=None); MPT then aligns
    # subtitles from the audio file (edge/whisper provider path).
    import math as _math
    task_id_audio = run.narration_file.split("tasks")[-1].strip("\\/").split("\\")[0].split("/")[0]
    from app.models.schema import VideoAspect, VideoConcatMode, VideoFitMode
    print(f"reusing TTS task dir for video build: {task_id_audio}")
    video_params = VideoParams(
        video_subject=f"IG Reel {today}",
        video_aspect=VideoAspect.portrait.value,
        video_script=run.script_farsi,
        video_language="fa",
        voice_name=cfg.tts_voice,
        voice_rate=1.0,
        subtitle_enabled=True,
        font_name="Vazirmatn-Regular.ttf",
        font_size=60,
        bgm_type="",
        bgm_volume=0.0,
        video_source="local",
        video_count=1,
    )
    # MPT's video.py calls `.value` on the concat/fit modes, so the in-process
    # seam must hold the enums, not their string values (r10_check.py does the same).
    video_params.video_concat_mode = VideoConcatMode.random
    video_params.video_fit_mode = VideoFitMode.cover

    # local ffmpeg testsrc clips
    local_dir = utils.storage_dir("local_videos", create=True)
    ffmpeg_bin = utils.get_ffmpeg_binary()
    import subprocess
    clip_names = []
    for i in range(3):
        name = f"fr6full_clip_{i}.mp4"
        out_path = Path(local_dir) / name
        subprocess.run(
            [ffmpeg_bin, "-y", "-f", "lavfi", "-i", f"testsrc=size=1080x1920:rate=25:duration=5",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "5", str(out_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        clip_names.append(name)
    video_params.video_materials = [MaterialInfo(provider="local", url=n, duration=5) for n in clip_names]

    # Reuse the FR-6 TTS audio directly (no second Gemini TTS call): Gemini's TTS
    # path already returns a SubMaker populated with legacy subs/offset fields
    # (populate_legacy_submaker_with_full_text), so build a matching SubMaker from
    # the measured duration and MPT's edge subtitle aggregation works unchanged.
    audio_file = run.narration_file
    audio_duration_int = _math.ceil(mpt_voice.get_audio_duration(audio_file))
    video_params.custom_audio_file = audio_file
    print(f"audio for video (reused TTS output): {audio_file} ({audio_duration_int}s)")
    if not os.path.exists(audio_file):
        print("FAIL: TTS narration file missing")
        return 1

    from app.services.voice import SubMaker, populate_legacy_submaker_with_full_text
    sub_maker = populate_legacy_submaker_with_full_text(SubMaker(), run.script_farsi, float(audio_duration_int))

    subtitle_path = mpt_task.generate_subtitle(task_id_audio, video_params, run.script_farsi, sub_maker, audio_file)
    print(f"subtitle: {subtitle_path or '<none>'}")

    print("getting video materials ...")
    materials = mpt_task.get_video_materials(task_id_audio, video_params, [], audio_duration_int or 0)
    if not materials:
        print("FAIL: no materials")
        return 1
    print(f"materials: {len(materials)} clip(s)")

    print("encoding final video (9:16, Vazirmatn subtitles) ...")
    final_paths, combined_paths, warnings = mpt_task.generate_final_videos(
        task_id_audio, video_params, materials, audio_file, (str(subtitle_path) if subtitle_path else ""), audio_duration_int
    )
    if not final_paths:
        print(f"FAIL: no final video (warnings: {warnings})")
        return 1

    final = final_paths[0]
    size = os.path.getsize(final) if os.path.exists(final) else 0
    print(f"\n=== RESULT ===")
    print(f"final video: {final}")
    print(f"size: {size/1e6:.2f} MB")
    print(f"narration: {run.narration_file} ({float(audio_duration):.1f}s)")
    print(f"video: {final} ({size/1e6:.2f} MB)")
    print(f"status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
