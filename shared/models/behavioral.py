"""Behavioral profile — output of module4.

The 8 sub-scores, behavioral_raw, and behavioral_multiplier. Consumed by module6
(ranking) and module7 (reasoning). Recency is measured against the AS_OF date, not
the wall clock, so runs are reproducible.
"""

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
    behavioral_raw: float = Field(ge=0, le=1)
    behavioral_multiplier: float = Field(ge=0.50, le=1.0)


__all__ = ["BehavioralProfile"]
