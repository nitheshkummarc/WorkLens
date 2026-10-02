"""BehavioralProfile, the output of module4."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BehavioralProfile(BaseModel):
    candidate_id: str
    recency: float = Field(ge=0, le=1)
    responsiveness: float = Field(ge=0, le=1)
    open: float = Field(ge=0, le=1)
    interview: float = Field(ge=0, le=1)
    offer: float = Field(ge=0, le=1)
    logistics: float = Field(ge=0, le=1)
    demand: float = Field(ge=0, le=1)
    trust: float = Field(ge=0, le=1)
    behavioral_raw: float = Field(ge=0, le=1)                # weighted sum of the sub-scores
    behavioral_multiplier: float = Field(ge=0, le=1.0)       # see module4_behavioral


__all__ = ["BehavioralProfile"]
