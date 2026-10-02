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
from supervisor.store import DailyRun, DailyRunStore

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

    The post stage ships now (Buffer client is concrete); content/media stages
    register themselves via `register_stage` as their cards land. The result is
    sorted by completion-checkpoint order so `pending_stages` is correct.
    """
    stages: list[Stage] = [make_post_stage(cfg), *get_registered_stages()]
    stages.sort(key=lambda s: checkpoint_index(s.checkpoint))
    return stages


__all__ = [
    "CHECKPOINT_ORDER",
    "TERMINAL_CHECKPOINT",
    "DEFAULT_BACKOFF_SECONDS",
    "Stage",
    "register_stage",
    "get_registered_stages",
    "clear_registered_stages",
    "parse_backoff",
    "checkpoint_index",
    "pending_stages",
    "post_time_for_date",
    "is_past_post_time",
    "run_stage_with_retry",
    "run_pipeline",
    "resume_run",
    "make_post_stage",
    "build_drivable_stages",
    "now_tehran",
    "TEHRAN_TZ",
]
