"""Generic helpers: phrase matching, text assembly, ontology loading, dates,
numeric helpers and JSONL input."""

from __future__ import annotations

from .date_utils import days_between, days_since, parse_date
from .jsonl_reader import CandidateReader
from .numeric import clamp01
from .ontology_loader import load_ontology
from .phrase_matcher import PhraseGroup
from .text_fields import career_entry_text, claimed_text, demonstrated_text

__all__ = [
    "load_ontology",
    "PhraseGroup",
    "demonstrated_text", "claimed_text", "career_entry_text",
    "parse_date", "days_between", "days_since",
    "clamp01",
    "CandidateReader",
]
