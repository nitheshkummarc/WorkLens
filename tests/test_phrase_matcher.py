"""shared/utils/phrase_matcher: the optimized PhraseGroup must equal the legacy
regex matcher exactly (the Phase 1B acceptance gate)."""

from __future__ import annotations

import pytest

from shared.utils.phrase_matcher import PhraseGroup, first_match, any_match

CASES = [
    ("ABC matching here", ("A", "AB", "ABC")),
    ("we use tokenizer daily", ("tokeniz*", "token")),
    ("a rag system for storage", ("rag", "storage")),
    ("roadmap to production", ("map", "production")),       # 'map' must NOT match in 'roadmap'
    ("Recommendation System built", ("system", "recommendation system")),
    ("RAG and Rag and rag", ("rag",)),                      # case-insensitive
    ("two-tower encoder", ("two-tower", "tower")),
    ("precision@k metric", ("precision@k", "precision")),
    ("nothing here", ("xyz", "abc")),
]


@pytest.mark.parametrize("text,phrases", CASES)
def test_group_matches_legacy(text, phrases):
    g = PhraseGroup(phrases)
    assert g.first_match(text) == first_match(text, phrases)
    assert g.any_match(text) == any_match(text, phrases)


def test_first_match_is_tuple_order_not_text_order():
    # 'beta' appears first in the text but 'alpha' is first in the tuple and also present
    g = PhraseGroup(("alpha", "beta"))
    assert g.first_match("beta then alpha") == "alpha"


def test_short_term_word_boundary():
    assert PhraseGroup(("rag",)).any_match("rag pipeline") is True
    assert PhraseGroup(("rag",)).any_match("storage bucket") is False
