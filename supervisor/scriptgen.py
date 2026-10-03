"""FR-4: Farsi reel script generation (skill + TTS-ready + self-check routing).

Runs the ``meta-safe-farsi-reel-script`` skill through the **raw** supervisor LLM
(``supervisor/llm.complete`` — un-scrubbed so the skill's JSON survives), then:

- parses + validates the single JSON object (status, 150-220 Farsi words,
  ``hook_type`` matches the rotated value, ``self_check.flags`` empty when
  ``passed`` is true);
- runs the FR-17 TTS-ready validator (``supervisor.farsi_norm.validate``) on the
  script + caption;
- routes: ``needs_review`` / any structural or TTS flag -> ``script_status:
  needs_review`` + a Telegram review request (the operator's ``review <text>``
  command, FR-15, edits the script) and **never auto-post**; a clean ``ok`` ->
  ``script_status: approved`` (the FR-5 ``approve`` gate advances the checkpoint).

The LLM call, Telegram send, and stores are injectable so tests run offline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from supervisor.store import DailyRun, DailyRunStore, HookRotationStore, IdeaCard
from supervisor import farsi_norm

# ---------------------------------------------------------------------------
# Skill + TTS-ready prompt constants
# ---------------------------------------------------------------------------

SKILL_FILE = Path("skills/meta-safe-farsi-reel-script/SKILL.md")

HOOK_TYPES = ("question", "myth", "story", "stat")

MIN_WORDS = 150
MAX_WORDS = 220

TTS_INSTRUCTIONS = (
    "نکات آماده‌سازی TTS را الزاماً رعایت کن:\n"
    "- خروجی را TTS-ready بنویس: زبانی صحیح، بدون انگلیسی‌سازی، با اعداد فارسی.\n"
    "- Hmakat را روی کلمات ابهام‌دار درست بگذار تا گوینده‌ی گفتاری صحیح بخواند.\n"
    "- نیم‌فاصله (ZWNJ) را درست بگذار (مثلاً می‌شود، بچه‌ها، می‌کند).\n"
    "- نشانه‌گذاریِ روانی: فقط ویرگول و علامت سؤال/تعجب؛ هر ۱۵ تا ۲۵ کلمه یک نشانه.\n"
    "فقط همان JSON یک‌تکه را بازگردان؛ هیچ متن اضافی نیاور."
)

# One TTS-ready few-shot sample (~40 Farsi words; correct ZWNJ + light prosody
# punctuation). Authored here per plan §6C — no external file.
FEW_SHOT_SAMPLE = (
    "چرا بعضی‌ها از اولِ قرار باهاشون راحت‌ن و بعضی نه؟ معمولاً مشکل اینه که\n"
    "نمی‌دونی چطور خودت رو واقعی نشون بدی، نه اینکه آدم‌ها بدجنس‌ن. وقتی دنبال\n"
    "تأیید نباشی، راحت‌تر گوش می‌دی و کمتر دفاعی جواب می‌دی. همین کار ساده،\n"
    "اعتماد را می‌سازد و تو را واقع‌بین می‌کند. برای درس‌های روزانه فالو کن،\n"
    "لینک در پروفایل."
)


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def _strip_frontmatter(text: str) -> str:
    """Return the SKILL.md body without the YAML frontmatter block."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1 :])
    return text


def load_skill_body() -> str:
    return _strip_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))


def build_system_prompt() -> str:
    """Full skill body + TTS-ready instructions + one TTS-ready few-shot sample."""
    return (
        load_skill_body()
        + "\n\n"
        + TTS_INSTRUCTIONS
        + "\n\nنمونه‌ی TTS-ready (چند‌شوت):\n"
        + FEW_SHOT_SAMPLE
    )


def build_user_prompt(card: IdeaCard, hook_type: str, recent_hooks: list[str]) -> str:
    card_json = json.dumps(
        {
            "id": card.id,
            "book": card.book,
            "claim": card.claim,
            "quote": card.quote,
            "example": card.example,
        },
        ensure_ascii=False,
    )
    recent_block = "\n".join(recent_hooks) if recent_hooks else "(هنوز نمونه‌ای نیست)"
    return (
        "ایده کارت، نوع هوکِ چرخشی، و هوک‌های ۷ روز اخیر را می‌بینی.\n"
        f"Idea card (JSON): {card_json}\n"
        f"hook_type (mandatory, use exactly this): {hook_type}\n"
        f"recent_hooks (last 7 — do not reuse these openings/types):\n{recent_block}"
    )


# ---------------------------------------------------------------------------
# JSON parsing + structural validation
# ---------------------------------------------------------------------------


def parse_json_object(raw: str) -> dict:
    """Extract and parse the single JSON object from a raw LLM string.

    Tolerates ```json fences and surrounding prose: takes the outermost ``{...}``.
    Raises ``ValueError`` when no valid object is found.
    """
    text = raw or ""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("no JSON object in LLM response")
        candidate = text[start : end + 1]
    data = json.loads(candidate)
    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object")
    return data


def count_farsi_words(text: str) -> int:
    text = (text or "").strip()
    return len(text.split()) if text else 0


