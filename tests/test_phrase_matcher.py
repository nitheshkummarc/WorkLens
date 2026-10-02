"""PhraseGroup and PhraseIndex matching rules."""

from __future__ import annotations

import re

import pytest

from shared.config import scoring
from shared.utils.phrase_matcher import PhraseGroup, PhraseIndex


def _regex_first_match(text: str, phrases: tuple[str, ...]) -> str | None:
    """Reference implementation without negation: one regex per phrase."""
    for phrase in phrases:
        stem = phrase.endswith("*")
        core = re.escape(phrase[:-1] if stem else phrase)
        bounded = not stem and len(phrase) <= scoring.SHORT_TERM_MAX_LEN
        if re.search(rf"\b{core}\b" if bounded else rf"\b{core}", text, re.IGNORECASE):
            return phrase
    return None


CASES = [
    ("ABC matching here", ("A", "AB", "ABC")),
    ("we use tokenizer daily", ("tokeniz*", "token")),
    ("a rag system for storage", ("rag", "storage")),
    ("ragged edges", ("rag",)),
    ("roadmap to production", ("map", "production")),
    ("Recommendation System built", ("system", "recommendation system")),
    ("RAG and Rag and rag", ("rag",)),
    ("two-tower encoder", ("two-tower", "tower")),
    ("precision@k metric", ("precision@k", "precision")),
    ("nothing here", ("xyz", "abc")),
    ("research lab", ("search", "lab")),
    ("observing users", ("serving", "users")),
    ("data pipelines", ("pipeline",)),
    ("detokenization", ("tokeniz*",)),
    ("beta then alpha", ("alpha", "beta")),
]


@pytest.mark.parametrize("text,phrases", CASES)
def test_matches_regex_reference(text, phrases):
    group = PhraseGroup(phrases)
    expected = _regex_first_match(text, phrases)
    assert group.first_match(text.lower()) == expected
    assert group.any_match(text.lower()) == (expected is not None)


@pytest.mark.parametrize("text,matched", [
    ("lighter weight than ranking systems at faang", False),
    ("interested in transitioning toward nlp work", False),
    ("not a toy. built a ranking system", True),        # cue is in an earlier clause
    ("more than one product; ranking system owner", True),
])
def test_negation_cues(text, matched):
    assert PhraseGroup(("ranking system", "nlp")).any_match(text) is matched


def test_index_union_of_parts_equals_joined_text():
    phrases = ("search", "rag", "recommendation system", "tokeniz*", "pipeline", "map")
    parts = ["Recommendation System lead", "research and RAG", "", "tokenizer pipelines", "roadmap"]
    index = PhraseIndex(phrases)
    joined = "\n".join(p for p in parts if p).lower()
    assert index.matches_any_part(parts) == PhraseGroup(phrases).all_matches(joined)
    assert index.matches_any_part(parts) == {"recommendation system", "rag", "tokeniz*", "pipeline"}
    with pytest.raises(ValueError):
        PhraseIndex(("two\nlines",))
