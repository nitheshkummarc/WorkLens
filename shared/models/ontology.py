"""A single node of the capability ontology (data/ai_capability_ontology.json)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OntologyNode(BaseModel):
    name: str                                  # e.g. "N1 Retrieval & Search"
    importance: float = Field(ge=0, le=1)      # weight in base_capability
    strong_phrases: tuple[str, ...]            # specific technical terms
    weak_phrases: tuple[str, ...]              # generic terms


__all__ = ["OntologyNode"]
