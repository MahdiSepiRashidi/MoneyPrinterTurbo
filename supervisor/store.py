import hashlib
import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

STORAGE_DIR = Path("storage")
IDEA_CARDS_FILE = STORAGE_DIR / "idea_cards.json"
IDEA_CARDS_LOCK = STORAGE_DIR / "idea_cards.json.lock"


@dataclass
class IdeaCard:
    id: str
    book: str
    claim: str
    quote: str
    example: str
    status: str = "unused"
    picked_date: Optional[str] = None
    run_id: Optional[str] = None

    @staticmethod
    def generate_id(book: str, claim: str, quote: str) -> str:
        raw = f"{book}|{claim}|{quote}".encode("utf-8")
        digest = hashlib.sha1(raw).hexdigest()[:32]
        return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "IdeaCard":
        return cls(**data)


def _ensure_storage_dir() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _acquire_lock(timeout: float = 5.0) -> None:
    _ensure_storage_dir()
    start = time.monotonic()
    while True:
        try:
            # Use O_CREAT | O_EXCL for atomic lock file creation
            fd = os.open(IDEA_CARDS_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if time.monotonic() - start > timeout:
                raise TimeoutError("Could not acquire lock")
            time.sleep(0.01)


def _release_lock() -> None:
    try:
        IDEA_CARDS_LOCK.unlink(missing_ok=True)
    except OSError:
        pass


def _load_cards() -> list[IdeaCard]:
    _ensure_storage_dir()
    if not IDEA_CARDS_FILE.exists():
        return []
    _acquire_lock()
    try:
        with IDEA_CARDS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    finally:
        _release_lock()
    return [IdeaCard.from_dict(item) for item in data]


def _save_cards(cards: list[IdeaCard]) -> None:
    _ensure_storage_dir()
    _acquire_lock()
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=STORAGE_DIR, delete=False, suffix=".tmp"
        ) as tmp:
            json.dump([c.to_dict() for c in cards], tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, IDEA_CARDS_FILE)
    finally:
        _release_lock()


def upsert_card(card: IdeaCard) -> bool:
    """
    Upsert an idea card. Returns True if inserted (new), False if skipped (duplicate).
    """
    cards = _load_cards()
    existing_ids = {c.id for c in cards}
    if card.id in existing_ids:
        return False
    cards.append(card)
    _save_cards(cards)
    return True


def get_card(card_id: str) -> Optional[IdeaCard]:
    cards = _load_cards()
    for c in cards:
        if c.id == card_id:
            return c
    return None


def get_unused_cards(limit: int = 5) -> list[IdeaCard]:
    cards = _load_cards()
    unused = [c for c in cards if c.status == "unused"]
    return unused[:limit]


def mark_cards_picked(card_ids: list[str], run_id: str, picked_date: str) -> None:
    cards = _load_cards()
    for c in cards:
        if c.id in card_ids:
            c.status = "picked"
            c.picked_date = picked_date
            c.run_id = run_id
    _save_cards(cards)


def release_cards_to_unused(card_ids: list[str]) -> None:
    cards = _load_cards()
    for c in cards:
        if c.id in card_ids:
            c.status = "unused"
            c.picked_date = None
            c.run_id = None
    _save_cards(cards)


def mark_card_used(card_id: str) -> None:
    cards = _load_cards()
    for c in cards:
        if c.id == card_id:
            c.status = "used"
    _save_cards(cards)


def get_all_cards() -> list[IdeaCard]:
    return _load_cards()