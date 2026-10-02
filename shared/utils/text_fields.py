"""Text assembly for capability matching.

demonstrated: current title and all career titles and descriptions.
claimed: summary, headline and skill names (self-reported).
"""

from __future__ import annotations

from collections.abc import Iterable

from shared.models.candidate import Candidate, CareerEntry, Skill

_SEP = "\n"


def demonstrated_text(candidate: Candidate) -> str:
    """Current title plus all career titles and descriptions."""
    parts: list[str] = [candidate.profile.current_title]
    for entry in candidate.career_history:
        parts.append(entry.title)
        parts.append(entry.description)
    return _SEP.join(p for p in parts if p)


def claimed_text(candidate: Candidate, skills: Iterable[Skill]) -> str:
    """Summary, headline and the names of `skills`."""
    parts: list[str] = [candidate.profile.summary, candidate.profile.headline]
    parts.extend(s.name for s in skills)
    return _SEP.join(p for p in parts if p)


def career_entry_text(entry: CareerEntry) -> str:
    """Title and description of one role."""
    return f"{entry.title}{_SEP}{entry.description}"


__all__ = ["demonstrated_text", "claimed_text", "career_entry_text"]
