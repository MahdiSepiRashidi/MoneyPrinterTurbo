"""FR-1: Book -> idea cards (one-time LLM pass, idempotent).

Splits a book (plain text or PDF) into overlapping chunks, sends each chunk
to the LLM for card extraction, validates the JSON response, generates
deterministic card IDs, and upserts into IdeaCardStore.

Malformed LLM output is rejected and logged; it is never persisted.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from supervisor.store import IdeaCard, IdeaCardStore, IngestProgressStore, DEFAULT_STORAGE_DIR

CHUNK_SIZE = 3000
CHUNK_OVERLAP = 500

# A card is kept only when its `lesson` is a real takeaway; shorter than this
# is treated as vague/hedged and dropped (not persisted, not needs_review).
MIN_LESSON_LEN = 12
_VALID_CARD_TYPES = {"principle", "tip", "insight"}

_SYSTEM_PROMPT = (
    "Extract teachable idea cards from the given book passage.\n"
    "A card is a GENERALIZABLE, ACTIONABLE lesson (a principle, tip, or skill) "
    "that the author states or clearly implies - something a short educational Reel "
    "could teach on its own.\n\n"
    "Return an empty array [] when the passage has no such lesson. Do NOT turn a "
    "scene, event, dialogue, or a character's moment into a card: the card must be "
    "the transferable idea, not 'what happened to a character'. Prefer proactive, "
    "skill-building takeaways; skip defeatist, manipulative, or purely-descriptive "
    "content.\n\n"
    "Each card object has exactly these fields:\n"
    '- "claim": the specific assertion (one sentence)\n'
    '- "quote": a verbatim or near-verbatim line from the passage that states/implies it\n'
    '- "example": a concrete example from the passage that illustrates it\n'
    '- "lesson": the one-sentence generalizable, actionable takeaway a viewer could apply\n'
    '- "type": one of "principle" | "tip" | "insight"\n\n'
    "Example outputs for reference:\n"
    '[{"claim": "Daily systems beat goal-setting for lasting change", '
    '"quote": "You do not rise to the level of your goals. You fall to the level of your systems.", '
    '"example": "Reading two pages a day compounds into 12 books per year.", '
    '"lesson": "Build small daily systems instead of chasing vague goals.", '
    '"type": "tip"}]\n'
    '[{"claim": "The first two weeks decide whether a habit sticks", '
    '"quote": "The first two weeks of a new habit are the most important.", '
    '"example": "Skip the workout in week one and the habit likely dies.", '
    '"lesson": "Treat the first two weeks of any new habit as the make-or-break window.", '
    '"type": "principle"}]\n\n'
    "Output a JSON array only. Do not invent content. If nothing is teachable, return []."
)


@dataclass
class IngestResult:
    book: str
    total_chunks: int
    start_chunk: int
    processed_chunks: int
    cards_created: int
    cards_review: int
    chunks_rejected: int
    llm_errors: int
    skipped_chunks: int = 0
    vague_dropped: int = 0


def read_book_text(file_path: Path) -> str:
    """Read a book from a text or PDF file, returning the full text."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(file_path)
    return file_path.read_text(encoding="utf-8")


