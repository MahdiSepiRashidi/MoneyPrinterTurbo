import os
from pathlib import Path
from typing import Any, Optional

import toml

CONFIG_DIR = Path(".")
CONFIG_FILE = CONFIG_DIR / "config.toml"
CONFIG_EXAMPLE_FILE = CONFIG_DIR / "config.example.toml"


class SupervisorConfig:
    def __init__(self, config_dict: dict[str, Any]):
        supervisor = config_dict.get("supervisor", {})
        self.enabled: bool = supervisor.get("enabled", True)
        self.telegram_bot_token: str = supervisor.get("telegram_bot_token", "")
        self.telegram_chat_id: str = supervisor.get("telegram_chat_id", "")
        self.tts_voice: str = supervisor.get("tts_voice", "gemini:Charon")
        self.candidates_llm_ranking: bool = supervisor.get("candidates_llm_ranking", False)
        self.candidates_count: int = supervisor.get("candidates_count", 5)
        self.pick_deadline_weekday: str = supervisor.get("pick_deadline_weekday", "18:00")
        self.pick_deadline_friday: str = supervisor.get("pick_deadline_friday", "12:00")
        self.post_time_weekday: str = supervisor.get("post_time_weekday", "20:00")
        self.post_time_friday: str = supervisor.get("post_time_friday", "14:00")
        self.buffer_api_key: str = supervisor.get("buffer_api_key", "")
        self.buffer_base_url: str = supervisor.get("buffer_base_url", "https://api.buffer.com")
        self.buffer_organization_id: str = supervisor.get("buffer_organization_id", "")
        self.buffer_channel_id: str = supervisor.get("buffer_channel_id", "")
        self.buffer_reel_type: str = supervisor.get("buffer_reel_type", "reel")
        self.buffer_media_host: str = supervisor.get("buffer_media_host", "cloudinary")
        self.clip_max_downloads: int = supervisor.get("clip_max_downloads", 10000)
        self.bgm_moods: list[str] = supervisor.get("bgm_moods", ["calm", "motivational", "reflective", "hopeful"])
        self.bgm_volume: float = supervisor.get("bgm_volume", 0.2)
        self.retry_backoff_seconds: str = supervisor.get("retry_backoff_seconds", "30,120,600")
        self.poll_interval_seconds: int = supervisor.get("poll_interval_seconds", 30)

    @classmethod
    def load(cls) -> "SupervisorConfig":
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                config_dict = toml.load(f)
        else:
            config_dict = {}
        return cls(config_dict)


def load_supervisor_config() -> SupervisorConfig:
    return SupervisorConfig.load()