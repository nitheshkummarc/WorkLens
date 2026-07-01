"""Ranking results — output of module6.

RankedCandidate is the thin top-100 record (id, rank, score). The richer
per-candidate payload used for reasoning is carried by module6's RankedEntry.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateScore(BaseModel):
    """Internal per-candidate score record (all candidates)."""

    candidate_id: str
    capability_fit: float
    behavioral_multiplier: float
    is_honeypot: bool
    final_score: float          # 0.0 if honeypot else capability_fit * multiplier


class RankedCandidate(BaseModel):
    """Top-100 ranked record (thin)."""

    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    rank: int = Field(ge=1, le=100)
    score: float                # round(final_score, 6)


__all__ = ["CandidateScore", "RankedCandidate"]
