"""FR-5: script approval gate (text only, via Telegram).

The video is built only after the operator replies ``approve``; no media stage
(FR-6 through FR-9 + post) runs before approval. The three operator commands drive
the day's ``DailyRun`` state. The Telegram transport that delivers the operator's
text reply is FR-15's (``supervisor/telegram_bot.py``); this module is the pure
gate logic it calls, so the state machine is testable today and transport-agnostic.

- ``approve`` -> ``checkpoint = "script_approved"``, ``script_status = "approved"``;
  the media continuation (FR-6..9 + post) is released on this event.
- ``rewrite`` -> at most one script re-generation (spec §6 C); re-enters the gate.
- ``reject``  -> ``script_status = "rejected"``, ``post_status = "failed"``; all five
  candidate cards released to ``unused``; the day-missed alert path is reached.

Every command sends Farsi text to the operator via an injectable ``send_fn``
(defaulting to ``telegram_client.send_message``). The media continuation, LLM
regeneration, stores, and day-missed alert are all injectable seams so tests run
offline.
"""

from __future__ import annotations

from typing import Callable, Optional

from loguru import logger

from supervisor import flow, scriptgen
from supervisor.daily import choose_hook_type
from supervisor.store import (
    DailyRun,
    DailyRunStore,
    HookRotationStore,
    IdeaCardStore,
)

# spec §6 C: exactly one re-generation of the script before the operator must
# approve or reject.
MAX_REWRITES = 1

# Card-lifecycle + gate checkpoints (data model: idea_cards / daily_runs).
PICKED_CHECKPOINT = "cards_picked"
APPROVED_CHECKPOINT = "script_approved"


def _default_send() -> Callable[[str], dict]:
    from supervisor.telegram_client import send_message  # noqa: PLC0415 - transport seam

    return send_message


def _recent_hooks(hook_store: HookRotationStore, today: str) -> list[str]:
    """The last-7 ``hook_type`` + opening lines for the scriptgen LLM input."""
    rows = [r for r in hook_store.load() if str(r.get("date_tehran", "")) < today]
    return [
        f"{r.get('hook_type', '?')} | {r.get('opening_line', '')}" for r in rows[-7:]
    ]


def resolve_run(
    store: Optional[DailyRunStore] = None,
    run_id: Optional[str] = None,
    date_tehran: Optional[str] = None,
) -> DailyRun:
    """Find the ``DailyRun`` to operate on: by ``run_id``, else today's run."""
    store = store or DailyRunStore()
    if run_id is not None:
        run = store.get_run(run_id)
        if run is None:
            raise KeyError(f"DailyRun not found: {run_id}")
        return run
    if date_tehran is None:
        date_tehran = flow.now_tehran().date().isoformat()
    run = store.get_by_date(date_tehran)
    if run is None:
        raise KeyError(f"no DailyRun for {date_tehran}")
    return run


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------


def approve(
    run: DailyRun,
    *,
    store: Optional[DailyRunStore] = None,
    media_fn: Optional[Callable[[DailyRun], None]] = None,
    send_fn: Optional[Callable[[str], dict]] = None,
) -> DailyRun:
    """The operator's ``approve``: pass the gate so media stages may start.

    - Advances ``run.checkpoint`` to ``"script_approved"`` and sets
      ``script_status = "approved"``; the FR-5 media gate now releases
      ``video_built`` / ``post`` stages.
    - Fires the optional ``media_fn(run)`` continuation on this event (FR-6..9 +
      post wire in their concrete stages; today the post stage is the only one).
    - Idempotent: a run already at/past the approval boundary is a no-op.
    """
    store = store or DailyRunStore()
    send_fn = send_fn or _default_send()

    if flow.checkpoint_index(run.checkpoint) >= flow.checkpoint_index(APPROVED_CHECKPOINT):
        logger.info("FR-5: run {} already approved; no-op", run.run_id)
        return run
    if not run.picked_card_id:
        logger.warning("FR-5: approve ignored for run {} (no picked card yet)", run.run_id)
        send_fn("هنوز کارتی انتخاب نشده؛ اول کارت را انتخاب کن.")
        return run

    run.checkpoint = APPROVED_CHECKPOINT
    run.script_status = "approved"
    run.last_error = None
    store.upsert_run(run)
    logger.info("FR-5: run {} approved; media gate released", run.run_id)

    # The media continuation starts only on this event (the FR-5 gate).
    if media_fn is not None:
        media_fn(run)
    send_fn("تأیید شد؛ ساخت فیلم آغاز می‌شود.")
    return run


# ---------------------------------------------------------------------------
# rewrite
# ---------------------------------------------------------------------------


