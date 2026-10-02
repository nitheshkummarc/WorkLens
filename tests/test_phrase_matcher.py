"""PhraseGroup and PhraseIndex matching rules."""

from __future__ import annotations

import pytest

from shared.utils.phrase_matcher import PhraseGroup, PhraseIndex
from tools.bench_matcher import regex_pattern


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
]


@pytest.mark.parametrize("text,phrases", CASES)
def test_matches_regex_reference(text, phrases):
    lowered = text.lower()
    expected = frozenset(p for p in phrases if regex_pattern(p).search(lowered))
    group = PhraseGroup(phrases)
    assert group.all_matches(lowered) == expected
    assert group.any_match(lowered) == bool(expected)


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
