"""FR-13 retry/backoff/resume flow engine for the daily reel pipeline.

Every pipeline stage runs through one wrapper (`run_stage_with_retry`):

- 3 attempts with backoff (config ``retry_backoff_seconds``; default "30,120,600").
  The 3 backoff values gate the 3 primary attempts; for LLM stages the last value
  also gates a single FR-14 cheap-model fallback attempt after the primary exhausts.
- LLM stages: after the 3 primary attempts fail, the stage's ``fallback`` callable
  (the FR-14 fallback provider) is invoked **once**.
- On success: ``DailyRun.checkpoint`` advances to the stage's next boundary.
- On final failure: ``DailyRun.last_error`` is set and ``retry_count`` incremented.

The Telegram "day missed" alert fires **only** when a failure is detected after the
post time (20:00 weekday / 14:00 Friday Tehran) for the run's date.

Checkpoint granularity is per-stage: ``resume`` re-runs the stage that owns the
current checkpoint, never a sub-step. The downstream Buffer post *retry* loop (FR-11)
sits inside the post stage; this engine is what escalates failures and resumes.
"""

from __future__ import annotations

import time
import tomllib
from dataclasses import dataclass
from datetime import date, datetime, time as dtime
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from loguru import logger

from supervisor.config import load_supervisor_config
from supervisor.farsi_norm import normalize as normalize_farsi
from supervisor.store import DailyRun, DailyRunStore, HookRotationStore, IdeaCardStore

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

# Terminal + ordered checkpoint boundaries (data-model: daily_runs.json).
CHECKPOINT_ORDER = [
    "cards_picked",
    "script_approved",
    "video_built",
    "posting",
    "posted",
]
TERMINAL_CHECKPOINT = "posted"

# FR-5 approval boundary: no media/post stage may run before the operator advances
# the run to this checkpoint (the `approve` gate in supervisor/approval.py).
APPROVAL_CHECKPOINT = "script_approved"
APPROVAL_INDEX = CHECKPOINT_ORDER.index(APPROVAL_CHECKPOINT)

DEFAULT_BACKOFF_SECONDS = [30, 120, 600]


def now_tehran() -> datetime:
    return datetime.now(TEHRAN_TZ)


# ---------------------------------------------------------------------------
# Stage model
# ---------------------------------------------------------------------------

@dataclass
class Stage:
    """One pipeline stage driven through the FR-13 retry/backoff wrapper.

    - ``run``: executes the stage against a ``DailyRun``; must raise on failure.
    - ``checkpoint``: value written to ``DailyRun.checkpoint`` when the stage completes.
    - ``entry_checkpoint``: optional in-flight marker written on entry (e.g. the post
      stage sets ``posting``; a later resume re-runs the whole stage, not a sub-step).
    - ``is_llm`` / ``fallback``: when the stage is an LLM stage, ``fallback`` is the
      FR-14 cheap-model attempt, invoked once after the primary attempts exhaust.
    """

    name: str
    checkpoint: str
    run: Callable[[DailyRun], None]
    is_llm: bool = False
    fallback: Optional[Callable[[DailyRun], None]] = None
    entry_checkpoint: Optional[str] = None


# Module-level registry: future content/media stages (FR-4/6/7/8/9) wire themselves in
# via register_stage() as their cards land; the engine is complete today.
_REGISTERED: list[Stage] = []


def register_stage(stage: Stage) -> Stage:
    """Register a concrete stage so `build_drivable_stages` picks it up."""
    _REGISTERED.append(stage)
    return stage


def get_registered_stages() -> list[Stage]:
    return list(_REGISTERED)


def clear_registered_stages() -> None:
    _REGISTERED.clear()


# ---------------------------------------------------------------------------
# Backoff / checkpoint helpers
# ---------------------------------------------------------------------------

