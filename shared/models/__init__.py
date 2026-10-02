"""Pydantic models exchanged between pipeline stages."""

from __future__ import annotations

from .behavioral import BehavioralProfile
from .candidate import (
    Candidate, CareerEntry, Certification, CompanySize, Education,
    Language, Profile, RedrobSignals, Skill,
)
from .capability import CapabilityProfile, EvidenceSource, NodeEvidence
from .capability_fit import CapabilityFit
from .honeypot import HoneypotAnalysis
from .jd_profile import (
    AntiSignalRule, AntiSignalVocab, CapabilityRequirement, ExperienceBand,
    JDProfile, LogisticsBuckets,
)
from .ontology import OntologyNode
from .submission import SubmissionRow

__all__ = [
    # input
    "Candidate", "Profile", "CareerEntry", "Education", "Skill",
    "Certification", "Language", "RedrobSignals", "CompanySize",
    # configuration
    "OntologyNode",
    "JDProfile", "CapabilityRequirement", "AntiSignalRule", "AntiSignalVocab",
    "LogisticsBuckets", "ExperienceBand",
    # stage outputs
    "CapabilityProfile", "NodeEvidence", "EvidenceSource",
    "CapabilityFit",
    "BehavioralProfile",
    "HoneypotAnalysis",
    "SubmissionRow",
]
