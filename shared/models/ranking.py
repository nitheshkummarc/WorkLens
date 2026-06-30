"""Ranking result models (§0 final + §5) — output of module6_ranking.

Sole owner of `final_score` and `rank`. `RankedCandidate` is the thin top-100
projection; the rich per-candidate payload needed for reasoning is carried by
module6's internal `RankedEntry`. Mirrors interface_contract.md §8.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateScore(BaseModel):
    """Internal per-candidate score record (all candidates)."""

    candidate_id: str
    capability_fit: float
    behavioral_multiplier: float
    is_honeypot: bool
    final_score: float          # 0.0 if honeypot else capability_fit · multiplier


class RankedCandidate(BaseModel):
    """Top-100 ranked record (thin)."""

    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    rank: int = Field(ge=1, le=100)
    score: float                # round(final_score, 6)


__all__ = ["CandidateScore", "RankedCandidate"]
