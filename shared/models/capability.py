"""Capability profile — output of module2.

Holds the per-node strengths, the importance-weighted base_capability, and the
relevant-ML tenure. Consumed by module3 and module7.
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
    base_capability: float = Field(ge=0, le=1)      # importance-weighted mean of strengths
    ml_relevant_months: int = Field(ge=0)           # months in ML-relevant roles (nodes N1-N7)


__all__ = ["NodeEvidence", "CapabilityProfile"]
