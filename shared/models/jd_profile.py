"""JD rubric — output of module1.

Built from the ontology, the JD rubric data file, and the constants in
shared/config/scoring.py. Consumed by modules 2 and 3.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CapabilityRequirement(BaseModel):
    name: str
    importance: float                                       # node-specific weight (the scoring value)
    tier: Literal["Critical", "High", "Medium", "Nice"]     # DISPLAY-ONLY bucket of importance


class AntiSignalRule(BaseModel):
    key: str                # "research_only" | "consulting_only" | "langchain_only" | ...
    penalty: float          # e.g. 0.25, 0.125, 0.20, 0.15, 0.10
    is_hard_dq: bool        # True ONLY for "research_only"


class ExperienceBand(BaseModel):
    lo: float
    hi: float
    factor: float


class JDProfile(BaseModel):
    role: str                                       # "Senior AI Engineer"
    required_capabilities: list[CapabilityRequirement]   # all 9 nodes w/ importance + tier
    critical_nodes: list[str]
    nice_to_have_nodes: list[str]
    nice_bonus_per_item: float                      # +0.03
    nice_bonus_cap: float                           # +0.10
    anti_signals: list[AntiSignalRule]
    anti_penalty_cap: float                         # 0.50
    hard_dq_base_ceiling: float                     # 0.30
    experience_bands: list[ExperienceBand]
    consulting_companies: tuple[str, ...]           # employers for the consulting soft penalty
    logistics_target_cities: tuple[str, ...]        # cities that count for location fit


__all__ = [
    "CapabilityRequirement", "AntiSignalRule", "ExperienceBand", "JDProfile",
]
