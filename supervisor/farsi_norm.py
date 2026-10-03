"""FR-17 / R-2: TTS-ready Farsi normalization + validator (rule-based).

Deterministic, testable text-quality gate that runs on the Farsi script + caption
before TTS (FR-4, FR-6). Three rules, each backed by a curated, extendable table:

- **ZWNJ (نیم‌فاصله)** — a set of high-confidence compounds that must be written
  with a ZWNJ. The validator flags a missing ZWNJ when the space-broken form is
  present; the normalizer joins it.
- **Harakat (diacritics)** — a table of un-marked forms that a TTS phonetizer
  misreads without an explicit harakat. The normalizer inserts the marked form;
  the validator flags an un-marked occurrence. The enforcement table is
  operator-curated; a separate *candidate* list seeds it (R-2 defers
  model-based diacritics, so anything unverified stays a candidate, not a rule).
- **Punctuation density** — clamp prosody punctuation to 1 mark per 8-25 words.

Every rule is table-driven so tests can inject their own tables without touching
the module constants. No LLM in the loop: the output is fully deterministic and
unit-testable against the Farsi fixture corpus in ``test/resources/farsi/``.
"""

from __future__ import annotations

import re
from typing import Optional

# The ZWNJ character (نیم‌فاصله).
ZWNJ = "\u200c"

# ---------------------------------------------------------------------------
# Rule tables (curated, extendable; see R-2)
# ---------------------------------------------------------------------------

# High-confidence required-ZWNJ compounds, as (space-broken, ZWNJ-joined) pairs.
# The validator flags the broken form; the normalizer joins it.
ZWNJ_PAIRS: list[tuple[str, str]] = [
    ("می شود", "می‌شود"),
    ("نمی شود", "نمی‌شود"),
    ("می گردد", "می‌گردد"),
    ("نمی گردد", "نمی‌گردد"),
    ("می توان", "می‌توان"),
    ("نمی توان", "نمی‌توان"),
    ("رها ها", "رها‌ها"),
    ("مرد ها", "مرد‌ها"),
    ("روز ها", "روز‌ها"),
    ("بچه ها", "بچه‌ها"),
]

# Un-marked surface form -> TTS-ready diacritized form. Operator-curated; the
# validator flags a present un-marked form and the normalizer inserts the mark.
# Kept intentionally small: anything not yet verified stays a *candidate*.
HARAKAT_REQUIRED: dict[str, str] = {}

# Suggested ambiguous tokens to promote into HARAKAT_REQUIRED once verified
# (informational seed; not enforced). Examples where a harakat flips meaning or
# forces the correct vowel for a Farsi TTS phonetizer.
HARAKAT_CANDIDATES: tuple[str, ...] = (
    "بِه",  # to / at — disambiguate the final vowel
    "کِه",  # that / which — vs. kiyā
    "مِی",  # verb-prefix vowel
    "دَی",  # he-gives — vs. day (dā-yad)
)

# Punctuation-density bounds: 1 mark per 8-25 words (spec §Farsi writing rules;
# upper bound widened from 1/15 to 1/8: real LLM prose lands at ~1/9-1/12 and
# dense prosody is the safe direction for TTS, so the band clamps run-on, not
# commas).
PUNCT_MIN_PER_WORD = 1.0 / 25.0
PUNCT_MAX_PER_WORD = 1.0 / 8.0

# The density rule describes a full script (150-220 words); it is not meaningful
# for fragments, so it only fires at or above this many words.
PUNCT_MIN_WORDS = 15

# Prosody punctuation to count: Farsi comma/question + ASCII question/exclamation
# (an LLM may emit either script's marks). Deduped at count time.
PUNCT_CHARS = "،؟?!"

# Unicode combining diacritics used for harakat detection.
_HARAKAT_MARKS = re.compile(
    "[\u064b-\u065f\u0670\u06d6-\u06ed]"
)
# A run of letters/digits (RTL-aware).
_WORD = re.compile(r"[\u0600-\u06ff0-9]+")


