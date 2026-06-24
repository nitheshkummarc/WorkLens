"""Generic, domain-free helpers: phrase matching, text assembly, ontology loading.

Each helper operates on arbitrary inputs and embeds no AI/Backend vocabulary —
the vocabulary lives in `data/`. (Streaming `jsonl_reader` and `date_utils` are
added alongside the modules that need them.)
"""

from __future__ import annotations

from .ontology_loader import load_ontology
from .phrase_matcher import any_match, first_match, match_phrases
from .text_fields import career_entry_text, claimed_text, demonstrated_text

__all__ = [
    "load_ontology",
    "any_match", "first_match", "match_phrases",
    "demonstrated_text", "claimed_text", "career_entry_text",
]
