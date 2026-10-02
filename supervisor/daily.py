import random
from datetime import datetime
from zoneinfo import ZoneInfo

from supervisor.store import (
    get_unused_cards,
    mark_cards_picked,
    IdeaCard,
)
from supervisor.config import load_supervisor_config


TEHRAN_TZ = ZoneInfo("Asia/Tehran")


def now_tehran() -> datetime:
    return datetime.now(TEHRAN_TZ)


def pick_candidate_cards(run_id: str, picked_date: str) -> list[IdeaCard]:
    """Pick candidate cards for a daily run.
    
    Default: uniform random pick of 5 unused cards via random.sample.
    When candidates_llm_ranking=true: call LLM ranking (opt-in), fallback to random on failure.
    """
    cfg = load_supervisor_config()
    count = cfg.candidates_count
    
    unused_cards = get_unused_cards(limit=count * 10)  # Get more than needed for LLM ranking
    
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


def create_daily_run() -> dict:
    """Create a new DailyRun with 5 candidate cards picked."""
    run_id = f"run-{now_tehran().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    picked_date = now_tehran().date().isoformat()
    
    candidate_cards = pick_candidate_cards(run_id, picked_date)
    
    if not candidate_cards:
        return {
            "run_id": run_id,
            "date_tehran": picked_date,
            "candidate_card_ids": [],
            "picked_card_id": None,
            "picked_by": None,
            "hook_type": None,
            "script_status": "pending",
            "narration_file": None,
            "video_file": None,
            "caption": None,
            "hashtags": [],
            "post_status": "not_scheduled",
            "scheduled_time_tehran": None,
            "checkpoint": "cards_picked",
            "retry_count": 0,
            "last_error": None,
            "warning": "No unused cards available. Ingest more books." if len(get_unused_cards()) == 0 else f"Only {len(candidate_cards)} unused cards available. Ingest more books."
        }
    
    candidate_ids = [card.id for card in candidate_cards]
    
    # Mark all candidates as picked
    mark_cards_picked(candidate_ids, run_id, picked_date)
    
    return {
        "run_id": run_id,
        "date_tehran": picked_date,
        "candidate_card_ids": candidate_ids,
        "picked_card_id": None,
        "picked_by": None,
        "hook_type": None,
        "script_status": "pending",
        "narration_file": None,
        "video_file": None,
        "caption": None,
        "hashtags": [],
        "post_status": "not_scheduled",
        "scheduled_time_tehran": None,
        "checkpoint": "cards_picked",
        "retry_count": 0,
        "last_error": None,
        "warning": None if len(candidate_cards) >= 5 else f"Only {len(candidate_cards)} unused cards available. Ingest more books."
    }