def rewrite(
    run: DailyRun,
    *,
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
    hook_store: Optional[HookRotationStore] = None,
    llm_fn: Optional[Callable[[str, str], str]] = None,
    send_fn: Optional[Callable[[str], dict]] = None,
) -> DailyRun:
    """The operator's ``rewrite``: exactly one script re-generation, then re-enter
    the approval gate. A second ``rewrite`` is refused (``MAX_REWRITES`` cap) and the
    operator is told to approve or reject instead.
    """
    store = store or DailyRunStore()
    idea_store = idea_store or IdeaCardStore()
    hook_store = hook_store or HookRotationStore()
    send_fn = send_fn or _default_send()

    if run.rewrite_count >= MAX_REWRITES:
        logger.info("FR-5: run {} rewrite cap reached; refusing", run.run_id)
        send_fn("دوباره‌نویسی قبلاً انجام شده؛ لطفاً approve یا reject بفرست.")
        return run

    card = idea_store.get_card(run.picked_card_id) if run.picked_card_id else None
    if card is None:
        logger.warning("FR-5: rewrite ignored for run {} (picked card not found)", run.run_id)
        send_fn("کارت انتخاب‌شده پیدا نشد؛ دوباره کارتی انتخاب کن.")
        return run

    hook_type = run.hook_type or choose_hook_type(run.date_tehran, hook_store=hook_store)
    recent = _recent_hooks(hook_store, run.date_tehran)
    result = scriptgen.generate_script(card, hook_type, recent, llm_fn=llm_fn)
    # apply_to_run stores the script + caption + hashtags + hook, sends the review
    # request when the script is not clean, and persists the run.
    scriptgen.apply_to_run(
        run, result, card, store=store, send_fn=send_fn, hook_store=hook_store
    )

    # Re-enter the gate: the operator must approve the new script before media runs.
    run.rewrite_count += 1
    run.checkpoint = PICKED_CHECKPOINT
    run.last_error = None
    store.upsert_run(run)
    logger.info(
        "FR-5: run {} rewritten ({}/{}); gate re-entered (script_status={})",
        run.run_id, run.rewrite_count, MAX_REWRITES, run.script_status,
    )
    send_fn(
        "نسخه‌ی دوباره‌نویسی‌شده آماده است (دوباره‌نویسی {}/{}). "
        "لطفاً approve یا reject بفرست.".format(run.rewrite_count, MAX_REWRITES)
    )
    return run


# ---------------------------------------------------------------------------
# reject
# ---------------------------------------------------------------------------


def reject(
    run: DailyRun,
    *,
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
    send_fn: Optional[Callable[[str], dict]] = None,
    alert_fn: Optional[Callable[[DailyRun], None]] = None,
) -> DailyRun:
    """The operator's ``reject``: do not build/post today's reel.

    - ``script_status = "rejected"``, ``post_status = "failed"``.
    - All five candidate cards released back to ``unused`` (card lifecycle).
    - Reaches the day-missed alert path: ``alert_fn(run)`` fires when supplied
      (FR-13/FR-15 route the delivery); the operator also gets a Farsi note that
      no reel will be posted today.
    """
    store = store or DailyRunStore()
    idea_store = idea_store or IdeaCardStore()
    send_fn = send_fn or _default_send()

    run.script_status = "rejected"
    run.post_status = "failed"
    store.upsert_run(run)

    if run.candidate_card_ids and idea_store is not None:
        idea_store.release_to_unused(list(run.candidate_card_ids))
        logger.info(
            "FR-5: run {} rejected; {} card(s) released to unused",
            run.run_id, len(run.candidate_card_ids),
        )

    # Operator-driven day miss: no reel today.
    send_fn("رد شد؛ کارت‌ها آزاد شدند و امروز ریل منتشر نمی‌شود.")
    if alert_fn is not None:
        alert_fn(run)
    return run


# ---------------------------------------------------------------------------
# Command dispatch (what FR-15's long-poll bot calls on an operator reply)
# ---------------------------------------------------------------------------


def handle_command(
    command: str,
    run: DailyRun,
    *,
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
    hook_store: Optional[HookRotationStore] = None,
    llm_fn: Optional[Callable[[str, str], str]] = None,
    media_fn: Optional[Callable[[DailyRun], None]] = None,
    send_fn: Optional[Callable[[str], dict]] = None,
    alert_fn: Optional[Callable[[DailyRun], None]] = None,
) -> DailyRun:
    """Route an operator command word (``approve`` / ``rewrite`` / ``reject``) to its
    gate handler. Unknown commands get a Farsi help line and leave the run untouched.
    """
    key = (command or "").strip().lower()
    if key in ("approve", "تأیید", "تایید"):
        return approve(
            run, store=store, media_fn=media_fn, send_fn=send_fn
        )
    if key in ("rewrite", "دوباره", "دوباره‌نویسی"):
        return rewrite(
            run, store=store, idea_store=idea_store, hook_store=hook_store,
            llm_fn=llm_fn, send_fn=send_fn,
        )
    if key in ("reject", "رد"):
        return reject(
            run, store=store, idea_store=idea_store, send_fn=send_fn, alert_fn=alert_fn
        )
    send_fn = send_fn or _default_send()
    send_fn("دستور نامعلوم. یکی را بفرست: approve / rewrite / reject")
    return run


__all__ = [
    "MAX_REWRITES",
    "PICKED_CHECKPOINT",
    "APPROVED_CHECKPOINT",
    "resolve_run",
    "approve",
    "rewrite",
    "reject",
    "handle_command",
]
