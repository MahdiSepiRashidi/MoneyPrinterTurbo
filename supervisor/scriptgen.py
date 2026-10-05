"""FR-4: Farsi reel script generation (skill + TTS-ready + self-check routing).

Runs the ``meta-safe-farsi-reel-script`` skill through the **raw** supervisor LLM
(``supervisor/llm.complete`` — un-scrubbed so the skill's JSON survives), then:

- parses + validates the single JSON object (status, 150-220 Farsi words,
  ``hook_type`` matches the rotated value, ``self_check.flags`` empty when
  ``passed`` is true);
- FR-10: validates the ``caption_farsi`` (1-2 Farsi lines, not a verbatim
  repeat of the narration, exactly one follow+bio soft CTA) and ``hashtags``
  (3-5 items, Farsi-first) contract fields;
- runs the FR-17 TTS-ready validator (``supervisor.farsi_norm.validate``) on the
  script + caption;
- routes: ``needs_review`` / any structural or TTS flag -> ``script_status:
  needs_review`` + a Telegram review request (the operator's ``review <text>``
  command, FR-15, edits the script) and **never auto-post**; a clean ``ok`` ->
  ``script_status: approved`` (the FR-5 ``approve`` gate advances the checkpoint).

The LLM call, Telegram send, and stores are injectable so tests run offline.
"""

from __future__ import annotations

import ast
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
    "- تعداد کلماتِ script_farsi الزاماً بین 150 تا 220 کلمه باشد؛ قبل از ارسال بشمار و هدف 200 تا 210 کلمه باشد.\n"
    "- هراکات را روی کلمات ابهام‌دار درست بگذار تا گوینده‌ی گفتاری صحیح بخواند.\n"
    "- نیم‌فاصله (ZWNJ) را درست بگذار (مثلاً می‌شود، بچه‌ها، می‌کند).\n"
    "- نشانه‌گذاریِ روانی: فقط ویرگول و علامت سؤال/تعجب؛ هر 10 تا 25 کلمه یک نشانه؛ از تراکم نشانه پرهیز کن.\n"
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
    Gemini occasionally emits single-quoted (Python-style) JSON, so a strict
    ``json.loads`` failure falls back to ``ast.literal_eval``.
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
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            data = ast.literal_eval(candidate)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(f"unparseable JSON object: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object")
    return data


def count_farsi_words(text: str) -> int:
    text = (text or "").strip()
    return len(text.split()) if text else 0


# ---------------------------------------------------------------------------
# FR-10: caption + hashtag contract checks
# ---------------------------------------------------------------------------

# A single Farsi/Arabic-block letter (covers all Farsi letters incl. پ چ ژ گ).
FARI_CHARS = re.compile(r"[\u0600-\u06FF]")

MIN_HASHTAGS = 3
MAX_HASHTAGS = 5
MAX_CAPTION_LINES = 2

# The only allowed soft CTA, as two markers: "follow" + "link in bio".
CTA_FOLLOW_MARKER = "فالو"
CTA_BIO_MARKER = "پروفایل"


def _squash(text: str) -> str:
    """Whitespace/ZWNJ-free form used for the verbatim-narration containment check."""
    return re.sub(r"[\s\u200c]+", "", text or "")


def caption_flags(caption: str, script: str) -> list[str]:
    """FR-10 caption contract: 1-2 Farsi lines, exactly one follow+bio CTA,
    never a verbatim repeat of the narration."""
    caption = caption or ""
    lines = [ln for ln in caption.splitlines() if ln.strip()]
    if not lines:
        return ["caption-missing"]
    flags: list[str] = []
    if len(lines) > MAX_CAPTION_LINES:
        flags.append(f"caption-lines:{len(lines)} (allowed 1-{MAX_CAPTION_LINES})")
    if not FARI_CHARS.search(caption):
        flags.append("caption-not-farsi")
    cap, scr = _squash(caption), _squash(script)
    if cap and scr and (cap in scr or scr in cap):
        flags.append("caption-verbatim-narration")
    follow = caption.count(CTA_FOLLOW_MARKER)
    bio = caption.count(CTA_BIO_MARKER)
    if follow == 0 or bio == 0:
        flags.append("caption-cta-missing")
    elif follow > 1 or bio > 1:
        flags.append(f"caption-cta-multiple (follow={follow}, bio={bio})")
    return flags


def hashtag_flags(hashtags: list) -> list[str]:
    """FR-10 hashtag contract: 3-5 items, Farsi-first (the first tag is Farsi)."""
    items = [hashtags] if isinstance(hashtags, str) else (hashtags or [])
    tags = [str(t).strip() for t in items if str(t).strip()]
    flags: list[str] = []
    n = len(tags)
    if not (MIN_HASHTAGS <= n <= MAX_HASHTAGS):
        flags.append(f"hashtags-count:{n} (allowed {MIN_HASHTAGS}-{MAX_HASHTAGS})")
    if tags and not FARI_CHARS.search(tags[0]):
        flags.append("hashtags-not-farsi-first")
    return flags


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

    # FR-10 approval gate: caption + hashtag contract. Refusals (needs_review)
    # carry their own self_check reasons and are not re-validated.
    if status == "ok":
        flags.extend(caption_flags(str(data.get("caption_farsi") or ""), script))
        hashtags = data.get("hashtags") or []
        if not isinstance(hashtags, list):
            hashtags = [str(hashtags)]
        flags.extend(hashtag_flags(hashtags))
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


