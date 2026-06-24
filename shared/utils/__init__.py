"""Generic, domain-free helpers: phrase matching, text assembly, ontology
loading, date math, and streaming JSONL input.

Each helper operates on arbitrary inputs and embeds no AI/Backend vocabulary —
the vocabulary lives in `data/`.
"""

from __future__ import annotations

from .date_utils import days_between, days_since, parse_date
from .jsonl_reader import CandidateReader
from .ontology_loader import load_ontology
from .phrase_matcher import any_match, first_match, match_phrases
from .text_fields import career_entry_text, claimed_text, demonstrated_text

__all__ = [
    "load_ontology",
    "any_match", "first_match", "match_phrases",
    "demonstrated_text", "claimed_text", "career_entry_text",
    "parse_date", "days_between", "days_since",
    "CandidateReader",
]
