"""Match ontology phrases inside a piece of text.

Single responsibility: locate where phrases occur. Generic — it knows nothing
about the AI ontology; it operates on arbitrary phrase tuples. Adapted from the
WorkLens matcher (the same word-boundary/substring logic), plus stem handling:

  - Short terms (≤ SHORT_TERM_MAX_LEN chars) match on word boundaries, so "rag"
    never matches inside "storage" and "map" never matches inside "roadmap".
  - Longer terms match as substrings, so multi-word phrases and stems survive
    suffixes and joined text.
  - A trailing "*" marks an explicit stem ("tokeniz*" → matches "tokenizer",
    "tokenization") and always matches as a substring.

Patterns are compiled once and cached, so reuse across 100K candidates costs no
recompilation (the per-candidate performance contract, PHASE0 §3c).
"""

from __future__ import annotations

import re
from functools import lru_cache

from shared.config import scoring

Span = tuple[int, int]


@lru_cache(maxsize=8192)
def _compile(phrase: str) -> re.Pattern[str]:
    """Compile a case-insensitive pattern for one phrase (cached)."""
    stem = phrase.endswith("*")
    core = phrase[:-1] if stem else phrase
    escaped = re.escape(core)
    if not stem and len(core) <= scoring.SHORT_TERM_MAX_LEN:
        pattern = rf"\b{escaped}\b"
    else:
        pattern = escaped
    return re.compile(pattern, re.IGNORECASE)


def first_match(text: str, phrases: tuple[str, ...]) -> str | None:
    """Return the first phrase (in list order) that occurs in `text`, else None.

    Cheaper than `match_phrases` when the caller only needs presence + one
    example phrase (the common case in module2 node scoring).
    """
    for phrase in phrases:
        if _compile(phrase).search(text):
            return phrase
    return None


def any_match(text: str, phrases: tuple[str, ...]) -> bool:
    """True if any phrase occurs in `text`."""
    return first_match(text, phrases) is not None


def match_phrases(text: str, phrases: tuple[str, ...]) -> dict[str, list[Span]]:
    """Find every phrase that occurs in `text`, with its match spans."""
    found: dict[str, list[Span]] = {}
    for phrase in phrases:
        spans = [(m.start(), m.end()) for m in _compile(phrase).finditer(text)]
        if spans:
            found[phrase] = spans
    return found


__all__ = ["Span", "first_match", "any_match", "match_phrases"]