MAX_REGEN_PASSES = 2


def _regen_instruction(words: int, script_flags: list[str]) -> str:
    """Close-the-gap instruction appended for a regeneration pass (plan §FR-6 recovery).

    Models (both Agnes and Gemini) systematically undershoot the 150-220 band and
    sometimes drop prosody punctuation on a rewrite, so targets sit safely inside
    the band (210 when short, 170 when long) and the punctuation requirement is
    restated. ``script_flags`` are the FR-17 flags on the previous script.
    """
    parts: list[str] = []
    if words < MIN_WORDS:
        parts.append(
            f"نکته: نسخه‌ی قبلی فقط {words} کلمه بود و از محدوده خارج است. "
            "نسخه‌ی جدید script_farsi را بلند بنویس: حدود 210 کلمه (حتماً بیش از 150، حداکثر 220)."
        )
    elif words > MAX_WORDS:
        parts.append(
            f"نکته: نسخه‌ی قبلی {words} کلمه بود و از محدوده خارج است. "
            "نسخه‌ی جدید script_farsi را فشرده‌تر بنویس: حدود 170 کلمه (حداقل 150، حداکثر 220)."
        )
    if any(f.startswith("punctuation-density") for f in script_flags):
        parts.append(
            "نکته: نشانه‌گذاریِ سبکِ روانی لازم است: هر 10 تا 20 کلمه یک ویرگول یا علامت سؤال؛ "
            "جمله‌ای بدون هیچ نشانه‌ای نیاور."
        )
    other = [f for f in script_flags if not f.startswith("punctuation-density")]
    if other:
        parts.append("نکته: مشکلات زیر را در نسخه‌ی جدید رفع کن: " + "; ".join(other))
    parts.append("همان هوک و ساختار را نگه دار. فقط JSON بازگردان.")
    return " ".join(parts)


def generate_script(
    card: IdeaCard,
    hook_type: str,
    recent_hooks: Optional[list[str]] = None,
    llm_fn: Optional[Callable[[str, str], str]] = None,
    target_words: Optional[int] = None,
) -> ScriptResult:
    """Generate + parse + validate the Farsi script for one card.

    Returns a ``ScriptResult``; ``result.approved`` is True only when the LLM
    status is ``ok`` **and** there are no structural or TTS flags. When an ``ok``
    result misses the 150-220 word band or the FR-17 TTS gate on the script, up
    to ``MAX_REGEN_PASSES`` regenerations with close-the-gap instructions are
    attempted; an unparseable or non-ok re-attempt keeps the previous result.
    Refusals (``needs_review``) are never retried.

    ``target_words`` (FR-6 recovery) steers the regeneration toward a closer
    word-count target (clamped into the 150-220 band) so the TTS duration can
    land in the 60-90 s band.
    """
    if llm_fn is None:
        from supervisor.llm import complete as llm_fn  # noqa: PLC0415 - injectable seam

    system = build_system_prompt()
    user = build_user_prompt(card, hook_type, recent_hooks or [])
    if target_words is not None:
        target = max(MIN_WORDS, min(MAX_WORDS, target_words))
        user += (
            f"\nنکته: script_farsi را حدود {target} کلمه بنویس "
            f"(حداقل {MIN_WORDS}، حداکثر {MAX_WORDS})."
        )

    raw = llm_fn(system, user)

    try:
        data = parse_json_object(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("FR-4: unparseable script JSON: {}", exc)
        return ScriptResult(status="needs_review", flags=[f"json-unparseable:{exc}"])

    # Up to MAX_REGEN_PASSES regenerations for an ok script that misses the word
    # band or the FR-17 gate on the script itself (never on a refusal).
    if str(data.get("status") or "") == "ok":
        for pass_no in range(MAX_REGEN_PASSES):
            script = str(data.get("script_farsi") or "")
            words = count_farsi_words(script)
            script_flags = farsi_norm.validate(script)
            if MIN_WORDS <= words <= MAX_WORDS and not script_flags:
                break
            retry_user = user + "\n" + _regen_instruction(words, script_flags)
            try:
                data = parse_json_object(llm_fn(system, retry_user))
                logger.info(
                    "FR-4: attempt {} flagged (words={}, flags={}) — regenerated",
                    pass_no + 1, words, script_flags,
                )
            except (ValueError, json.JSONDecodeError) as exc:
                logger.warning("FR-4: regeneration unparseable ({}); keeping previous attempt", exc)
                break
            if str(data.get("status") or "") != "ok":
                break

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
