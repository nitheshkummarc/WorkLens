"""Build the two text blobs module2 matches against.

What matters for scoring is *where* the evidence is:

  - demonstrated = current title + all career titles/descriptions. Work someone
    actually did, so it can earn full (1.0) credit.
  - claimed = summary + headline + skill names. Self-asserted, so it's capped at
    half (0.5) unless an assessment backs it up.

Splitting them is what lets "built a recommendation system" score strong while a
stuffed skills list is discounted. This module only builds text; it scores nothing.
"""

from __future__ import annotations

from shared.models.candidate import Candidate, CareerEntry, Skill

_SEP = "\n"


def demonstrated_text(candidate: Candidate) -> str:
    """current_title + all career_history titles and descriptions (demonstrated work)."""
    parts: list[str] = [candidate.profile.current_title]
    for entry in candidate.career_history:
        parts.append(entry.title)
        parts.append(entry.description)
    return _SEP.join(p for p in parts if p)


def claimed_text(candidate: Candidate, kept_skills: list[Skill]) -> str:
    """summary + headline + kept skill names (self-asserted, not demonstrated).

    `kept_skills` is the skill list after dropping assessment-failed skills
    (module2 applies the <30 stuffing gate before calling this).
    """
    parts: list[str] = [candidate.profile.summary, candidate.profile.headline]
    parts.extend(s.name for s in kept_skills)
    return _SEP.join(p for p in parts if p)


def career_entry_text(entry: CareerEntry) -> str:
    """title + description for one role (used to tag ML-relevant roles)."""
    return f"{entry.title}{_SEP}{entry.description}"


__all__ = ["demonstrated_text", "claimed_text", "career_entry_text"]
