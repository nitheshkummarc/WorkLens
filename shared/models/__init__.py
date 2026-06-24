"""Pydantic schemas for WorkLens-RedRob (interface_contract.md).

Only the models needed by the capability-extraction path (input candidate,
ontology, JD rubric, capability profile) are present so far; behavioral,
honeypot, ranking and submission models are added as their modules land.
"""

from __future__ import annotations

from .candidate import (
    Candidate, CareerEntry, Certification, CompanySize, Education,
    Language, Profile, RedrobSignals, Skill,
)
from .capability import CapabilityProfile, NodeEvidence
from .jd_profile import (
    AntiSignalRule, CapabilityRequirement, ExperienceBand, JDProfile,
)
from .ontology import OntologyNode

__all__ = [
    # candidate
    "Candidate", "Profile", "CareerEntry", "Education", "Skill",
    "Certification", "Language", "RedrobSignals", "CompanySize",
    # ontology
    "OntologyNode",
    # jd profile
    "JDProfile", "CapabilityRequirement", "AntiSignalRule", "ExperienceBand",
    # capability
    "CapabilityProfile", "NodeEvidence",
]
