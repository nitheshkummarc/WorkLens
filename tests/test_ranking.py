"""module6: streaming top-K selection + score-desc / id-asc tie-break."""

from __future__ import annotations

from shared.models.behavioral import BehavioralProfile
from shared.models.capability import CapabilityProfile
from shared.models.capability_fit import CapabilityFit
from shared.models.honeypot import HoneypotAnalysis
from modules.module6_ranking import TopKRanker
from tests.conftest import make_candidate


def _fit(cid, v):
    return CapabilityFit(candidate_id=cid, base_capability=v, anti_signals_fired=[], anti_penalty=0.0,
                         hard_dq=False, experience_factor=1.0, ml_depth_factor=1.0, nice_items=[],
                         nice_bonus=0.0, capability_fit=v)


def _beh(cid):  # multiplier 1.0 -> final == capability_fit
    return BehavioralProfile(candidate_id=cid, recency=1, responsiveness=1, open=1, interview=1,
                             offer=1, logistics=1, demand=1, trust=1, behavioral_raw=1.0,
                             behavioral_multiplier=1.0)


def _cap(cid):
    return CapabilityProfile(candidate_id=cid, node_strengths=[], base_capability=0.0, ml_relevant_months=0)


def _hp(cid):
    return HoneypotAnalysis(candidate_id=cid, is_honeypot=False)


def _add(ranker, cid, v, honeypot=False):
    c = make_candidate(cid=cid)
    hp = HoneypotAnalysis(candidate_id=cid, is_honeypot=honeypot)
    ranker.add(c, _cap(cid), _fit(cid, v), _beh(cid), hp)


def test_topk_keeps_highest_and_evicts():
    r = TopKRanker(k=3)
    for i, v in enumerate([0.9, 0.1, 0.5, 0.7, 0.2], start=1):
        _add(r, f"CAND_000000{i}", v)
    entries = r.finalize()
    assert [e.score for e in entries] == [0.9, 0.7, 0.5]
    assert [e.rank for e in entries] == [1, 2, 3]


def test_score_tie_breaks_by_id_ascending():
    r = TopKRanker(k=3)
    _add(r, "CAND_0000001", 0.9)
    _add(r, "CAND_0000002", 0.8)
    _add(r, "CAND_0000003", 0.8)
    _add(r, "CAND_0000005", 0.8)   # ties; largest id must be evicted
    _add(r, "CAND_0000004", 0.7)
    ids = [e.candidate.candidate_id for e in r.finalize()]
    assert ids == ["CAND_0000001", "CAND_0000002", "CAND_0000003"]


def test_honeypot_scores_zero_and_sinks():
    r = TopKRanker(k=3)
    _add(r, "CAND_0000001", 0.9, honeypot=True)   # capability 0.9 but honeypot -> final 0
    _add(r, "CAND_0000002", 0.3)
    _add(r, "CAND_0000003", 0.1)
    entries = r.finalize()
    assert entries[0].candidate.candidate_id == "CAND_0000002"   # 0.3 ranks first
    assert entries[-1].candidate.candidate_id == "CAND_0000001"  # honeypot sinks to bottom
    assert entries[-1].score == 0.0


def test_scores_non_increasing():
    r = TopKRanker(k=5)
    for i, v in enumerate([0.3, 0.9, 0.1, 0.5, 0.7], start=1):
        _add(r, f"CAND_000000{i}", v)
    scores = [e.score for e in r.finalize()]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