def _read_pdf(file_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks (skip chunks shorter than 100 chars)."""
    step = chunk_size - overlap
    if step <= 0:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
    chunks: list[str] = []
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        if len(chunk.strip()) > 100:
            chunks.append(chunk)
    return chunks


def _parse_llm_response(raw: str, chunk_index: int) -> tuple[list[dict], bool, int]:
    """Parse the LLM response into a list of card dicts.

    Returns (cards, rejected, dropped_vague). `rejected` means the whole chunk
    was rejected (bad JSON / wrong type / LLM error) and nothing should be
    persisted. `dropped_vague` counts cards that parsed but had a vague/empty
    `lesson` and were dropped (not persisted, not needs_review).
    """
    raw = raw.strip()
    if not raw:
        logger.warning("chunk {}: empty LLM response, rejecting", chunk_index)
        return [], True, 0

    # Extract JSON array from the response (LLM may wrap in markdown fences).
    if raw.startswith("["):
        json_str = raw
    else:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            logger.warning("chunk {}: no JSON array in response, rejecting: {:.120}", chunk_index, raw)
            return [], True, 0

    try:
        items = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning("chunk {}: JSON parse failed ({}), rejecting: {:.120}", chunk_index, exc, raw)
        return [], True, 0

    if not isinstance(items, list):
        logger.warning("chunk {}: LLM returned {}, not a list, rejecting", chunk_index, type(items).__name__)
        return [], True, 0

    cards: list[dict] = []
    dropped_vague = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim", "")).strip()
        quote = str(item.get("quote", "")).strip()
        example = str(item.get("example", "")).strip()
        lesson = str(item.get("lesson", "")).strip()
        card_type = str(item.get("type", "")).strip().lower()
        if card_type not in _VALID_CARD_TYPES:
            card_type = "principle"

        # Quality gate: a card must carry a real, non-vague teachable takeaway.
        if len(lesson) < MIN_LESSON_LEN:
            dropped_vague += 1
            logger.debug(
                "chunk {}: dropped card with vague/empty lesson: {:.80}",
                chunk_index, lesson or "(empty)",
            )
            continue

        # Guardrail: the three supporting fields must be present to be "clean";
        # otherwise keep it flagged for human review.
        if not claim or not quote or not example:
            status = "needs_review"
            logger.debug("chunk {}: card with empty field(s) -> needs_review", chunk_index)
        else:
            status = "unused"

        cards.append(
            {
                "claim": claim or "(missing)",
                "quote": quote or "(missing)",
                "example": example or "(missing)",
                "lesson": lesson,
                "type": card_type,
                "status": status,
            }
        )

    return cards, False, dropped_vague


def ingest_book(
    file_path: Path,
    book_name: Optional[str] = None,
    storage_dir: Optional[Path] = None,
    llm_complete: Optional[Callable[[str, str], str]] = None,
    max_chunks: Optional[int] = None,
    from_chunk: Optional[int] = None,
    skip_chunks: Optional[list] = None,
) -> IngestResult:
    """Ingest a book file into idea cards via one LLM call per chunk.

    Auto-resume: unless `from_chunk` is given explicitly, the start is read
    from the per-book checkpoint in `IngestProgressStore` (`last_completed_chunk +
    1`), so an interrupted run continues where it left off instead of re-spending
    quota on chunks already answered.

    Args:
        file_path: Path to the book file (.txt, .md, or .pdf).
        book_name: Override the book name (default: file stem). Also the
            checkpoint key, so keep it consistent across batch runs.
        storage_dir: Where to store idea_cards.json (default: "storage").
        llm_complete: Override the LLM function (for testing).
        max_chunks: Process at most N chunks in this run (None = all remaining).
        from_chunk: Explicit start index (0-based). None = auto-resume.
        skip_chunks: Chunk indices to record as permanently skipped (0-based)
            without calling the LLM. Use for chunks the LLM refuses for
            content (e.g. explicit text), which would otherwise be re-tried
            forever on auto-resume. They are advanced past, logged, and stored
            in the progress row's `skipped_chunks` for later re-ingest.

    Returns:
        IngestResult with counts.
    """
    from supervisor.llm import complete as _default_llm

    if llm_complete is None:
        llm_complete = _default_llm

    if book_name is None:
        book_name = file_path.stem

    store = IdeaCardStore(storage_dir) if storage_dir is not None else IdeaCardStore()
    progress = IngestProgressStore(storage_dir) if storage_dir is not None else IngestProgressStore()

    logger.info("reading book: {}", file_path)
    text = read_book_text(file_path)
    logger.info("book text: {} characters", len(text))

    all_chunks = chunk_text(text)
    total_chunks = len(all_chunks)

    if from_chunk is None:
        start = progress.next_chunk(book_name, total_chunks)
        if start >= total_chunks:
            logger.info(
                "book '{}' already fully ingested ({} chunks); nothing to do",
                book_name, total_chunks,
            )
            return IngestResult(
                book=book_name,
                total_chunks=total_chunks,
                start_chunk=total_chunks,
                processed_chunks=0,
                cards_created=0,
                cards_review=0,
                chunks_rejected=0,
                llm_errors=0,
            )
    else:
        start = from_chunk

    end = total_chunks if max_chunks is None else min(start + max_chunks, total_chunks)
    chunks = all_chunks[start:end]

    logger.info(
        "processing chunks [{}:{}] of {} total (start={})", start, end, total_chunks, start
    )

    created = 0
    review = 0
    rejected = 0
    errors = 0
    skipped = 0
    vague_dropped = 0
    last_done = start - 1
    skip_set = set(skip_chunks or [])
    skip_set_this_run: list[int] = []

    for i, chunk in enumerate(chunks):
        chunk_idx = start + i

        if chunk_idx in skip_set:
            # Permanent content refusal: record + advance, no LLM call.
            logger.warning(
                "  chunk {} SKIPPED on request (no LLM call); recorded for later re-ingest",
                chunk_idx,
            )
            skipped += 1
            skip_set_this_run.append(chunk_idx)
            last_done = chunk_idx
            progress.mark(book_name, last_done, total_chunks, skipped_chunks=skip_set_this_run)
            continue

        logger.info("  chunk {}/{} ({} chars)", chunk_idx + 1, total_chunks, len(chunk))

        raw_response = llm_complete(_SYSTEM_PROMPT, chunk)

        if not raw_response or raw_response.startswith("Error:"):
            # Hard LLM failure (quota/transient): do NOT advance the checkpoint
            # so a re-run retries this chunk.
            errors += 1
            logger.warning("  chunk {}: LLM error: {:.100}", chunk_idx + 1, raw_response)
            continue

        cards, chunk_rejected, dropped_vague = _parse_llm_response(raw_response, chunk_idx)

        if chunk_rejected:
            rejected += 1
            # An answered-but-malformed chunk still counts as processed.
            last_done = chunk_idx
            progress.mark(book_name, last_done, total_chunks, skipped_chunks=skip_set_this_run)
            continue

        vague_dropped += dropped_vague

        for card_dict in cards:
            claim = card_dict["claim"]
            quote = card_dict["quote"]
            example = card_dict["example"]
            status = card_dict.get("status", "unused")
            lesson = card_dict.get("lesson", "")
            card_type = card_dict.get("type", "principle")

            card_id = IdeaCard.generate_id(book_name, claim, quote)
            card = IdeaCard(
                id=card_id,
                book=book_name,
                claim=claim,
                quote=quote,
                example=example,
                lesson=lesson,
                type=card_type,
                status=status,
            )
            is_new = store.upsert_card(card)
            if is_new:
                created += 1
            if status == "needs_review":
                review += 1

        # Chunk answered: persist the checkpoint so an interruption resumes here.
        last_done = chunk_idx
        progress.mark(book_name, last_done, total_chunks, skipped_chunks=skip_set_this_run)

    result = IngestResult(
        book=book_name,
        total_chunks=total_chunks,
        start_chunk=start,
        processed_chunks=len(chunks),
        cards_created=created,
        cards_review=review,
        chunks_rejected=rejected,
        llm_errors=errors,
        skipped_chunks=skipped,
        vague_dropped=vague_dropped,
    )

    logger.info(
        "ingest complete: {} new cards, {} needs_review, {} vague dropped, "
        "{} chunks rejected, {} LLM errors, {} skipped",
        result.cards_created,
        result.cards_review,
        result.vague_dropped,
        result.chunks_rejected,
        result.llm_errors,
        result.skipped_chunks,
    )

    if last_done + 1 < total_chunks:
        logger.info(
            "book '{}' has {} more chunk(s) to go; re-run to resume from chunk {}",
            book_name, total_chunks - last_done - 1, last_done + 1,
        )

    return result
