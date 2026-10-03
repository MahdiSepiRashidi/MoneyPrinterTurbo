import random
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from loguru import logger

from supervisor.store import (
    DailyRun,
    DailyRunStore,
    IdeaCard,
    IdeaCardStore,
)
from supervisor.config import load_supervisor_config

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

CARD_STORE = IdeaCardStore()


def now_tehran() -> datetime:
    return datetime.now(TEHRAN_TZ)


def pick_candidate_cards(
    run_id: str,
    picked_date: str,
    idea_store: Optional[IdeaCardStore] = None,
) -> list[IdeaCard]:
    """Pick candidate cards for a daily run.

    Default: uniform random pick of 5 unused cards via random.sample.
    When candidates_llm_ranking=true: call LLM ranking (opt-in), fallback to random on failure.
    """
    cfg = load_supervisor_config()
    count = cfg.candidates_count
    store = idea_store or CARD_STORE

    unused_cards = store.unused(limit=count * 10)  # Get more than needed for LLM ranking

    if len(unused_cards) < count:
        # Return whatever we have (will trigger warning in caller)
        return unused_cards

    if cfg.candidates_llm_ranking:
        try:
            return _pick_cards_llm_ranking(unused_cards, count)
        except Exception:
            # LLM ranking failed -> fall back to random, never block the day
            pass

    # Default: uniform random pick
    return random.sample(unused_cards, count)


def _pick_cards_llm_ranking(unused_cards: list[IdeaCard], count: int) -> list[IdeaCard]:
    """Pick cards using LLM ranking. Falls back to random on any failure."""
    from supervisor.llm import complete
    
    # Prepare card info for LLM
    card_infos = []
    for card in unused_cards:
        card_infos.append({
            "id": card.id,
            "book": card.book,
            "claim": card.claim,
            "quote": card.quote[:200],  # Truncate for context
        })
    
    system_prompt = (
        "Return the 5 unused card ids most relevant + diverse for today. "
        "JSON array of ids only."
    )
    user_prompt = f"Available cards: {card_infos}"
    
    response = complete(system_prompt, user_prompt)
    
    # Parse JSON array of ids
    import json
    try:
        selected_ids = json.loads(response.strip())
        if not isinstance(selected_ids, list):
            raise ValueError("Response is not a JSON array")
    except (json.JSONDecodeError, ValueError):
        raise ValueError("Invalid LLM response format")
    
    # Map ids back to cards
    id_to_card = {card.id: card for card in unused_cards}
    selected_cards = []
    for card_id in selected_ids[:count]:
        if card_id in id_to_card:
            selected_cards.append(id_to_card[card_id])
    
    if len(selected_cards) < count:
        raise ValueError("LLM returned insufficient valid card ids")
    
    return selected_cards


def create_daily_run(
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
) -> DailyRun:
    """Create a new DailyRun with 5 candidate cards picked and persist it."""
    store = store or DailyRunStore()
    run_id = f"run-{now_tehran().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    picked_date = now_tehran().date().isoformat()

    candidate_cards = pick_candidate_cards(run_id, picked_date, idea_store=idea_store)
    candidate_ids = [card.id for card in candidate_cards]

    # Mark all candidates as picked
    _mark_cards_picked(candidate_ids, run_id, picked_date, idea_store=idea_store)

    run = DailyRun(
        run_id=run_id,
        date_tehran=picked_date,
        candidate_card_ids=candidate_ids,
        checkpoint="cards_picked",
    )
    if len(candidate_cards) < 5:
        # <5 unused -> warning copy sent by the caller (telegram_client)
        run.last_error = (
            f"only {len(candidate_cards)} unused cards available; ingest more books"
            if candidate_cards
            else "no unused cards available; ingest more books"
        )
    store.upsert_run(run)
    return run


def _mark_cards_picked(
    card_ids: list[str],
    run_id: str,
    picked_date: str,
    idea_store: Optional[IdeaCardStore] = None,
) -> None:
    (idea_store or CARD_STORE).mark_picked(card_ids, run_id, picked_date)


def lock_pick(
    run_id: str,
    number: int,
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
) -> DailyRun:
    """Operator replied ``1``-``N``: lock the pick on the numbered candidate.

    - ``number`` is the 1-based index into ``run.candidate_card_ids``.
    - Sets ``picked_card_id`` and ``picked_by="operator"``; persists the run.
      The checkpoint stays at ``cards_picked`` — FR-5's ``approve`` advances
      it to ``script_approved`` (the media gate is FR-5's).
    - Invalid number / unknown run -> raises.
    """
    store = store or DailyRunStore()
    run = store.get_run(run_id)
    if run is None:
        raise KeyError(f"DailyRun not found: {run_id}")
    if not 1 <= number <= len(run.candidate_card_ids):
        raise ValueError(f"invalid pick number {number} (run has {len(run.candidate_card_ids)} candidates)")
    run.picked_card_id = run.candidate_card_ids[number - 1]
    run.picked_by = "operator"
    store.upsert_run(run)
    return run


