"""module5: H1/H2 detection forces the final score to 0."""

from __future__ import annotations

import pytest

from tests.conftest import make_candidate, role, skill

UNUSED = [skill("MLflow", "expert", duration_months=0), skill("Kafka", "expert", duration_months=0)]


@pytest.mark.parametrize("kwargs,rule", [
    (dict(skills=UNUSED + [skill("Photoshop", "advanced", duration_months=0)]), "H1"),
    (dict(yoe=2.0, career=[role("ML Engineer", "work", duration_months=200)]), "H2"),
    (dict(skills=UNUSED + [skill("Python", "advanced", duration_months=36)]), None),
    (dict(), None),
])
def test_honeypot_rules(pipeline, kwargs, rule):
    _, _, _, hp, final = pipeline(make_candidate(**kwargs))
    assert hp.rule_fired == rule
    assert hp.is_honeypot is (rule is not None)
    if rule:
        assert final == 0.0
