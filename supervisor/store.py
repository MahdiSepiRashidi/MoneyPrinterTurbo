"""JSON data stores backing the supervisor (IdeaCard, DailyRun, ClipUsageLog,
HookRotationLog, MusicUsageLog).

Each store owns one JSON file under a StorageDir:
- atomic writes (temp file + os.replace)
- a per-store file lock (msvcrt.locking on Windows, fcntl.flock on POSIX) so
  concurrent supervisor processes cannot interleave writes
- store-specific retention rules applied on every save
"""

import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Union

IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    import msvcrt
else:
    import fcntl

DEFAULT_STORAGE_DIR = "storage"


class StorageDir:
    """The supervisor storage directory; `mkdir -p` is done at construction."""

    def __init__(self, root: Union[str, Path] = DEFAULT_STORAGE_DIR):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def join(self, filename: str) -> Path:
        return self.root / filename


class _FileLock:
    """Exclusive per-store file lock.

    msvcrt.locking (Windows) / fcntl.flock (POSIX); the lock is released
    automatically when the owning process dies, so a crash cannot leave a
    dangling lock behind.
    """

    def __init__(self, lock_file: Path, timeout: float = 5.0):
        self._lock_file = lock_file
        self._timeout = timeout
        self._fd: Optional[int] = None

    def __enter__(self) -> "_FileLock":
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self._lock_file), os.O_RDWR | os.O_CREAT)
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                if IS_WINDOWS:
                    msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    os.close(self._fd)
                    self._fd = None
                    raise TimeoutError(
                        f"Could not acquire lock {self._lock_file.name} within {self._timeout}s"
                    )
                time.sleep(0.01)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fd is None:
            return
        try:
            if IS_WINDOWS:
                try:
                    msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)
            self._fd = None


