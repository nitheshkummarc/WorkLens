"""One AI-capability ontology node.

Loaded from data/ai_capability_ontology.json. Module1 uses the importances, module2
matches the phrases. There are 9 nodes (N1-N9); the embedding node N10 is not used.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OntologyNode(BaseModel):
    name: str                                  # e.g. "N1 Retrieval & Search"
    importance: float = Field(ge=0, le=1)      # node-specific weight — the scoring driver
    strong_phrases: tuple[str, ...]            # high-precision domain terms
    weak_phrases: tuple[str, ...]              # ambiguous plain-language terms


__all__ = ["OntologyNode"]
