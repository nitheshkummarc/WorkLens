"""Capability fit — output of module3.

The base capability after experience/ML-depth factors, anti-signal penalties, and
the nice-to-have bonus. Consumed by module6 (ranking) and module7 (reasoning).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CapabilityFit(BaseModel):
    candidate_id: str
    base_capability: float                              # carried from module2 (input)
    anti_signals_fired: list[str]                       # keys that fired
    anti_penalty: float = Field(ge=0, le=0.50)
    hard_dq: bool                                       # research_only only
    experience_factor: float = Field(ge=0, le=1)
    ml_depth_factor: float = Field(ge=0.85, le=1.10)
    nice_items: list[str]
    nice_bonus: float = Field(ge=0, le=0.10)
    capability_fit: float = Field(ge=0, le=1)           # clamp(base * E * D - anti + nice)


__all__ = ["CapabilityFit"]
