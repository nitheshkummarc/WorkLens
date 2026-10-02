"""CapabilityFit, the output of module3."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CapabilityFit(BaseModel):
    candidate_id: str
    base_capability: float                              # from module2
    anti_signals_fired: list[str]
    anti_penalty: float = Field(ge=0, le=0.50)
    hard_dq: bool
    experience_factor: float = Field(ge=0, le=1)
    ml_depth_factor: float = Field(ge=0.85, le=1.10)
    nice_items: list[str]
    nice_bonus: float = Field(ge=0, le=0.10)
    capability_fit: float = Field(ge=0, le=1)


__all__ = ["CapabilityFit"]
