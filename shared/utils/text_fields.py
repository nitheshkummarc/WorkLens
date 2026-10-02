"""Which profile fields count as demonstrated and which as self-reported.

demonstrated: current title and all career titles and descriptions.
claimed: summary, headline and skill names (self-reported).

The *_parts functions are the single definition; module2 matches the parts
separately (cached per part), module3 matches the joined text.
"""

from __future__ import annotations

from collections.abc import Iterable

from shared.models.candidate import Candidate, Skill

_SEP = "\n"


def demonstrated_parts(candidate: Candidate) -> list[str]:
    """Current title plus every career title and description."""
    parts = [candidate.profile.current_title]
    for entry in candidate.career_history:
        parts.append(entry.title)
        parts.append(entry.description)
    return parts


def claimed_parts(candidate: Candidate, skills: Iterable[Skill]) -> list[str]:
    """Summary, headline and the names of `skills`."""
    return [candidate.profile.summary, candidate.profile.headline] + [s.name for s in skills]


def demonstrated_text(candidate: Candidate) -> str:
    return _SEP.join(p for p in demonstrated_parts(candidate) if p)


def claimed_text(candidate: Candidate, skills: Iterable[Skill]) -> str:
    return _SEP.join(p for p in claimed_parts(candidate, skills) if p)


__all__ = ["demonstrated_parts", "claimed_parts", "demonstrated_text", "claimed_text"]
