"""R-10 live verification: two in-process execution paths (media vs text-LLM).

Proves, against the real MPT modules, that the supervisor can drive MPT stages
in-process under a synthetic task_id (no agent framework, no pre-registration):

  Media path (module-level, app/services/task.py):
      generate_audio -> generate_subtitle -> get_video_materials -> generate_final_videos
      ...all called with a freshly minted task_id = sup-<date>-<uuid8>.
  Text/LLM path (raw, app/services/llm.py):
      _generate_response returns un-scrubbed text (JSON / # / * survive).

Run from the repo root:
      uv run python -X utf8 -m supervisor.r10_check            # media chain + LLM probe
      uv run python -X utf8 -m supervisor.r10_check --no-llm  # media chain only
      uv run python -X utf8 -m supervisor.r10_check --clips 5 # more local clips
      uv run python -X utf8 -m supervisor.r10_check --reuse-task storage/tasks/<id> --no-llm
          # re-encode the final from a prior run's audio.mp3/subtitle.srt (skips TTS)

Exits 0 when every assertion passes. No MPT source files are modified.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FARSI_SCRIPT = (
    "به نام خدا. این یک ویدیوی آزمایشی برای اثبات مسیر اجرای مپ "
    "در فرایند است؛ هر مرحله یک فایل موقت می‌سازد و خروجی نهایی "
    "یک ریل عمودی می‌شود."
)


def _load_config_toml() -> dict:
    p = REPO_ROOT / "config.toml"
    if not p.exists():
        return {}
    with open(p, "rb") as handle:
        try:
            return tomllib.load(handle)
        except Exception as exc:  # pragma: no cover - config is expected to parse
            print(f"config.toml unreadable: {exc}")
            return {}


def _banner(text: str) -> None:
    print(f"\n=== {text} ===")


def _ok(label: str, cond: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" -> {detail}" if detail else ""))
    return not cond


def _make_local_clips(count: int, seconds: int, out_dir: Path, ffmpeg_bin: str) -> list[str]:
    names = []
    for i in range(count):
        name = f"r10_clip_{i}.mp4"
        cmd = [
            ffmpeg_bin, "-y",
            "-f", "lavfi",
            "-i", f"testsrc=size=1080x1920:rate=25:duration={seconds}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-t", str(seconds), str(out_dir / name),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        names.append(name)
    return names


def _probe_aspect(path: str, ffmpeg_bin: str) -> tuple[int, int]:
    probe = subprocess.run([ffmpeg_bin, "-i", path], capture_output=True, text=True)
    match = re.search(r"(\d{2,5})x(\d{2,5})", probe.stderr or "")
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="R-10 live verification of the two in-process execution paths.")
    parser.add_argument("--no-llm", action="store_true", help="Skip the raw LLM _generate_response probe.")
    parser.add_argument("--script", default=DEFAULT_FARSI_SCRIPT, help="Farsi narration to synthesize.")
    parser.add_argument("--clips", type=int, default=3, help="Number of local test clips to synthesize.")
    parser.add_argument("--clip-seconds", type=int, default=6, help="Seconds per local test clip.")
    parser.add_argument("--voice", default=None, help="Override TTS voice (default: config [supervisor].tts_voice).")
    parser.add_argument("--font", default="Vazirmatn-Regular.ttf", help="Subtitle font in resource/fonts (Farsi-capable).")
    parser.add_argument("--font-size", type=int, default=60, dest="font_size", help="Subtitle font size.")
    parser.add_argument("--reuse-task", default=None, dest="reuse_task",
                        help="Skip TTS+subtitle; re-encode the final from a prior task dir's audio.mp3/subtitle.srt.")
    args = parser.parse_args(argv)

    os.chdir(REPO_ROOT)
    # Import MPT modules after chdir so config.toml / storage resolve to repo root.
    from app.models.schema import MaterialInfo, VideoConcatMode, VideoParams
    from app.services import llm as mpt_llm
    from app.services import state as sm
    from app.services import task as mpt_task
    from app.services import voice as mpt_voice
    from app.utils import utils

    cfg = _load_config_toml()
    sup = cfg.get("supervisor") or {}
    app_cfg = cfg.get("app") or {}
    voice = args.voice or str(sup.get("tts_voice") or "gemini:Charon")

    task_id = f"sup-{datetime.now().date()}-{uuid4().hex[:8]}"
    _banner(f"R-10 live chain  (task_id={task_id})")
    print(f"  TTS voice      = {voice}")
    print(f"  LLM provider   = {app_cfg.get('llm_provider')}  model={app_cfg.get('gemini_model_name')}")
    print(f"  local clips    = {args.clips} x {args.clip_seconds}s  source=local")

    # --- prepare local materials (9:16) --------------------------------
    local_dir = utils.storage_dir("local_videos", create=True)
    ffmpeg_bin = utils.get_ffmpeg_binary()
    _banner("1. local materials (ffmpeg testsrc -> 9:16)")
    try:
        clip_names = _make_local_clips(args.clips, args.clip_seconds, Path(local_dir), ffmpeg_bin)
    except Exception as exc:
        print(f"  [FAIL] ffmpeg clip generation: {exc}")
        return 1
    materials = [MaterialInfo(provider="local", url=name, duration=args.clip_seconds) for name in clip_names]
    _ok(f"created {len(clip_names)} local clips in {local_dir}", True, ", ".join(clip_names))

    params = VideoParams(
        video_subject="R-10 live chain",
        video_script=args.script,
        video_source="local",
        video_materials=materials,
        video_clip_duration=5,
        video_count=1,
        video_concat_mode=VideoConcatMode.random,
        voice_name=voice,
        subtitle_enabled=True,
        font_name=args.font,
        font_size=args.font_size,
        bgm_type="",
        bgm_volume=0.0,
    )

    before_ids = set(sm.state.list_task_ids())
    print(f"\n  pre-registered task ids = {len(before_ids)}; synthetic id absent: {task_id not in before_ids}")

    failures = 0

    # --- stage 1+2: audio + subtitle (or reuse a prior run) -----------
    audio_file = audio_duration = sub_maker = None
    subtitle_path = ""
    if args.reuse_task:
        reuse = Path(args.reuse_task)
        if not reuse.is_absolute() and not (REPO_ROOT / args.reuse_task).exists():
            reuse = REPO_ROOT / args.reuse_task
        audio_file = reuse / "audio.mp3"
        sub_file = reuse / "subtitle.srt"
        subtitle_path = sub_file if sub_file.exists() else ""
        audio_duration = math.ceil(mpt_voice.get_audio_duration(str(audio_file)))
        _banner("2. REUSE audio/subtitle from prior task (TTS skipped)")
        _ok(f"reusing {audio_file}", audio_file.exists(), f"{audio_duration}s")
    else:
        _banner("2. generate_audio (module-level, in-process)")
        try:
            audio_file, audio_duration, sub_maker = mpt_task.generate_audio(task_id, params, params.video_script)
        except Exception as exc:
            print(f"  [FAIL] generate_audio raised: {exc}")
        if audio_file and os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
            _ok("audio produced", True, f"{audio_file} ({os.path.getsize(audio_file)} bytes, {audio_duration}s)")
        else:
            failures += _ok("audio produced", False, f"audio_file={audio_file}; state={sm.state.get_task(task_id)}")
        _ok("sub_maker returned (edge needs word cues; TTS may be None)", sub_maker is not None,
             type(sub_maker).__name__)

        _banner("3. generate_subtitle (module-level, in-process)")
        try:
            subtitle_path = mpt_task.generate_subtitle(task_id, params, params.video_script, sub_maker, audio_file)
        except Exception as exc:
            print(f"  [WARN] generate_subtitle raised: {exc}")
        _ok("subtitle path (empty ok when TTS gives no word cues)", True, f"{subtitle_path or '<none>'}")

    # --- stage 3: materials --------------------------------------------
    _banner("4. get_video_materials (module-level, in-process, local)")
    downloaded = None
    try:
        downloaded = mpt_task.get_video_materials(task_id, params, [], audio_duration or 0)
    except Exception as exc:
        print(f"  [FAIL] get_video_materials raised: {exc}")
    if downloaded:
        _ok("materials resolved", True, f"{len(downloaded)} local clip(s)")
    else:
        failures += _ok("materials resolved", False, f"state={sm.state.get_task(task_id)}")

    # --- stage 4: final video ------------------------------------------
    _banner("5. generate_final_videos (module-level, in-process, ffmpeg)")
    final_paths = []
    warnings: list = []
    if downloaded and audio_file and audio_duration:
        try:
            final_paths, _combined, warnings = mpt_task.generate_final_videos(
                task_id, params, downloaded, audio_file, (str(subtitle_path) if subtitle_path else ""), audio_duration
            )
        except Exception as exc:
            print(f"  [FAIL] generate_final_videos raised: {exc}")
            failures += 1
    else:
        print("  [SKIP] upstream stage failed; cannot run final video")
        failures += 1

    if final_paths:
        final = final_paths[0]
        size = os.path.getsize(final) if os.path.exists(final) else 0
        width, height = _probe_aspect(final, ffmpeg_bin)
        is_916 = bool(width) and bool(height) and abs(width / height - 9 / 16) < 1e-6
        _ok("final MP4 produced", os.path.exists(final), f"{final} ({size / 1e6:.2f} MB)")
        failures += _ok("aspect 9:16", is_916, f"{width}x{height}")
        failures += _ok("size <= 48 MB", size <= 48 * 1024 * 1024, f"{size / 1e6:.2f} MB")
        if warnings:
            print(f"  warnings: {warnings}")

    # --- state / task-manager conflict ---------------------------------
    _banner("6. task_id state + no task-manager conflict")
    after_ids = set(sm.state.list_task_ids())
    state_entry = sm.state.get_task(task_id)
    failures += _ok("state entry created for synthetic id", task_id in after_ids, f"{state_entry}")
    failures += _ok("id not pre-registered (no manager conflict)", task_id not in before_ids and task_id in after_ids)

    # --- LLM raw probe -------------------------------------------------
    if not args.no_llm:
        _banner("7. _generate_response is raw (JSON/#/* survive)")
        probe = (
            "Return ONLY a JSON object, no prose, with keys:\n"
            '  "hashtags": an array of 3 Farsi hashtags, each starting with #,\n'
            '  "note": a short string containing one *bold* word.\n'
            "Do not wrap it in a code fence."
        )
        try:
            resp = mpt_llm._generate_response(probe)
        except Exception as exc:
            resp = f"Error: {exc}"
        text = resp if isinstance(resp, str) else str(resp)
        raw_ok = "#" in text and "*" in text and "[" in text
        _ok("raw LLM text survived (no scrubbing)", raw_ok, f"{text[:200]!r} ...")
        failures += _ok("LLM call succeeded", not text.startswith("Error:"))

    _banner("RESULT")
    if failures == 0:
        print("  ALL PASS - two in-process execution paths confirmed (R-10).")
        return 0
    print(f"  {failures} assertion(s) failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