# ---------------------------------------------------------------------------
# Scheduler job (registered by supervisor/__main__.py at serve start)
# ---------------------------------------------------------------------------

PICK_JOB_NAME = "daily_pick"
PICK_TIME_WEEKDAY = "08:00"
PICK_TIME_FRIDAY = "07:00"


def run_pick_job(
    store: Optional[DailyRunStore] = None,
    idea_store: Optional[IdeaCardStore] = None,
    send_fn=None,
) -> DailyRun:
    """The 08:00 Tehran job: pick 5 unused cards, persist the run, send numbered
    cards to the operator via Telegram. Returns the created DailyRun.

    ``send_fn(text)`` defaults to ``telegram_client.send_message`` (Farsi copy);
    pass a fake in tests.
    """
    if send_fn is None:
        from supervisor.telegram_client import send_message as send_fn

    run = create_daily_run(store=store, idea_store=idea_store)
    idea_store = idea_store or CARD_STORE

    if not run.candidate_card_ids:
        if run.last_error:
            send_fn(f"⚠️ {run.last_error}")
        else:
            send_fn("هیچ کارت ایده‌ای در دسترس نیست؛ کتاب بیشتری register کنید.")
        return run

    lines = [f"امروز این {len(run.candidate_card_ids)} کارت را انتخاب کردم. عدد مورد نظر را بفرستید:\n"]
    for i, card_id in enumerate(run.candidate_card_ids, start=1):
        card = _find_card(card_id, idea_store)
        if card is None:
            lines.append(f"{i}. (card {card_id})")
            continue
        lines.append(f"{i}. «{card.claim}» — {card.book}")
    text = "\n".join(lines)
    if run.last_error:
        text += f"\n\n⚠️ {run.last_error}"
    send_fn(text)
    return run


def _find_card(card_id: str, idea_store: Optional[IdeaCardStore] = None) -> Optional[IdeaCard]:
    for card in (idea_store or CARD_STORE).all():
        if card.id == card_id:
            return card
    return None


def register_pick_job(scheduler) -> None:
    """Register the 08:00 Tehran pick job on the given Scheduler."""
    scheduler.add_daily_job(
        PICK_JOB_NAME,
        PICK_TIME_WEEKDAY,
        run_pick_job,
        friday_time=PICK_TIME_FRIDAY,
    )


# ---------------------------------------------------------------------------
# FR-3: deadline job (weekday 18:00 / Friday 12:00 Tehran)
# ---------------------------------------------------------------------------

DEADLINE_JOB_NAME = "daily_pick_deadline"


def run_deadline_job(
    store: Optional[DailyRunStore] = None,
    send_fn=None,
) -> Optional[DailyRun]:
    """Deadline job: if the operator hasn't picked by the deadline, pick one of
    the day's candidates at random and set ``picked_by="fallback"``.

    ``send_fn(text)`` defaults to ``telegram_client.send_message`` (Farsi copy);
    pass a fake in tests.
    """
    store = store or DailyRunStore()
    date_str = now_tehran().date().isoformat()
    run = store.get_by_date(date_str)

    if run is None:
        logger.warning("deadline: no DailyRun for date {} — nothing to pick", date_str)
        return None

    if not run.candidate_card_ids:
        logger.warning("deadline: run {} has no candidate cards", run.run_id)
        return None

    if run.picked_card_id is not None:
        logger.info(
            "deadline: run {} already picked by {} — no-op", run.run_id, run.picked_by
        )
        return run

    chosen = random.choice(run.candidate_card_ids)
    index = run.candidate_card_ids.index(chosen) + 1
    run.picked_card_id = chosen
    run.picked_by = "fallback"
    store.upsert_run(run)
    logger.info(
        "deadline: run {} — fallback picked card {} (candidate #{}/{}); "
        "proceeding to FR-4",
        run.run_id, chosen, index, len(run.candidate_card_ids),
    )

    if send_fn is None:
        from supervisor.telegram_client import send_message as send_fn
    send_fn(
        f"⏰ مهلت انتخاب امروز گذشت؛ کارت شماره {index} "
        f"به‌طور خودکار انتخاب شد."
    )
    return run


def register_deadline_job(scheduler) -> None:
    """Register the FR-3 deadline job on the given Scheduler.

    Weekday: 18:00 Tehran; Friday: 12:00 Tehran (replaces 18:00 that day).
    Times come from config (``pick_deadline_weekday`` / ``pick_deadline_friday``).
    """
    cfg = load_supervisor_config()
    scheduler.add_daily_job(
        DEADLINE_JOB_NAME,
        cfg.pick_deadline_weekday,
        run_deadline_job,
        friday_time=cfg.pick_deadline_friday,
    )