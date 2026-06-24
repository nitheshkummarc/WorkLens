"""Assemble candidate text blobs for phrase matching (§2 source separation).

The single most important precision lever in §2 is *where* evidence appears:

  - DEMONSTRATED  = current_title + every career_history title/description.
    Work actually described in employment history → can earn strong (1.0).
  - CLAIMED       = summary + headline + skill names. Self-asserted, not
    demonstrated → capped at weak (0.5) unless an assessment validates it.

Keeping these separate is what lets a plain-language "built a recommendation
system" score strong while a keyword-stuffed skill list is discounted. This
module only *assembles* text; it applies no scoring rules.
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
    """title + description for one role (used for §1.5 per-role ML-relevance)."""
    return f"{entry.title}{_SEP}{entry.description}"


__all__ = ["demonstrated_text", "claimed_text", "career_entry_text"]
