"""Build the JD rubric — one JDProfile for the whole run.

Combines the ontology importances, the JD selections in data/jd_rubric.json, and
the constants in scoring.py into one JDProfile. Runs once at startup and is reused
for every candidate.

`tier` is a display-only bucket of `importance`; the scoring input is always the
node-specific `importance`, not the tier.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.config import scoring
from shared.models.jd_profile import (
    AntiSignalRule,
    CapabilityRequirement,
    ExperienceBand,
    JDProfile,
)
from shared.models.ontology import OntologyNode


def _tier_for(importance: float) -> str:
    """Coarse display bucket (never the scoring value)."""
    if importance >= 0.9:
        return "Critical"
    if importance >= 0.7:
        return "High"
    if importance >= 0.5:
        return "Medium"
    return "Nice"


def build_jd_profile(nodes: list[OntologyNode], rubric_path: Path | str) -> JDProfile:
    """Assemble the `JDProfile` from ontology nodes + the JD rubric data file."""
    rubric = json.loads(Path(rubric_path).read_text(encoding="utf-8"))

    node_names = {n.name for n in nodes}
    unknown = [name for name in rubric["nice_to_have_nodes"] if name not in node_names]
    if unknown:
        raise ValueError(f"jd_rubric nice_to_have_nodes not in ontology: {unknown}")

    required = [
        CapabilityRequirement(name=n.name, importance=n.importance, tier=_tier_for(n.importance))
        for n in nodes
    ]
    critical = [n.name for n in nodes if n.importance >= 0.9]

    anti_signals = []
    for key in rubric["anti_signals"]:
        penalty, is_hard_dq = scoring.ANTI_SIGNAL_PENALTIES[key]
        anti_signals.append(AntiSignalRule(key=key, penalty=penalty, is_hard_dq=is_hard_dq))

    bands = [ExperienceBand(lo=lo, hi=hi, factor=f) for lo, hi, f in scoring.EXPERIENCE_BANDS]

    return JDProfile(
        role=rubric["role"],
        required_capabilities=required,
        critical_nodes=critical,
        nice_to_have_nodes=list(rubric["nice_to_have_nodes"]),
        nice_bonus_per_item=scoring.NICE_BONUS_PER_ITEM,
        nice_bonus_cap=scoring.NICE_BONUS_CAP,
        anti_signals=anti_signals,
        anti_penalty_cap=scoring.ANTI_PENALTY_CAP,
        hard_dq_base_ceiling=scoring.HARD_DQ_BASE_CEILING,
        experience_bands=bands,
        consulting_companies=tuple(rubric["consulting_companies"]),
        logistics_target_cities=tuple(rubric["logistics_target_cities"]),
    )


__all__ = ["build_jd_profile"]
