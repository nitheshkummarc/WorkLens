"""Capability profile model (§2) — output of module2_capability.

Owns `node_strengths`, `base_capability`, and `ml_relevant_months`. Consumed by
module3 (fit) and module7 (reasoning). Mirrors interface_contract.md §4.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class NodeEvidence(BaseModel):
    node: str
    strength: Literal[0.0, 0.5, 1.0]
    source: Literal["career_description", "skill_verified", "skill_unverified", "none"]
    evidence_phrase: Optional[str] = None   # matched phrase / skill name (for reasoning)


class CapabilityProfile(BaseModel):
    candidate_id: str
    node_strengths: list[NodeEvidence]              # one per ontology node (all 9 present)
    base_capability: float = Field(ge=0, le=1)      # Σ(importance·strength)/Σ importance
    ml_relevant_months: int = Field(ge=0)           # §1.5 — Σ duration_months of N1–N7 roles


__all__ = ["NodeEvidence", "CapabilityProfile"]
