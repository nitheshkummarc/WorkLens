"""Pydantic schemas for WorkLens-RedRob (interface_contract.md).

Covers the capability + behavioral + honeypot scoring path (candidate input,
ontology, JD rubric, capability profile, capability fit, behavioral profile,
honeypot analysis). Ranking and submission models are added as their modules land.
"""

from __future__ import annotations

from .behavioral import BehavioralProfile
from .candidate import (
    Candidate, CareerEntry, Certification, CompanySize, Education,
    Language, Profile, RedrobSignals, Skill,
)
from .capability import CapabilityProfile, NodeEvidence
from .capability_fit import CapabilityFit
from .honeypot import HoneypotAnalysis
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
    # capability fit (module3)
    "CapabilityFit",
    # behavioral (module4)
    "BehavioralProfile",
    # honeypot (module5)
    "HoneypotAnalysis",
]
