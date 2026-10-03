"""Minimal Telegram Bot API client for the supervisor's operator surface.

FR-2 only needs *outbound* delivery (numbered card shortlist at 08:00 Tehran,
replies for confirmation). The full long-poll command bot is FR-15's
(``supervisor/telegram_bot.py``); this module is deliberately tiny:

- ``send_message(text)`` -> operator chat, Farsi copy, ``[proxy]`` honored (R-7).
- ``send_video(path, caption)`` -> manual fallback (FR-12), file <48 MB.
- 429 -> sleep ``parameters.retry_after`` and retry.

Credentials come from ``supervisor.telegram_bot_token`` / ``supervisor.telegram_chat_id``
(``config.toml`` -> ``[supervisor]``).
"""

from __future__ import annotations

import tomllib
from typing import Optional

import requests
from loguru import logger

TG_API = "https://api.telegram.org"


def _load_proxies() -> Optional[dict]:
    """Read ``[proxy]`` from config.toml for Telegram egress (R-7), like buffer.py."""
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


class TelegramClient:
    """Outbound-only Telegram Bot API client (no long-poll; FR-15 owns that)."""

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        *,
        base_url: str = TG_API,
        proxies: Optional[dict] = None,
        timeout: int = 60,
    ) -> None:
        if not bot_token:
            raise ValueError("telegram_bot_token is required (supervisor.telegram_bot_token)")
        if not chat_id:
            raise ValueError("telegram_chat_id is required (supervisor.telegram_chat_id)")
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.base_url = base_url.rstrip("/")
        self.proxies = proxies or None
        self.timeout = timeout

    def _post(self, method: str, **params) -> dict:
        """POST /bot<token>/<method>; retry once per 429 with retry_after."""
        url = f"{self.base_url}/bot{self.bot_token}/{method}"
        for attempt in range(3):
            response = requests.post(
                url, params=params, timeout=self.timeout, proxies=self.proxies
            )
            if response.status_code == 429:
                retry_after = (response.json().get("parameters") or {}).get("retry_after", 5)
                logger.warning("Telegram 429; sleeping {}s", retry_after)
                import time

                time.sleep(retry_after)
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"Telegram {method} failed ({response.status_code}): {response.text}")
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(f"Telegram {method} rejected: {body}")
            return body
        raise RuntimeError(f"Telegram {method}: still rate-limited after retries")

    def send_message(self, text: str, **params) -> dict:
        """Send a text message to the operator chat (Farsi copy per spec)."""
        return self._post("sendMessage", chat_id=self.chat_id, text=text, **params)

    def send_video(self, video_path: str, caption: str = "", **params) -> dict:
        """Send a video file (<48 MB) with caption (manual fallback, FR-12)."""
        with open(video_path, "rb") as fh:
            data = {**params, "chat_id": self.chat_id, "caption": caption}
            files = {"video": (video_path.rsplit("/", 1)[-1], fh)}
            url = f"{self.base_url}/bot{self.bot_token}/sendVideo"
            for attempt in range(3):
                response = requests.post(
                    url, data=data, files=files, timeout=self.timeout, proxies=self.proxies
                )
                if response.status_code == 429:
                    retry_after = (response.json().get("parameters") or {}).get("retry_after", 5)
                    import time

                    time.sleep(retry_after)
                    continue
                if response.status_code >= 400:
                    raise RuntimeError(f"Telegram sendVideo failed ({response.status_code}): {response.text}")
                body = response.json()
                if not body.get("ok"):
                    raise RuntimeError(f"Telegram sendVideo rejected: {body}")
                return body
            raise RuntimeError("Telegram sendVideo: still rate-limited after retries")


_client: Optional[TelegramClient] = None


def get_client(cfg=None) -> TelegramClient:
    """Build (and cache) the client from supervisor config."""
    global _client
    if _client is None:
        from supervisor.config import load_supervisor_config

        cfg = cfg or load_supervisor_config()
        _client = TelegramClient(
            cfg.telegram_bot_token,
            cfg.telegram_chat_id,
            proxies=_load_proxies(),
        )
    return _client


def send_message(text: str, cfg=None, client: Optional[TelegramClient] = None) -> dict:
    """Convenience: send a message to the operator chat using the configured client."""
    return (client or get_client(cfg)).send_message(text)


def send_video(video_path: str, caption: str = "", cfg=None, client: Optional[TelegramClient] = None) -> dict:
    """Convenience: send a video to the operator chat using the configured client."""
    return (client or get_client(cfg)).send_video(video_path, caption=caption)


__all__ = [
    "TG_API",
    "TelegramClient",
    "get_client",
    "send_message",
    "send_video",
]
