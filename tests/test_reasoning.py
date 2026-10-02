"""module7: reasoning wording matches the evidence and the actual gap."""

from __future__ import annotations

import pytest

from modules.module6_ranking import RankedEntry
from modules.module7_reasoning import ReasoningGenerator
from tests.conftest import AS_OF, make_candidate, role, skill

FULL_CORE = ("Built a recommendation system with embeddings and a learning to rank model, "
             "evaluated with NDCG, model serving in production. Fine-tuning with LoRA; "
             "distributed training. Text classification with NLP.")


@pytest.fixture(scope="module")
def reasoner(jd):
    return ReasoningGenerator(jd, AS_OF)


def _reason(pipeline, reasoner, rank=1, **kwargs):
    c = make_candidate(**kwargs)
    cap, fit, beh, hp, final = pipeline(c)
    entry = RankedEntry(rank=rank, score=final, candidate=c, capability=cap, fit=fit,
                        behavioral=beh, honeypot=hp)
    return reasoner.reason(entry)


def test_self_reported_evidence_is_called_self_reported(pipeline, reasoner):
    text = _reason(pipeline, reasoner,
                   career=[role("ML Engineer", "Built a recommendation system with embeddings "
                                "and a learning to rank model, evaluated with NDCG.", duration_months=72)],
                   yoe=6.0, skills=[skill("MLflow")], summary="Experience with model serving.")
    assert "only self-reported ML Production & Deployment (MLOps) evidence" in text


def test_generic_career_evidence_is_not_called_claimed(pipeline, reasoner):
    text = _reason(pipeline, reasoner, yoe=6.0,
                   career=[role("ML Engineer", "Built a recommendation system with embeddings "
                                "and a learning to rank model, evaluated with NDCG; "
                                "owned the production release.", duration_months=72)])
    assert "only indirect ML Production & Deployment (MLOps) evidence in career history" in text
    assert "claimed" not in text


def test_inactive_candidate_concern_is_behavioral(pipeline, reasoner):
    text = _reason(pipeline, reasoner, rank=98, yoe=6.0, last_active_date="2025-12-01",
                   recruiter_response_rate=0.16,
                   career=[role("ML Engineer", FULL_CORE, duration_months=72)])
    assert "main gap: no platform activity in 177 days and a low recruiter response rate (0.16)" in text


def test_no_gap_is_not_labelled_a_concern(pipeline, reasoner):
    text = _reason(pipeline, reasoner, yoe=6.0, recruiter_response_rate=0.9,
                   career=[role("ML Engineer", FULL_CORE, duration_months=72)])
    assert text.endswith("No material gap identified.")
    assert "Concern" not in text


def test_low_rank_leads_with_gap(pipeline, reasoner):
    text = _reason(pipeline, reasoner, rank=80, career=[role("Engineer", "General software work.")])
    assert " — main gap: no demonstrated " in text


def test_tenure_shown_with_one_decimal(pipeline, reasoner):
    text = _reason(pipeline, reasoner, yoe=6.0, recruiter_response_rate=0.9,
                   career=[role("ML Engineer", FULL_CORE, duration_months=43)])
    assert "only ~3.6 yrs of applied-ML tenure" in text