def _atomic_write_json(path: Path, rows: list[dict]) -> None:
    """Write rows to path atomically: temp file + fsync + os.replace (rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


@dataclass
class IdeaCard:
    id: str
    book: str
    claim: str
    quote: str
    example: str
    lesson: str = ""
    type: str = "principle"
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


@dataclass
class DailyRun:
    run_id: str
    date_tehran: str
    candidate_card_ids: list[str] = field(default_factory=list)
    picked_card_id: Optional[str] = None
    picked_by: Optional[str] = None
    hook_type: Optional[str] = None
    script_status: str = "pending"
    narration_file: Optional[str] = None
    video_file: Optional[str] = None
    caption: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    post_status: str = "not_scheduled"
    scheduled_time_tehran: Optional[str] = None
    checkpoint: str = "cards_picked"
    retry_count: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DailyRun":
        return cls(**data)


class JsonStore:
    """One JSON file + a per-file lock; atomic writes; generic upsert/get_by_id/list."""

    filename: str = ""
    id_key: str = "id"

    def __init__(self, storage_dir: Union[str, Path] = DEFAULT_STORAGE_DIR):
        self.storage_dir = StorageDir(storage_dir)

    @property
    def file(self) -> Path:
        return self.storage_dir.join(self.filename)

    @property
    def lock_file(self) -> Path:
        return self.storage_dir.join(f"{self.filename}.lock")

    def _read_unlocked(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            with self.file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except ValueError:
            # A corrupt file (external tampering, power loss outside atomicity)
            # is treated as empty so the next save heals the store.
            return []
        return data if isinstance(data, list) else []

    def _write_unlocked(self, rows: list[dict]) -> None:
        _atomic_write_json(self.file, self._retention(rows))

    def _retention(self, rows: list[dict]) -> list[dict]:
        return rows

    def load(self) -> list[dict]:
        with _FileLock(self.lock_file):
            return self._read_unlocked()

    def save(self, rows: list[dict]) -> None:
        with _FileLock(self.lock_file):
            self._write_unlocked(rows)

    def list(self) -> list[dict]:
        return self.load()

    def upsert(self, row: dict) -> bool:
        """Insert or replace the row keyed by `id_key`. True if newly inserted."""
        with _FileLock(self.lock_file):
            rows = self._read_unlocked()
            key = row.get(self.id_key)
            filtered = [r for r in rows if r.get(self.id_key) != key]
            existed = len(filtered) != len(rows)
            filtered.append(row)
            self._write_unlocked(filtered)
            return not existed

    def get_by_id(self, key) -> Optional[dict]:
        for row in self.load():
            if row.get(self.id_key) == key:
                return row
        return None


class IdeaCardStore(JsonStore):
    """storage/idea_cards.json"""

    filename = "idea_cards.json"
    id_key = "id"

    def upsert_card(self, card: IdeaCard) -> bool:
        return self.upsert(card.to_dict())

    def get_card(self, card_id: str) -> Optional[IdeaCard]:
        row = self.get_by_id(card_id)
        return IdeaCard.from_dict(row) if row is not None else None

    def all(self) -> list[IdeaCard]:
        return [IdeaCard.from_dict(r) for r in self.load()]

    def unused(self, limit: int = 5) -> list[IdeaCard]:
        cards = [c for c in self.all() if c.status == "unused"]
        return cards[:limit]

    def mark_picked(self, card_ids: list[str], run_id: str, picked_date: str) -> None:
        with _FileLock(self.lock_file):
            rows = self._read_unlocked()
            for r in rows:
                if r.get("id") in card_ids:
                    r["status"] = "picked"
                    r["picked_date"] = picked_date
                    r["run_id"] = run_id
            self._write_unlocked(rows)

    def release_to_unused(self, card_ids: list[str]) -> None:
        with _FileLock(self.lock_file):
            rows = self._read_unlocked()
            for r in rows:
                if r.get("id") in card_ids:
                    r["status"] = "unused"
                    r["picked_date"] = None
                    r["run_id"] = None
            self._write_unlocked(rows)

    def mark_used(self, card_id: str) -> None:
        with _FileLock(self.lock_file):
            rows = self._read_unlocked()
            for r in rows:
                if r.get("id") == card_id:
                    r["status"] = "used"
            self._write_unlocked(rows)


class DailyRunStore(JsonStore):
    """storage/daily_runs.json — one run per Tehran date."""

    filename = "daily_runs.json"
    id_key = "run_id"

    def upsert_run(self, run: DailyRun) -> bool:
        return self.upsert(run.to_dict())

    def get_run(self, run_id: str) -> Optional[DailyRun]:
        row = self.get_by_id(run_id)
        return DailyRun.from_dict(row) if row is not None else None

    def get_by_date(self, date_tehran: str) -> Optional[DailyRun]:
        for row in self.load():
            if row.get("date_tehran") == date_tehran:
                return DailyRun.from_dict(row)
        return None

    def all(self) -> list[DailyRun]:
        return [DailyRun.from_dict(r) for r in self.load()]


class ClipUsageStore(JsonStore):
    """storage/clip_usage.json — rows {pexels_asset_id, used_date, run_id};
    rows older than 30 days are pruned on every write (FR-8 dedup source)."""

    filename = "clip_usage.json"
    id_key = "pexels_asset_id"
    RETENTION_DAYS = 30

    def _retention(self, rows: list[dict]) -> list[dict]:
        cutoff = (date.today() - timedelta(days=self.RETENTION_DAYS)).isoformat()
        return [r for r in rows if str(r.get("used_date", "")) >= cutoff]

    def upsert(self, row: dict) -> bool:
        """Idempotent per (pexels_asset_id, used_date, run_id) usage event."""
        with _FileLock(self.lock_file):
            rows = self._read_unlocked()
            key = (
                row.get("pexels_asset_id"),
                row.get("used_date"),
                row.get("run_id"),
            )
            filtered = [
                r for r in rows
                if (r.get("pexels_asset_id"), r.get("used_date"), r.get("run_id"))
                != key
            ]
            existed = len(filtered) != len(rows)
            filtered.append(row)
            self._write_unlocked(filtered)
            return not existed

    def add(self, asset_id: str, used_date: str, run_id: str) -> None:
        self.upsert(
            {"pexels_asset_id": asset_id, "used_date": used_date, "run_id": run_id}
        )

    def recent_asset_ids(self, days: int = RETENTION_DAYS) -> set[str]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return {
            r["pexels_asset_id"]
            for r in self.load()
            if str(r.get("used_date", "")) >= cutoff
        }

    def is_recently_used(self, asset_id: str, days: int = RETENTION_DAYS) -> bool:
        return asset_id in self.recent_asset_ids(days=days)


class HookRotationStore(JsonStore):
    """storage/hook_rotation.json — rows {date_tehran, hook_type, opening_line};
    only the last 7 entries are kept on every write."""

    filename = "hook_rotation.json"
    id_key = "date_tehran"
    KEEP_LAST = 7

    def _retention(self, rows: list[dict]) -> list[dict]:
        return rows[-self.KEEP_LAST:]

    def record(self, date_tehran: str, hook_type: str, opening_line: str) -> None:
        self.upsert(
            {
                "date_tehran": date_tehran,
                "hook_type": hook_type,
                "opening_line": opening_line,
            }
        )

    def recent(self, days: int = 7) -> list[dict]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return [h for h in self.load() if str(h.get("date_tehran", "")) >= cutoff]


class MusicUsageStore(JsonStore):
    """storage/music_usage.json — rows {pexels_audio_track_id, used_date};
    FR-7 "not reused on the next day"."""

    filename = "music_usage.json"
    id_key = "pexels_audio_track_id"

    def upsert(self, row: dict) -> bool:
        """Idempotent per (pexels_audio_track_id, used_date) pair."""
        with _FileLock(self.lock_file):
            rows = self._read_unlocked()
            pair = (row.get("pexels_audio_track_id"), row.get("used_date"))
            filtered = [
                r for r in rows
                if (r.get("pexels_audio_track_id"), r.get("used_date")) != pair
            ]
            existed = len(filtered) != len(rows)
            filtered.append(row)
            self._write_unlocked(filtered)
            return not existed

    def add(self, track_id: str, used_date: str) -> None:
        self.upsert({"pexels_audio_track_id": track_id, "used_date": used_date})

    def yesterday_track_id(self) -> Optional[str]:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        rows = [r for r in self.load() if r.get("used_date") == yesterday]
        return rows[-1]["pexels_audio_track_id"] if rows else None


class IngestProgressStore(JsonStore):
    """storage/ingest_progress.json — per-book FR-1 ingestion checkpoint.

    One row per book, keyed by `book`:
    `{book, last_completed_chunk, total_chunks, updated_at}`.
    `last_completed_chunk` is the highest chunk index that got a real LLM
    answer (empty [] and malformed responses count as answered; only hard
    LLM `Error:` responses leave the checkpoint un-advanced so a quota
    failure is retried on the next run). Re-running without an explicit
    `--from-chunk` resumes from `last_completed_chunk + 1`.
    """

    filename = "ingest_progress.json"
    id_key = "book"

    def get(self, book: str) -> Optional[dict]:
        return self.get_by_id(book)

    def mark(self, book: str, last_completed_chunk: int, total_chunks: int,
             skipped_chunks: Optional[list] = None) -> None:
        row = {
            "book": book,
            "last_completed_chunk": last_completed_chunk,
            "total_chunks": total_chunks,
            "updated_at": time.time(),
        }
        if skipped_chunks is not None:
            row["skipped_chunks"] = skipped_chunks
        self.upsert(row)

    def next_chunk(self, book: str, total_chunks: int) -> int:
        """The chunk index to start from on an auto-resume (or 0)."""
        row = self.get(book)
        if row is None:
            return 0
        nxt = int(row.get("last_completed_chunk", -1)) + 1
        return min(nxt, total_chunks)
