"""Build the JDProfile from the ontology, data/jd_rubric.json and scoring.py.

Vocabulary is lower-cased here once.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.config import scoring
from shared.models.jd_profile import (
    AntiSignalRule,
    AntiSignalVocab,
    CapabilityRequirement,
    ExperienceBand,
    JDProfile,
    LogisticsBuckets,
)
from shared.models.ontology import OntologyNode


def _lower(values: list[str]) -> tuple[str, ...]:
    return tuple(v.lower() for v in values)


def _check_nodes(names: list[str], known: set[str], field: str) -> None:
    unknown = [n for n in names if n not in known]
    if unknown:
        raise ValueError(f"jd_rubric {field} not in ontology: {unknown}")


def _build_vocab(raw: dict, node_names: set[str]) -> AntiSignalVocab:
    research = raw["research_only"]
    langchain = raw["langchain_only"]
    cv = raw["cv_speech_robotics"]
    _check_nodes(cv["ir_nlp_nodes"], node_names, "cv_speech_robotics.ir_nlp_nodes")
    _check_nodes(langchain["retrieval_nodes"], node_names, "langchain_only.retrieval_nodes")
    return AntiSignalVocab(
        research_terms=_lower(research["research_terms"]),
        production_terms=_lower(research["production_terms"]),
        llm_wrapper_terms=_lower(langchain["llm_wrapper_terms"]),
        pre_llm_ml_terms=_lower(langchain["pre_llm_ml_terms"]),
        retrieval_nodes=tuple(langchain["retrieval_nodes"]),
        tutorial_terms=_lower(raw["framework_tutorial"]["tutorial_terms"]),
        senior_titles=_lower(raw["no_recent_handson"]["senior_titles"]),
        cv_domain_terms=_lower(cv["domain_terms"]),
        ir_nlp_nodes=tuple(cv["ir_nlp_nodes"]),
    )


def build_jd_profile(nodes: list[OntologyNode], rubric_path: Path | str) -> JDProfile:
    """Raises ValueError if the rubric is incomplete or inconsistent."""
    rubric = json.loads(Path(rubric_path).read_text(encoding="utf-8"))
    node_names = {n.name for n in nodes}

    try:
        _check_nodes(rubric["nice_to_have_nodes"], node_names, "nice_to_have_nodes")
        _check_nodes(rubric["ml_nodes"], node_names, "ml_nodes")

        unknown_keys = [k for k in rubric["anti_signals"] if k not in scoring.ANTI_SIGNAL_PENALTIES]
        if unknown_keys:
            raise ValueError(f"jd_rubric anti_signals have no penalty in scoring.py: {unknown_keys}")
        anti_signals = []
        for key in rubric["anti_signals"]:
            penalty, is_hard_dq = scoring.ANTI_SIGNAL_PENALTIES[key]
            anti_signals.append(AntiSignalRule(key=key, penalty=penalty, is_hard_dq=is_hard_dq))

        vocab = _build_vocab(rubric["anti_signal_vocab"], node_names)
        concerns = dict(rubric["anti_signal_concerns"])
        missing = [k for k in rubric["anti_signals"] if k not in concerns]
        if missing:
            raise ValueError(f"jd_rubric anti_signal_concerns missing text for: {missing}")
        loc = rubric["logistics"]
        logistics = LogisticsBuckets(
            home_country=loc["home_country"].lower(),
            office=_lower(loc["office"]),
            welcome=_lower(loc["welcome"]),
            preferred_work_modes=_lower(loc["preferred_work_modes"]),
        )
        role = rubric["role"]
        consulting = _lower(rubric["consulting_companies"])
        nice_nodes = list(rubric["nice_to_have_nodes"])
        ml_nodes = list(rubric["ml_nodes"])
    except KeyError as exc:
        raise ValueError(f"jd_rubric is missing key {exc}") from exc

    return JDProfile(
        role=role,
        required_capabilities=[
            CapabilityRequirement(name=n.name, importance=n.importance) for n in nodes
        ],
        critical_nodes=[n.name for n in nodes if n.importance >= scoring.CRITICAL_IMPORTANCE_MIN],
        nice_to_have_nodes=nice_nodes,
        ml_nodes=ml_nodes,
        nice_bonus_per_item=scoring.NICE_BONUS_PER_ITEM,
        nice_bonus_cap=scoring.NICE_BONUS_CAP,
        anti_signals=anti_signals,
        anti_signal_vocab=vocab,
        anti_signal_concerns=concerns,
        anti_penalty_cap=scoring.ANTI_PENALTY_CAP,
        hard_dq_base_ceiling=scoring.HARD_DQ_BASE_CEILING,
        experience_bands=[
            ExperienceBand(lo=lo, hi=hi, factor=f) for lo, hi, f in scoring.EXPERIENCE_BANDS
        ],
        consulting_companies=consulting,
        logistics=logistics,
    )


__all__ = ["build_jd_profile"]
