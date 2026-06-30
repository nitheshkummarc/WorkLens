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
PhraseSpec = tuple[str, str, bool]


def _pattern_source(phrase: str) -> str:
    """Return the regex source that implements the phrase's legacy match rule."""
    stem = phrase.endswith("*")
    core = phrase[:-1] if stem else phrase
    escaped = re.escape(core)
    if not stem and len(core) <= scoring.SHORT_TERM_MAX_LEN:
        return rf"\b{escaped}\b"
    return escaped


@lru_cache(maxsize=8192)
def _compile(phrase: str) -> re.Pattern[str]:
    """Compile a case-insensitive pattern for one phrase (cached)."""
    return re.compile(_pattern_source(phrase), re.IGNORECASE)


class PhraseGroup:
    """Fast exact-preserving matcher for a fixed phrase tuple.

    The group keeps phrase-order semantics but avoids regex in the hot path.
    Short-term word-boundary behavior mirrors the legacy regex matcher.
    """

    def __init__(self, phrases: tuple[str, ...]) -> None:
        self.phrases = phrases
        self._specs: tuple[PhraseSpec, ...] = tuple(
            self._make_spec(phrase)
            for phrase in phrases
        )

    def first_match(self, text: str) -> str | None:
        """Return the same phrase as legacy `first_match`, with fewer full scans."""
        lowered = text.lower()
        for phrase, core, bounded in self._specs:
            if self._contains(lowered, core, bounded):
                return phrase
        return None

    def any_match(self, text: str) -> bool:
        """True if any phrase occurs in `text`."""
        lowered = text.lower()
        return any(self._contains(lowered, core, bounded) for _, core, bounded in self._specs)

    @staticmethod
    def _make_spec(phrase: str) -> PhraseSpec:
        stem = phrase.endswith("*")
        core = phrase[:-1] if stem else phrase
        bounded = not stem and len(core) <= scoring.SHORT_TERM_MAX_LEN
        return phrase, core.lower(), bounded

    @staticmethod
    def _is_word_char(char: str) -> bool:
        return char == "_" or char.isalnum()

    @classmethod
    def _contains(cls, text: str, core: str, bounded: bool) -> bool:
        if not core:
            return True
        start = text.find(core)
        if not bounded:
            return start != -1
        while start != -1:
            end = start + len(core)
            before_ok = start == 0 or not cls._is_word_char(text[start - 1])
            after_ok = end == len(text) or not cls._is_word_char(text[end])
            if before_ok and after_ok:
                return True
            start = text.find(core, start + 1)
        return False


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


__all__ = ["Span", "PhraseSpec", "PhraseGroup", "first_match", "any_match", "match_phrases"]
