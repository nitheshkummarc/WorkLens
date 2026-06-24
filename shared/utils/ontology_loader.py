"""Load the AI capability ontology from JSON into typed `OntologyNode`s.

Generic "JSON → dataclass" loader (the WorkLens `signal_loader` pattern, adapted
to carry the `importance` field). The vocabulary itself lives entirely in the
data file; this module embeds no domain terms. Loaded once at startup and passed
as an immutable reference into the per-candidate path (PHASE0 §3c).
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.models.ontology import OntologyNode

EXPECTED_VERSION = "ai-capability-ontology-v1"


def load_ontology(path: Path | str) -> list[OntologyNode]:
    """Parse the ontology JSON and return its nodes in file order (N1..N9)."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    version = raw.get("version")
    if version != EXPECTED_VERSION:
        raise ValueError(
            f"ontology version mismatch: expected {EXPECTED_VERSION!r}, got {version!r}"
        )
    return [
        OntologyNode(
            name=node["name"],
            importance=node["importance"],
            strong_phrases=tuple(node["strong_phrases"]),
            weak_phrases=tuple(node["weak_phrases"]),
        )
        for node in raw["nodes"]
    ]


__all__ = ["load_ontology", "EXPECTED_VERSION"]
