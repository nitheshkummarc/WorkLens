"""JDProfile, the output of module1."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CapabilityRequirement(BaseModel):
    name: str
    importance: float


class AntiSignalRule(BaseModel):
    key: str
    penalty: float
    is_hard_dq: bool


class AntiSignalVocab(BaseModel):
    """Lower-cased detection terms for the anti-signal rules."""

    model_config = ConfigDict(frozen=True)

    research_terms: tuple[str, ...]
    production_terms: tuple[str, ...]
    llm_wrapper_terms: tuple[str, ...]
    pre_llm_ml_terms: tuple[str, ...]
    retrieval_nodes: tuple[str, ...]       # career evidence here rules out langchain_only
    tutorial_terms: tuple[str, ...]
    senior_titles: tuple[str, ...]
    cv_domain_terms: tuple[str, ...]
    ir_nlp_nodes: tuple[str, ...]          # ontology nodes that rule out cv_speech_robotics


class LogisticsBuckets(BaseModel):
    """Lower-cased location and work-mode settings used by the logistics factor."""

    model_config = ConfigDict(frozen=True)

    home_country: str
    office: tuple[str, ...]
    welcome: tuple[str, ...]
    preferred_work_modes: tuple[str, ...]


class ExperienceBand(BaseModel):
    lo: float
    hi: float
    factor: float


class JDProfile(BaseModel):
    role: str
    required_capabilities: list[CapabilityRequirement]   # every ontology node
    critical_nodes: list[str]
    nice_to_have_nodes: list[str]
    ml_nodes: list[str]                                  # nodes that make a role ML-relevant
    nice_bonus_per_item: float
    nice_bonus_cap: float
    anti_signals: list[AntiSignalRule]
    anti_signal_vocab: AntiSignalVocab
    anti_signal_concerns: dict[str, str]                # reasoning text per anti-signal
    anti_penalty_cap: float
    hard_dq_base_ceiling: float
    experience_bands: list[ExperienceBand]
    consulting_companies: tuple[str, ...]               # lower-cased
    logistics: LogisticsBuckets


__all__ = [
    "CapabilityRequirement", "AntiSignalRule", "AntiSignalVocab",
    "LogisticsBuckets", "ExperienceBand", "JDProfile",
]
