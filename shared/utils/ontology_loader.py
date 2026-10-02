"""Load the capability ontology JSON into OntologyNode objects."""

from __future__ import annotations

import json
from pathlib import Path

from shared.models.ontology import OntologyNode

EXPECTED_VERSION = "ai-capability-ontology-v1"


def load_ontology(path: Path | str) -> list[OntologyNode]:
    """Return the ontology nodes in file order. Raises ValueError on a version mismatch."""
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