def parse_backoff(seconds: str) -> list[int]:
    """Parse ``retry_backoff_seconds`` ("30,120,600") into [30, 120, 600]."""
    values = []
    for part in (seconds or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.append(int(part))
        except ValueError:
            return list(DEFAULT_BACKOFF_SECONDS)
    return values or list(DEFAULT_BACKOFF_SECONDS)


def checkpoint_index(value: str) -> int:
    try:
        return CHECKPOINT_ORDER.index(value)
    except ValueError:
        return -1


def pending_stages(run: DailyRun, stages: list[Stage]) -> list[Stage]:
    """Stages whose completion checkpoint is still beyond the run's current boundary.

    A stage is pending iff its ``checkpoint`` sorts after ``run.checkpoint`` in
    ``CHECKPOINT_ORDER``. This is the per-stage granularity: resume re-runs the
    first pending stage in full, not a sub-step of it.
    """
    current = checkpoint_index(run.checkpoint)
    return [s for s in stages if checkpoint_index(s.checkpoint) > current]


def media_stage_eligible(run: DailyRun, stage: "Stage") -> bool:
    """FR-5 gate: a media/post stage (checkpoint past the approval boundary) may only
    run once the run itself is at/past ``script_approved``. Before the operator's
    ``approve`` event this is False, so the pipeline stops at the gate and no media
    stage runs. Media stages are never gated for post-approval runs.
    """
    return not (
        checkpoint_index(stage.checkpoint) > APPROVAL_INDEX
        and checkpoint_index(run.checkpoint) < APPROVAL_INDEX
    )


def _parse_hhmm(value: str) -> dtime:
    hour, minute = value.split(":")
    return dtime(int(hour), int(minute))


def post_time_for_date(date_tehran: str, cfg) -> datetime:
    """The post deadline (Tehran) for a run's date: Friday uses the Friday time."""
    day = date.fromisoformat(date_tehran)
    hhmm = cfg.post_time_friday if day.weekday() == 4 else cfg.post_time_weekday
    return datetime.combine(day, _parse_hhmm(hhmm), tzinfo=TEHRAN_TZ)


def is_past_post_time(run: DailyRun, cfg, now: Optional[datetime] = None) -> bool:
    """True when a failure at ``now`` has already passed the run's post deadline.

    The day-missed alert is gated on this: a failure *before* post time is just a
    recorded error (retry / resume is still possible); only *after* post time do we
    escalate to a Telegram day-missed alert.
    """
    return (now or now_tehran()) >= post_time_for_date(run.date_tehran, cfg)


# ---------------------------------------------------------------------------
# Retry/backoff/fallback wrapper (the FR-13 core)
# ---------------------------------------------------------------------------

def run_stage_with_retry(
    run: DailyRun,
    stage: Stage,
    backoff: list[int],
    sleep_fn: Callable[[int], None] = time.sleep,
    attempts: Optional[int] = None,
) -> tuple[bool, Optional[BaseException]]:
    """Run ``stage`` up to ``attempts`` times with backoff, then one LLM fallback.

    Returns ``(succeeded, last_error)``. Backoff values gate the attempts in order;
    for LLM stages the final value also gates the single ``stage.fallback`` call. A
    non-LLM stage never waits out its final backoff value (nothing follows it).
    """
    backoff = list(backoff or [])
    if attempts is None:
        attempts = len(backoff) or 1

    last_error: Optional[BaseException] = None
    for i in range(attempts):
        try:
            stage.run(run)
            return True, None
        except Exception as exc:  # noqa: BLE001 - any stage failure is retriable
            last_error = exc
            logger.warning(
                "flow: stage '{}' attempt {}/{} failed: {}", stage.name, i + 1, attempts, exc
            )
            is_last = i == attempts - 1
            has_followup = (not is_last) or (stage.is_llm and stage.fallback is not None)
            delay = backoff[i] if i < len(backoff) else 0
            if delay and has_followup:
                sleep_fn(delay)

    if stage.is_llm and stage.fallback is not None:
        logger.info("flow: stage '{}' primary exhausted -> FR-14 fallback attempt", stage.name)
        try:
            stage.fallback(run)
            return True, None
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.error("flow: stage '{}' fallback failed: {}", stage.name, exc)

    return False, last_error


# ---------------------------------------------------------------------------
# Orchestrator (drives the pipeline, advances checkpoints, gates alerts)
# ---------------------------------------------------------------------------

def run_pipeline(
    run: DailyRun,
    store: DailyRunStore,
    cfg,
    stages: list[Stage],
    *,
    resume: bool = True,
    sleep_fn: Callable[[int], None] = time.sleep,
    now_fn: Callable[[], datetime] = now_tehran,
    alert_fn: Optional[Callable[[DailyRun, BaseException], None]] = None,
    backoff: Optional[list[int]] = None,
    attempts: Optional[int] = None,
) -> DailyRun:
    """Drive the remaining (or all, when ``resume`` is False) stages through the wrapper.

    - Advances ``run.checkpoint`` only on a stage's success.
    - On a stage's final failure, sets ``last_error`` / increments ``retry_count`` and
      fires the day-missed alert **only** when the failure is past the post time.
    """
    stages = list(stages if stages is not None else build_drivable_stages(cfg))
    target_backoff = list(backoff) if backoff is not None else parse_backoff(cfg.retry_backoff_seconds)
    remaining = pending_stages(run, stages) if resume else list(stages)

    # FR-5 media gate: hold every media/post stage while the run is unapproved so no
    # media stage can run before the operator's `approve` event.
    held = [s for s in remaining if not media_stage_eligible(run, s)]
    if held:
        logger.info(
            "flow: run {} gated at approval (FR-5); holding {} media stage(s): {}",
            run.run_id, len(held), [s.name for s in held],
        )
        remaining = [s for s in remaining if media_stage_eligible(run, s)]

    if not remaining:
        logger.info("flow: nothing to do for run {} (checkpoint '{}')", run.run_id, run.checkpoint)
        return run

    logger.info(
        "flow: run {} resume={} checkpoint='{}' -> stages {}",
        run.run_id, resume, run.checkpoint, [s.name for s in remaining],
    )
    for stage in remaining:
        if stage.entry_checkpoint:
            run.checkpoint = stage.entry_checkpoint
            store.upsert_run(run)

        ok, last_error = run_stage_with_retry(
            run, stage, target_backoff, sleep_fn=sleep_fn, attempts=attempts
        )
        if ok:
            run.checkpoint = stage.checkpoint
            run.last_error = None
            store.upsert_run(run)
            logger.info("flow: stage '{}' done; checkpoint -> '{}'", stage.name, stage.checkpoint)
            continue

        # Final failure: keep the in-flight marker (or stay put), record the error.
        run.checkpoint = stage.entry_checkpoint or run.checkpoint
        run.last_error = str(last_error)
        run.retry_count += 1
        store.upsert_run(run)
        logger.error("flow: stage '{}' final failure: {}", stage.name, last_error)
        if is_past_post_time(run, cfg, now_fn()):
            if alert_fn is not None:
                alert_fn(run, last_error)
            else:
                _default_day_missed_alert(run, last_error, cfg)
        break

    return run


def resume_run(
    run_id: str,
    cfg=None,
    store: Optional[DailyRunStore] = None,
    stages: Optional[list[Stage]] = None,
    **kwargs,
) -> DailyRun:
    """Load a ``DailyRun`` and continue it from its checkpoint (FR-13 resume)."""
    cfg = cfg or load_supervisor_config()
    store = store or DailyRunStore()
    run = store.get_run(run_id)
    if run is None:
        raise KeyError(f"DailyRun not found: {run_id}")
    if stages is None:
        stages = build_drivable_stages(cfg)
    return run_pipeline(run, store, cfg, stages, resume=True, **kwargs)


# ---------------------------------------------------------------------------
# Day-missed alert (the gate is FR-13's; the delivery copy is FR-15's)
# ---------------------------------------------------------------------------

def _default_day_missed_alert(run: DailyRun, error: BaseException, cfg) -> None:
    """Route the day-missed alert through the Telegram bot when it exists; else log.

    ``supervisor/telegram_bot.py`` (FR-15) is the operator surface; until it lands,
    the alert is logged so it is not silently dropped.
    """
    try:
        from supervisor import telegram_bot as tb  # noqa: PLC0415 - lazy; FR-15 seam

        if hasattr(tb, "send_day_missed"):
            tb.send_day_missed(run, error, cfg)
            return
        if hasattr(tb, "send_message"):
            tb.send_message(
                f"⚠️ روز از دست رفت (run {run.run_id}): {error}\n"
                f"دور با «resume {run.run_id}» یا بازسازی دوباره."
            )
            return
    except Exception:  # noqa: BLE001 - alerting must never take the pipeline down
        logger.debug("flow: telegram day-missed alert unavailable; logging instead")
    logger.warning("flow: day missed for run {}: {}", run.run_id, error)


# ---------------------------------------------------------------------------
# FR-6: Farsi TTS narration stage (pluggable provider + 60-90s duration gate)
# ---------------------------------------------------------------------------

TTS_MIN_SECONDS = 60
TTS_MAX_SECONDS = 90
TTS_RATE_MIN = 0.9
TTS_RATE_MAX = 1.1
TTS_RATE_STEP = 0.05
MAX_TTS_RERUNS = 2
# FR-4 regeneration word-count targets, mirroring scriptgen's band-closing
# targets (scriptgen._regen_instruction): TTS too short -> longer script,
# TTS too long -> shorter script (both inside the 150-220 word band).
TTS_TARGET_WORDS_LONGER = 210
TTS_TARGET_WORDS_SHORTER = 170


class TTSApprovalHeld(RuntimeError):
    """The TTS stage found the run held behind the FR-5 approval gate.

    After a duration-gate escalation regenerates the script and re-enters the
    gate (``cards_picked``), the FR-13 backoff retries of the stage fast-fail
    with this error until the operator re-approves the new script.
    """


def _next_voice_rate(current: float, duration: int) -> float:
    """Step ``current`` toward the rate that would bring the measured duration
    into [TTS_MIN_SECONDS, TTS_MAX_SECONDS]: too short -> slow down (longer
    audio), too long -> speed up (shorter audio). Clamped to [0.9, 1.1]; when
    already at the relevant bound the current rate is returned unchanged."""
    if duration < TTS_MIN_SECONDS:
        return max(TTS_RATE_MIN, current - TTS_RATE_STEP)
    if duration > TTS_MAX_SECONDS:
        return min(TTS_RATE_MAX, current + TTS_RATE_STEP)
    return current


def build_tts_params(cfg, run: DailyRun, tts_text: str, voice_rate: float = 1.0):
    """MPT ``VideoParams`` for the Farsi reel: portrait 9:16 (1080x1920) with
    ``voice_name = cfg.tts_voice``.

    The provider switch is config-only (R-1): MPT's voice dispatch routes the
    voice-name prefix to a provider (``gemini:Charon``, ``fa-IR-DilaraNeural``, ...).
    """
    from app.models.schema import VideoAspect, VideoParams  # noqa: PLC0415 - keep MPT imports lazy

    return VideoParams(
        video_subject=f"IG Reel {run.date_tehran}",
        video_aspect=VideoAspect.portrait.value,
        video_script=tts_text,
        video_language="fa",
        voice_name=cfg.tts_voice,
        voice_rate=voice_rate,
        subtitle_enabled=True,
        bgm_type="",
        bgm_volume=0.0,
    )


def _primary_tts_model(cfg) -> str:
    """The primary Gemini TTS model name (``[app] gemini_tts_model_name``).

    Falls back to ``GEMINI_TTS_DEFAULT_MODEL`` when unset, matching MPT's
    ``voice.gemini_tts`` behaviour.
    """
    try:
        from app.config import config as mpt_config  # noqa: PLC0415
        model = str(mpt_config.app.get("gemini_tts_model_name", "") or "").strip()
        if model:
            return model
    except Exception:  # noqa: BLE001
        pass
    try:
        from app.services.voice import GEMINI_TTS_DEFAULT_MODEL  # noqa: PLC0415
        return GEMINI_TTS_DEFAULT_MODEL
    except Exception:  # noqa: BLE001
        return "gemini-2.5-flash-preview-tts"


def _tts_model_candidates(cfg) -> list[str]:
    """Ordered TTS model candidates: the primary model first, then the
    ``cfg.tts_model_fallbacks`` chain (deduped, preserving order). The FR-6 stage
    walks this list when the primary call fails (quota 429 / 503 / transient
    disconnect) so a different model with remaining budget can keep the reel
    moving without waiting for a quota reset."""
    candidates = [_primary_tts_model(cfg)]
    for model in getattr(cfg, "tts_model_fallbacks", None) or []:
        model = str(model or "").strip()
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def _default_generate_audio(task_id: str, params, tts_text: str, model: Optional[str] = None):
    """MPT's module-level TTS seam (R-10: in-process calls, synthetic task id).

    When ``model`` is given, ``config.app["gemini_tts_model_name"]`` is temporarily
    pointed at it for the duration of the call so the gemini TTS dispatch picks
    that model; the original value is restored afterwards.
    """
    from app.services import task as mpt_task  # noqa: PLC0415
    if model is None:
        return mpt_task.generate_audio(task_id, params, tts_text)
    from app.config import config as mpt_config  # noqa: PLC0415
    original = mpt_config.app.get("gemini_tts_model_name", "")
    mpt_config.app["gemini_tts_model_name"] = model
    try:
        return mpt_task.generate_audio(task_id, params, tts_text)
    finally:
        mpt_config.app["gemini_tts_model_name"] = original


def _recent_hook_rows(hook_store: Optional[HookRotationStore], today: str) -> list[str]:
    """The last-7 ``hook_type | opening_line`` rows before ``today`` for the
    FR-4 prompt (mirrors ``approval._recent_hooks``)."""
    if hook_store is None:
        return []
    rows = [r for r in hook_store.load() if str(r.get("date_tehran", "")) < today]
    return [f"{r.get('hook_type', '?')} | {r.get('opening_line', '')}" for r in rows[-7:]]


def _regen_script_and_reenter_gate(
    run: DailyRun,
    store: DailyRunStore,
    idea_store: Optional[IdeaCardStore],
    hook_store: Optional[HookRotationStore],
    llm_fn,
    send_fn,
    max_rewrites: int,
    last_duration: int,
) -> None:
    """FR-6 escalation: regenerate the script at a closer word-count target
    (FR-4), re-enter the FR-5 approval gate, and fail the stage so FR-13
    records the outcome (day-missed alert only once post time has passed).

    The new script must be re-approved by the operator: ``checkpoint`` returns
    to ``cards_picked`` and the stage then raises ``TTSApprovalHeld``. When the
    day's rewrite budget (FR-5) is exhausted, or the picked card is missing,
    there is nothing to regenerate: a plain error is raised instead so FR-13
    escalates straight to the day-missed path.
    """
    from supervisor import scriptgen
    from supervisor.daily import choose_hook_type  # noqa: PLC0415

    card = None
    if run.picked_card_id and idea_store is not None:
        card = idea_store.get_card(run.picked_card_id)
    if card is None:
        raise RuntimeError(
            f"run {run.run_id}: TTS duration {last_duration}s outside "
            f"[{TTS_MIN_SECONDS}, {TTS_MAX_SECONDS}]s after {MAX_TTS_RERUNS} voice-rate "
            "re-runs; picked card missing - cannot regenerate the script "
            "(FR-13 day-missed path)"
        )
    if run.rewrite_count >= max_rewrites:
        raise RuntimeError(
            f"run {run.run_id}: TTS duration {last_duration}s outside "
            f"[{TTS_MIN_SECONDS}, {TTS_MAX_SECONDS}]s after {MAX_TTS_RERUNS} voice-rate "
            f"re-runs; rewrite budget exhausted ({run.rewrite_count}/{max_rewrites}) "
            "(FR-13 day-missed path)"
        )

    target = TTS_TARGET_WORDS_SHORTER if last_duration > TTS_MAX_SECONDS else TTS_TARGET_WORDS_LONGER
    hook_type = run.hook_type or choose_hook_type(run.date_tehran, hook_store=hook_store)
    result = scriptgen.generate_script(
        card,
        hook_type,
        _recent_hook_rows(hook_store, run.date_tehran),
        llm_fn=llm_fn,
        target_words=target,
    )
    scriptgen.apply_to_run(
        run, result, card, store=store, send_fn=send_fn, hook_store=hook_store
    )

    run.rewrite_count += 1
    run.checkpoint = "cards_picked"
    run.last_error = None
    store.upsert_run(run)
    logger.info(
        "FR-6: run {} TTS {}s out of range; script regenerated (~{} words) and "
        "the approval gate was re-entered",
        run.run_id, last_duration, target,
    )
    if send_fn is not None:
        send_fn(
            "امروز مدت روایت از محدوده خارج بود؛ اسکریپت دوباره‌نویسی شد. "
            "لطفاً approve یا reject بفرست."
        )
    raise TTSApprovalHeld(
        f"run {run.run_id}: TTS duration {last_duration}s outside "
        f"[{TTS_MIN_SECONDS}, {TTS_MAX_SECONDS}]s after {MAX_TTS_RERUNS} voice-rate "
        f"re-runs; script regenerated (~{target} words) and the FR-5 approval "
        "gate was re-entered"
    )


def make_tts_stage(
    cfg,
    *,
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
    hook_store: Optional[HookRotationStore] = None,
    llm_fn=None,
    send_fn: Optional[Callable[[str], dict]] = None,
    generate_audio_fn=None,
    task_id_fn: Optional[Callable[[DailyRun], str]] = None,
) -> Stage:
    """FR-6: the Farsi TTS narration stage with a pluggable provider.

    - Builds portrait 9:16 ``VideoParams`` with ``voice_name = cfg.tts_voice``
      (provider switch is config-only, R-1) and synthesizes through MPT's
      module-level ``generate_audio`` under the R-10 synthetic task id
      ``sup-<run_id>``.
    - Consumes the TTS-ready normalized script: ``farsi_norm.normalize`` (FR-17)
      runs on ``run.script_farsi`` before TTS.
    - Gates on the returned measured ``audio_duration`` in [60, 90] s.
    - Out of range: adjusts ``voice_rate`` within 0.9-1.1 and re-runs TTS up
      to 2 times. Still out of range -> regenerates the script at a closer
      word-count target (FR-4) and re-enters the FR-5 approval gate; out of
      range again -> the FR-13 day-missed alert path.
    - On a hard TTS failure (provider returns None: 429 quota / 503 / transient
      disconnect), the stage walks the ordered model fallback chain
      (``_tts_model_candidates``: primary first, then ``cfg.tts_model_fallbacks``)
      so a model with remaining daily budget can keep the reel moving.
    """
    gen_audio = generate_audio_fn or _default_generate_audio

    def run_stage(run: DailyRun) -> None:
        from supervisor.approval import MAX_REWRITES  # noqa: PLC0415 - approval imports flow

        if checkpoint_index(run.checkpoint) < APPROVAL_INDEX:
            raise TTSApprovalHeld(
                f"run {run.run_id} held at the FR-5 approval gate "
                f"(checkpoint '{run.checkpoint}')"
            )
        script = (run.script_farsi or "").strip()
        if not script:
            raise RuntimeError(
                f"run {run.run_id} has no TTS-ready script (script_farsi is empty)"
            )

        tts_text = normalize_farsi(script)
        task_id = task_id_fn(run) if task_id_fn is not None else f"sup-{run.run_id}"
        active_store = store or DailyRunStore()

        voice_rate = 1.0
        reruns = 0
        audio_file: Optional[str] = None
        audio_duration: Optional[int] = None
        models_tried: list[str] = []
        while True:
            params_for_rate = build_tts_params(cfg, run, tts_text, voice_rate)

            def synthesize(model: Optional[str]) -> tuple[Optional[str], Optional[int], object]:
                """One TTS call under ``model``. When a ``generate_audio_fn`` seam is
                injected (tests), it keeps its 3-arg (task_id, params, text) contract
                and runs under the primary model; the model fallback chain only applies
                to the default MPT seam."""
                if generate_audio_fn is not None:
                    return gen_audio(task_id, params_for_rate, tts_text)
                return _default_generate_audio(task_id, params_for_rate, tts_text, model)

            candidates = _tts_model_candidates(cfg)
            audio_file, audio_duration, _sub_maker = None, None, None
            failed = 0
            for model in candidates:
                audio_file, audio_duration, _sub_maker = synthesize(model)
                models_tried.append(model or _primary_tts_model(cfg))
                if audio_file is not None and audio_duration is not None:
                    break
                failed += 1
            if failed:
                logger.warning(
                    "FR-6: run {} TTS hard-failed on {} model(s) of {} "
                    "(429 quota / 503 / disconnect); will retry via FR-13 backoff",
                    run.run_id, failed, len(candidates),
                )
            if audio_file is None or audio_duration is None:
                raise RuntimeError(
                    f"run {run.run_id}: TTS failed on all models "
                    f"{models_tried} (task {task_id}, voice '{cfg.tts_voice}')"
                )
            if TTS_MIN_SECONDS <= audio_duration <= TTS_MAX_SECONDS:
                run.narration_file = audio_file
                run.last_error = None
                active_store.upsert_run(run)
                logger.info(
                    "FR-6: run {} TTS ok (rate {}): {}s -> {}",
                    run.run_id, voice_rate, audio_duration, audio_file,
                )
                return
            next_rate = _next_voice_rate(voice_rate, audio_duration)
            if reruns >= MAX_TTS_RERUNS or next_rate == voice_rate:
                break
            voice_rate = next_rate
            reruns += 1
            logger.info(
                "FR-6: run {} TTS {}s outside [{}-{}]s; re-run {} at rate {}",
                run.run_id, audio_duration,
                TTS_MIN_SECONDS, TTS_MAX_SECONDS, reruns, voice_rate,
            )

        _regen_script_and_reenter_gate(
            run,
            active_store,
            idea_store,
            hook_store,
            llm_fn,
            send_fn,
            MAX_REWRITES,
            last_duration=audio_duration,
        )

    return Stage(name="tts", checkpoint="video_built", run=run_stage)


# ---------------------------------------------------------------------------
# Concrete post stage (thin Buffer seam; FR-11 owns the sent-confirmation loop)
# ---------------------------------------------------------------------------

def _load_proxies() -> Optional[dict]:
    """Read ``[proxy]`` from config.toml for Buffer/LLM egress (R-7), like buffer_poc."""
    try:
        with open("config.toml", "rb") as handle:
            proxy = (tomllib.load(handle).get("proxy") or {})
    except Exception:  # noqa: BLE001 - no proxy configured is fine
        return None
    out: dict[str, str] = {}
    if proxy.get("http"):
        out["http"] = str(proxy["http"])
    if proxy.get("https"):
        out["https"] = str(proxy["https"])
    return out or None


def _resolve_media_url(run: DailyRun, cfg) -> str:
    """Return a public, fetchable MP4 URL for the reel (R-9 seam -> media_host)."""
    if not run.video_file:
        raise RuntimeError("no built video for run (video_built checkpoint not reached)")
    try:
        from supervisor import media_host  # noqa: PLC0415 - lazy; R-9 seam
        url = media_host.host_video(run.video_file, cfg)
        if url:
            return url
    except Exception:  # noqa: BLE001 - media_host not built yet
        logger.debug("flow: media_host unavailable; using recorded public URL if any")
    if run.video_file.startswith(("http://", "https://")):
        return run.video_file
    raise RuntimeError("media host (R-9) unavailable and video_file is not a public URL")


def make_post_stage(cfg) -> Stage:
    """The retryable post attempt: host the media, create the Buffer post (shareNow)."""

    def run(run: DailyRun) -> None:
        from supervisor import buffer  # noqa: PLC0415 - keep Buffer optional at import

        # Validate inputs before any network call so a missing video fails fast
        # with a clear error instead of a Buffer 401/auth round-trip.
        media_url = _resolve_media_url(run, cfg)

        client = buffer.BufferClient(
            api_key=cfg.buffer_api_key,
            base_url=cfg.buffer_base_url,
            organization_id=cfg.buffer_organization_id or None,
            proxies=_load_proxies(),
        )
        channel = client.find_channel(
            service="instagram",
            preferred_id=cfg.buffer_channel_id or None,
        )
        if channel is None:
            raise RuntimeError("no Buffer instagram channel connected")

        caption = (run.caption or "").strip()
        hashtags = " ".join(h if h.startswith("#") else f"#{h}" for h in (run.hashtags or []))
        text = f"{caption}\n{hashtags}".strip()

        result = client.create_post(
            str(channel["id"]),
            text,
            video_url=media_url,
            reel_type=cfg.buffer_reel_type,
            save_to_draft=False,
            publish_now=True,
            is_ai_generated=True,
        )
        post = result.get("post") if isinstance(result, dict) else None
        if not post:
            raise buffer.BufferError(f"Buffer post rejected: {result}")

        # Mark the post scheduled; the find_post->sent confirmation loop is FR-11's.
        run.post_status = "scheduled"
        run.scheduled_time_tehran = now_tehran().isoformat()
        if run.picked_card_id:
            from supervisor.store import IdeaCardStore  # noqa: PLC0415

            IdeaCardStore().mark_used(run.picked_card_id)

    return Stage(name="post", checkpoint=TERMINAL_CHECKPOINT, run=run, entry_checkpoint="posting")


def build_drivable_stages(cfg) -> list[Stage]:
    """Assemble the concrete stages available today, ordered by checkpoint boundary.

    The TTS (FR-6) and post stages ship now; the remaining media sub-steps
    (FR-7 BGM, FR-8 clips, FR-9 encode) register themselves via `register_stage`
    as their cards land, inside the `video_built` boundary the TTS stage owns.
    The result is sorted by completion-checkpoint order so `pending_stages` is
    correct.
    """
    stages: list[Stage] = [make_tts_stage(cfg), make_post_stage(cfg), *get_registered_stages()]
    stages.sort(key=lambda s: checkpoint_index(s.checkpoint))
    return stages


__all__ = [
    "CHECKPOINT_ORDER",
    "TERMINAL_CHECKPOINT",
    "APPROVAL_CHECKPOINT",
    "DEFAULT_BACKOFF_SECONDS",
    "TTS_MIN_SECONDS",
    "TTS_MAX_SECONDS",
    "TTS_RATE_MIN",
    "TTS_RATE_MAX",
    "MAX_TTS_RERUNS",
    "TTS_TARGET_WORDS_LONGER",
    "TTS_TARGET_WORDS_SHORTER",
    "TTSApprovalHeld",
    "Stage",
    "register_stage",
    "get_registered_stages",
    "clear_registered_stages",
    "parse_backoff",
    "checkpoint_index",
    "pending_stages",
    "media_stage_eligible",
    "post_time_for_date",
    "is_past_post_time",
    "run_stage_with_retry",
    "run_pipeline",
    "resume_run",
    "build_tts_params",
    "make_tts_stage",
    "make_post_stage",
    "build_drivable_stages",
    "now_tehran",
    "TEHRAN_TZ",
    "_primary_tts_model",
    "_tts_model_candidates",
]
