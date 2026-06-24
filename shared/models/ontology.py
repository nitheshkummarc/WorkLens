"""AI capability ontology node model (§2 data).

Loaded from `data/ai_capability_ontology.json` by `shared/utils/ontology_loader`.
Consumed by module1 (importances → JD rubric) and module2 (phrase matching →
node strengths). The 9 nodes (N1–N9) and their importances/phrases are frozen
per `REDROB_SCORING_DESIGN.md` §2. N10 (embeddings) is NOT present in v1.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OntologyNode(BaseModel):
    name: str                                  # e.g. "N1 Retrieval & Search"
    importance: float = Field(ge=0, le=1)      # node-specific weight — the scoring driver
    strong_phrases: tuple[str, ...]            # high-precision domain terms
    weak_phrases: tuple[str, ...]              # ambiguous plain-language terms


__all__ = ["OntologyNode"]
