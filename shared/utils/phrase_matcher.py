"""Phrase matching on lower-cased text.

Rules:
  - A match must start at a word boundary ("search" does not match "research").
  - Phrases of up to SHORT_TERM_MAX_LEN characters must also end at one
    ("rag" does not match "ragged").
  - Longer phrases may run into a longer word ("pipeline" matches "pipelines").
  - A trailing "*" marks a stem ("tokeniz*").
  - A match preceded, within NEGATION_WINDOW_WORDS words of the same clause,
    by a word in NEGATION_CUES is ignored ("lighter weight than ranking
    systems", "not in production").

PhraseGroup expects text that is already lower-cased. PhraseIndex lower-cases
and caches per text.
"""

from __future__ import annotations

import re
from functools import lru_cache

from shared.config import scoring

PhraseSpec = tuple[str, str, bool]   # (original phrase, lower-cased core, needs word end)

_CLAUSE_BREAKS = ".;:!?\n"
_WORD = re.compile(r"[a-z0-9_]+")
_LOOKBACK_CHARS = 80


def _negated(text: str, start: int) -> bool:
    """True if a negation or comparison cue precedes `start` in the same clause."""
    window = text[max(0, start - _LOOKBACK_CHARS):start]
    cut = max(window.rfind(c) for c in _CLAUSE_BREAKS)
    if cut >= 0:
        window = window[cut + 1:]
    words = _WORD.findall(window)[-scoring.NEGATION_WINDOW_WORDS:]
    return any(w in scoring.NEGATION_CUES for w in words)


class PhraseGroup:
    """Matcher for a fixed, ordered tuple of phrases."""

    def __init__(self, phrases: tuple[str, ...]) -> None:
        self.phrases = phrases
        self._specs: tuple[PhraseSpec, ...] = tuple(self._make_spec(p) for p in phrases)

    def any_match(self, lowered: str) -> bool:
        """True if any phrase occurs in `lowered`."""
        contains = self._contains
        for _, core, bounded in self._specs:
            if core in lowered and contains(lowered, core, bounded):
                return True
        return False

    def all_matches(self, lowered: str) -> frozenset[str]:
        """Every phrase found in `lowered`."""
        contains = self._contains
        return frozenset(
            phrase for phrase, core, bounded in self._specs
            if core in lowered and contains(lowered, core, bounded)
        )

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
        while start != -1:
            end = start + len(core)
            before_ok = start == 0 or not cls._is_word_char(text[start - 1])
            after_ok = not bounded or end == len(text) or not cls._is_word_char(text[end])
            if before_ok and after_ok and not _negated(text, start):
                return True
            start = text.find(core, start + 1)
        return False


class PhraseIndex:
    """Phrases of a fixed vocabulary found in a text, cached per distinct text.

    Phrases never span a newline and the negation window stops at one, so the
    matches in newline-joined parts equal the union of the matches in each
    part. Callers match parts separately and union the results; repeated parts
    are served from the cache.
    """

    def __init__(self, phrases: tuple[str, ...], cache_size: int = 65_536) -> None:
        if any("\n" in p for p in phrases):
            raise ValueError("phrases must not contain newlines")
        self._group = PhraseGroup(tuple(dict.fromkeys(phrases)))
        self.matches = lru_cache(maxsize=cache_size)(self._matches)

    def _matches(self, text: str) -> frozenset[str]:
        return self._group.all_matches(text.lower())

    def matches_any_part(self, parts) -> frozenset[str]:
        """Union of the matches in each part."""
        found: frozenset[str] = frozenset()
        for part in parts:
            if part:
                found = found | self.matches(part)
        return found


__all__ = ["PhraseGroup", "PhraseIndex"]
