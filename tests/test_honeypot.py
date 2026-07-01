"""module5: H1/H2 impossibility detection forces final to 0."""

from __future__ import annotations

from tests.conftest import make_candidate, role, skill


def test_h1_expert_zero_duration(pipeline):
    c = make_candidate(skills=[
        skill("MLflow", "expert", duration_months=0),
        skill("Kafka", "expert", duration_months=0),
        skill("Photoshop", "advanced", duration_months=0),
    ])
    cap, fit, beh, hp, final = pipeline(c)
    assert hp.is_honeypot and hp.rule_fired == "H1"
    assert final == 0.0


def test_h2_tenure_exceeds_working_life(pipeline):
    c = make_candidate(yoe=2.0, career=[role("ML Engineer", "work", duration_months=200)])
    cap, fit, beh, hp, final = pipeline(c)
    assert hp.is_honeypot and hp.rule_fired == "H2"
    assert final == 0.0


def test_two_expert_zero_is_not_honeypot(pipeline):
    # below the >=3 threshold -> not a honeypot
    c = make_candidate(skills=[
        skill("MLflow", "expert", duration_months=0),
        skill("Kafka", "expert", duration_months=0),
        skill("Python", "advanced", duration_months=36),
    ])
    hp = pipeline(c)[3]
    assert not hp.is_honeypot


def test_normal_candidate_not_honeypot(pipeline):
    hp = pipeline(make_candidate())[3]
    assert not hp.is_honeypot