def structural_flags(data: dict, expected_hook_type: str) -> list[str]:
    """Skill-output contract checks (independent of TTS normalization)."""
    flags: list[str] = []
    status = data.get("status")
    if status not in ("ok", "needs_review"):
        flags.append(f"invalid-status:{status!r}")

    script = str(data.get("script_farsi") or "")
    words = count_farsi_words(script)
    if not (MIN_WORDS <= words <= MAX_WORDS):
        flags.append(f"word-count:{words} (allowed {MIN_WORDS}-{MAX_WORDS})")

    hook = data.get("hook_type")
    if hook != expected_hook_type:
        flags.append(f"hook-mismatch:{hook!r} (expected {expected_hook_type!r})")

    self_check = data.get("self_check") or {}
    if self_check.get("passed") and self_check.get("flags"):
        flags.append("self-check-flags-nonempty")
    return flags


# ---------------------------------------------------------------------------
# Generation result
# ---------------------------------------------------------------------------


@dataclass
class ScriptResult:
    """Parsed + validated script, ready to be routed onto a DailyRun."""

    status: str = "needs_review"
    hook_type: Optional[str] = None
    script_farsi: str = ""
    target_seconds: Optional[int] = None
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    opening_line: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.status == "ok" and not self.flags

    def to_run_fields(self) -> dict:
        return {
            "hook_type": self.hook_type,
            "script_farsi": self.script_farsi,
            "caption": self.caption,
            "hashtags": list(self.hashtags),
            "script_status": "approved" if self.approved else "needs_review",
        }


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def generate_script(
    card: IdeaCard,
    hook_type: str,
    recent_hooks: Optional[list[str]] = None,
    llm_fn: Optional[Callable[[str, str], str]] = None,
) -> ScriptResult:
    """Generate + parse + validate the Farsi script for one card.

    Returns a ``ScriptResult``; ``result.approved`` is True only when the LLM
    status is ``ok`` **and** there are no structural or TTS flags.
    """
    if llm_fn is None:
        from supervisor.llm import complete as llm_fn  # noqa: PLC0415 - injectable seam

    raw = llm_fn(build_system_prompt(), build_user_prompt(card, hook_type, recent_hooks or []))

    try:
        data = parse_json_object(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("FR-4: unparseable script JSON: {}", exc)
        return ScriptResult(status="needs_review", flags=[f"json-unparseable:{exc}"])

    flags = structural_flags(data, hook_type)

    # FR-17 TTS-ready gate on the script + caption (ZWNJ / harakat / punctuation).
    script = str(data.get("script_farsi") or "")
    caption = str(data.get("caption_farsi") or "")
    flags.extend(farsi_norm.validate(script))
    flags.extend(farsi_norm.validate(caption))

    hashtags = data.get("hashtags") or []
    if not isinstance(hashtags, list):
        hashtags = [str(hashtags)]

    return ScriptResult(
        status=str(data.get("status") or "needs_review"),
        hook_type=data.get("hook_type") or hook_type,
        script_farsi=script,
        target_seconds=data.get("target_seconds"),
        caption=caption,
        hashtags=[str(h) for h in hashtags],
        opening_line=_first_line(script),
        flags=flags,
    )


# ---------------------------------------------------------------------------
# Routing onto a DailyRun (Telegram review; never auto-post)
# ---------------------------------------------------------------------------


def build_review_request(result: ScriptResult, card: IdeaCard) -> str:
    """Farsi operator message asking for a human review (``review <text>`` edits)."""
    reasons = "; ".join(result.flags) if result.flags else "status: needs_review"
    return (
        "⚠️ اسکریپت امروز را باید بررسی کنی (خودکار منتشر نمی‌شود).\n"
        f"کارت: {card.claim}\n"
        f"دلیل: {reasons}\n"
        "متن فعلی:\n"
        f"{result.script_farsi}\n"
        "برای ویرایش، متن اصلاح‌شده را با دستور بفرست:\n"
        "review <متنِ جدید>"
    )


def apply_to_run(
    run: DailyRun,
    result: ScriptResult,
    card: IdeaCard,
    store: Optional[DailyRunStore] = None,
    send_fn: Optional[Callable[[str], dict]] = None,
    hook_store: Optional[HookRotationStore] = None,
) -> DailyRun:
    """Route a generated script onto ``run`` and persist it.

    - always stores the (raw) script + caption + hashtags + the rotated hook_type;
    - ``approved`` -> ``script_status: approved`` (FR-5's approve advances the
      checkpoint); never posts.
    - ``needs_review`` / any flag -> ``script_status: needs_review`` and a Telegram
      review request; never posts.
    - records the day's hook choice in the rotation log (last-7 for ``recent_hooks``).
    """
    store = store or DailyRunStore()

    fields = result.to_run_fields()
    run.hook_type = fields["hook_type"]
    run.caption = fields["caption"]
    run.hashtags = fields["hashtags"]
    run.script_status = fields["script_status"]
    # Store the TTS-ready (normalized) script for downstream TTS (FR-6).
    run.script_farsi = farsi_norm.normalize(result.script_farsi)

    # Never auto-post: the post stage only ever runs from the approved flow (FR-5).
    if fields["script_status"] == "needs_review" and send_fn is not None:
        send_fn(build_review_request(result, card))

    # Record the day's hook choice so FR-4's rotation sees it next time.
    if hook_store is not None:
        hook_store.record(run.date_tehran, result.hook_type or "", result.opening_line)

    store.upsert_run(run)
    logger.info(
        "FR-4: run {} script_status={} flags={}", run.run_id, run.script_status, result.flags
    )
    return run
