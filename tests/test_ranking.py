"""module6: streaming top-K selection and the score/id tie-break."""

from __future__ import annotations

from shared.models.behavioral import BehavioralProfile
from shared.models.capability import CapabilityProfile
from shared.models.capability_fit import CapabilityFit
from shared.models.honeypot import HoneypotAnalysis
from modules.module6_ranking import TopKRanker
from tests.conftest import make_candidate


def _add(ranker, cid, value, honeypot=False):
    fit = CapabilityFit(candidate_id=cid, base_capability=value, anti_signals_fired=[], anti_penalty=0.0,
                        hard_dq=False, experience_factor=1.0, ml_depth_factor=1.0, nice_items=[],
                        nice_bonus=0.0, capability_fit=value)
    beh = BehavioralProfile(candidate_id=cid, recency=1, responsiveness=1, open=1, interview=1, offer=1,
                            logistics=1, demand=1, trust=1, behavioral_raw=1.0, behavioral_multiplier=1.0)
    cap = CapabilityProfile(candidate_id=cid, node_strengths=[], base_capability=0.0, ml_relevant_months=0)
    ranker.add(make_candidate(cid=cid), cap, fit, beh, HoneypotAnalysis(candidate_id=cid, is_honeypot=honeypot))


def test_keeps_highest_in_order():
    ranker = TopKRanker(k=3)
    for i, v in enumerate([0.3, 0.9, 0.1, 0.5, 0.7], start=1):
        _add(ranker, f"CAND_000000{i}", v)
    entries = ranker.finalize()
    assert [e.score for e in entries] == [0.9, 0.7, 0.5]
    assert [e.rank for e in entries] == [1, 2, 3]


def test_ties_keep_smaller_ids_including_after_rounding():
    ranker = TopKRanker(k=3)
    for cid, v in [("CAND_0000005", 0.8), ("CAND_0000001", 0.9), ("CAND_0000003", 0.80000001),
                   ("CAND_0000002", 0.8), ("CAND_0000004", 0.7)]:
        _add(ranker, cid, v)
    assert [e.candidate.candidate_id for e in ranker.finalize()] == \
        ["CAND_0000001", "CAND_0000002", "CAND_0000003"]


def test_honeypot_scores_zero():
    ranker = TopKRanker(k=2)
    _add(ranker, "CAND_0000001", 0.9, honeypot=True)
    _add(ranker, "CAND_0000002", 0.3)
    entries = ranker.finalize()
    assert [(e.candidate.candidate_id, e.score) for e in entries] == [("CAND_0000002", 0.3), ("CAND_0000001", 0.0)]