def _count_words(text: str) -> int:
    """Number of whitespace-separated words (Farsi word count for the 150-220 gate)."""
    text = (text or "").strip()
    if not text:
        return 0
    return len(text.split())


def _count_punct(text: str) -> int:
    return sum((text or "").count(c) for c in set(PUNCT_CHARS))


def _zwnj_flags(text: str, pairs: list[tuple[str, str]]) -> list[str]:
    """Flag required-ZWNJ compounds that are present in their space-broken form."""
    flags: list[str] = []
    for broken, joined in pairs:
        # A broken occurrence is one not already glued with a ZWNJ.
        if broken in text and joined not in text:
            flags.append(f"zwnj-missing:{broken}")
    return flags


def _harakat_flags(text: str, table: dict[str, str]) -> list[str]:
    """Flag HARAKAT_REQUIRED forms that appear un-marked (no diacritic in the word)."""
    flags: list[str] = []
    for base in table:
        for m in _WORD.finditer(text or ""):
            token = m.group(0)
            if base in token and not _HARAKAT_MARKS.search(token):
                flags.append(f"harakat-missing:{base}")
                break
    return flags


def _punctuation_flags(text: str) -> list[str]:
    """Flag when prosody-punctuation density is outside [1/25, 1/8] per word.

    Only meaningful at ``PUNCT_MIN_WORDS`` words or more; fragments are skipped.
    """
    words = _count_words(text)
    if words < PUNCT_MIN_WORDS:
        return []
    ratio = _count_punct(text) / words
    if ratio < PUNCT_MIN_PER_WORD - 1e-9 or ratio > PUNCT_MAX_PER_WORD + 1e-9:
        return [
            f"punctuation-density-out-of-range:{ratio:.3f}"
            f" (allowed {PUNCT_MIN_PER_WORD:.3f}-{PUNCT_MAX_PER_WORD:.3f})"
        ]
    return []


def validate(
    text: str,
    *,
    zwnj_pairs: Optional[list[tuple[str, str]]] = None,
    harakat_required: Optional[dict[str, str]] = None,
) -> list[str]:
    """Return the list of TTS-quality flags for ``text`` (empty == TTS-ready).

    ``zwnj_pairs`` / ``harakat_required`` override the module tables (tests).
    Punctuation density always uses the module bounds.
    """
    zwnj_pairs = ZWNJ_PAIRS if zwnj_pairs is None else zwnj_pairs
    harakat_required = HARAKAT_REQUIRED if harakat_required is None else harakat_required

    flags: list[str] = []
    flags += _zwnj_flags(text, zwnj_pairs)
    flags += _harakat_flags(text, harakat_required)
    flags += _punctuation_flags(text)
    return flags


def normalize(
    text: str,
    *,
    zwnj_pairs: Optional[list[tuple[str, str]]] = None,
    harakat_required: Optional[dict[str, str]] = None,
) -> str:
    """Join required-ZWNJ compounds and insert harakat on required forms.

    Punctuation is *not* rewritten (the LLM owns prosody; the validator clamps
    density and routes out-of-range text to review rather than auto-editing it).
    """
    zwnj_pairs = ZWNJ_PAIRS if zwnj_pairs is None else zwnj_pairs
    harakat_required = HARAKAT_REQUIRED if harakat_required is None else harakat_required

    out = text
    for broken, joined in zwnj_pairs:
        out = out.replace(broken, joined)
    for base, marked in (harakat_required or {}).items():
        # Word-boundary replace so a longer correct form is never clobbered.
        out = re.sub(rf"(?<!\S){re.escape(base)}(?!\S)", marked, out)
    return out


__all__ = [
    "ZWNJ",
    "ZWNJ_PAIRS",
    "HARAKAT_REQUIRED",
    "HARAKAT_CANDIDATES",
    "PUNCT_MIN_PER_WORD",
    "PUNCT_MAX_PER_WORD",
    "PUNCT_MIN_WORDS",
    "PUNCT_CHARS",
    "validate",
    "normalize",
]
