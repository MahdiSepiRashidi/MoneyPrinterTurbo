import time
import threading
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from typing import Callable, Optional

from supervisor.config import load_supervisor_config

TEHRAN_TZ = ZoneInfo("Asia/Tehran")


def now_tehran() -> datetime:
    return datetime.now(TEHRAN_TZ)


class Scheduler:
    """In-process 30s tick loop comparing now_tehran() against due jobs.
    
    No APScheduler/cron dependency.
    """
    
    def __init__(self, tick_interval: int = 30):
        self.tick_interval = tick_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._jobs: dict[str, dict] = {}  # job_name -> {time, fn, last_run_date}
        self._lock = threading.Lock()
    
    def add_daily_job(
        self,
        name: str,
        run_time: str,
        fn: Callable[[], None],
        friday_time: Optional[str] = None,
    ) -> None:
        """Add a daily job that runs at run_time (HH:MM) on weekdays,
        and at friday_time (HH:MM) on Fridays (replaces weekday time that day)."""
        with self._lock:
            self._jobs[name] = {
                "weekday_time": self._parse_time(run_time),
                "friday_time": self._parse_time(friday_time) if friday_time else None,
                "fn": fn,
                "last_run_date": None,
            }
    
    def _parse_time(self, time_str: str) -> dtime:
        hour, minute = map(int, time_str.split(":"))
        return dtime(hour, minute, tzinfo=TEHRAN_TZ)
    
    def _should_run(self, job: dict, now: datetime) -> bool:
        today = now.date()
        if job["last_run_date"] == today:
            return False
        
        # Determine which time to use
        if now.weekday() == 4 and job["friday_time"]:  # Friday
            target_time = job["friday_time"]
        else:
            target_time = job["weekday_time"]
        
        # Check if current time >= target time (within the same day)
        now_time = now.timetz()
        return now_time >= target_time
    
    def _tick(self) -> None:
        now = now_tehran()
        with self._lock:
            for name, job in list(self._jobs.items()):
                if self._should_run(job, now):
                    try:
                        job["fn"]()
                    except Exception as e:
                        # Log error but don't crash the scheduler
                        print(f"Scheduler job '{name}' failed: {e}")
                    job["last_run_date"] = now.date()
    
    def _run_loop(self) -> None:
        while self._running:
            self._tick()
            time.sleep(self.tick_interval)
    
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


# Global scheduler instance
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        cfg = load_supervisor_config()
        _scheduler = Scheduler(tick_interval=cfg.poll_interval_seconds)
    return _scheduler


def start_scheduler() -> None:
    get_scheduler().start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.stop()