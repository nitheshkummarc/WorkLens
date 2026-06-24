"""JD profile model (§1 rubric) — output of module1_jd_rubric.

Built from `data/ai_capability_ontology.json` + `data/jd_rubric.json` and the
numeric constants in `shared/config/scoring.py`. Consumed by modules 2 and 3.
Mirrors interface_contract.md §3.
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
    nice_to_have_nodes: list[str]                   # §1.2
    nice_bonus_per_item: float                      # +0.03
    nice_bonus_cap: float                           # +0.10
    anti_signals: list[AntiSignalRule]              # §1.3
    anti_penalty_cap: float                         # 0.50
    hard_dq_base_ceiling: float                     # 0.30
    experience_bands: list[ExperienceBand]          # §1.4
    consulting_companies: tuple[str, ...]           # consulting soft-penalty employer list
    logistics_target_cities: tuple[str, ...]        # §3.2 location_factor


__all__ = [
    "CapabilityRequirement", "AntiSignalRule", "ExperienceBand", "JDProfile",
]
