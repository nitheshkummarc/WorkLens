"""CapabilityProfile, the output of module2."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Where a node's strength came from:
#   career          strong phrase in career history (strength 1.0)
#   skill_verified  advanced/expert skill with assessment >= 50 (strength 1.0)
#   claimed         strong phrase only in summary, headline or skills (strength 0.5)
#   career_weak     only a generic phrase in career history (strength 0.5)
#   none            no evidence (strength 0.0)
EvidenceSource = Literal["career", "skill_verified", "claimed", "career_weak", "none"]


class NodeEvidence(BaseModel):
    node: str
    strength: Literal[0.0, 0.5, 1.0]
    source: EvidenceSource
    evidence_phrase: Optional[str] = None   # matched phrase or skill name


class CapabilityProfile(BaseModel):
    candidate_id: str
    node_strengths: list[NodeEvidence]              # one entry per ontology node
    base_capability: float = Field(ge=0, le=1)      # importance-weighted mean of strengths
    ml_relevant_months: int = Field(ge=0)           # months in ML-relevant roles (N1-N7)


__all__ = ["EvidenceSource", "NodeEvidence", "CapabilityProfile"]
