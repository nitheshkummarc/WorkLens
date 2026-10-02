"""module3: each anti-signal fires on its pattern and not otherwise."""

from __future__ import annotations

import pytest

from tests.conftest import make_candidate, role

ML = "Built a recommendation system with embeddings, deployed to production."


def _short_roles(n, current_months):
    return [role("ML Engineer", ML, duration_months=current_months)] + [
        role("ML Engineer", ML, duration_months=12, current=False) for _ in range(n)
    ] + [role("ML Engineer", ML, duration_months=60, current=False)]


# (rule, candidate kwargs, expected to fire)
CASES = [
    ("research_only", dict(title="Research Scientist",
                           career=[role("Research Scientist", "Published papers on semantic search.")]), True),
    ("research_only", dict(title="Research Scientist", career=[role("Research Scientist", ML)]), False),
    ("consulting_only", dict(career=[role("ML Engineer", ML, company="Infosys"),
                                     role("ML Engineer", ML, company="TCS", current=False)]), True),
    ("consulting_only", dict(career=[role("ML Engineer", ML, company="Infosys"),
                                     role("ML Engineer", ML, company="Swiggy", current=False)]), False),
    ("langchain_only", dict(career=[role("AI Engineer", "Built chatbots with LangChain and the OpenAI API.")]), True),
    ("langchain_only", dict(career=[role("AI Engineer", "Built LangChain apps and XGBoost ranking models.")]), False),
    ("langchain_only", dict(career=[role("AI Engineer", "Built a semantic search feature with FAISS; "
                                                        "later a chatbot on the OpenAI API.")]), False),
    ("framework_tutorial", dict(career=[role("Developer", "Completed a bootcamp and a demo project.")]), True),
    ("framework_tutorial", dict(summary="Udemy course graduate.",
                                career=[role("Developer", "General software work.")]), True),
    ("framework_tutorial", dict(career=[role("ML Engineer", ML + " Mentored a bootcamp.")]), False),
    ("title_chasing", dict(yoe=8.0, career=_short_roles(3, 40)), True),
    ("title_chasing", dict(yoe=8.0, career=_short_roles(2, 3)), False),     # new current role ignored
    ("no_recent_handson", dict(title="Engineering Manager",
                               career=[role("Engineering Manager", "Managed a team of engineers.")]), True),
    ("no_recent_handson", dict(title="Engineering Manager", career=[role("Engineering Manager", ML)]), False),
    ("no_recent_handson", dict(title="MVP Developer", career=[role("MVP Developer", "Built MVP features.")]), False),
    ("cv_speech_robotics", dict(career=[role("Engineer", "Object detection with OpenCV.")]), True),
    ("cv_speech_robotics", dict(career=[role("Engineer", "Object detection and a recommendation system.")]), False),
]


@pytest.mark.parametrize("rule,kwargs,fires", CASES)
def test_rule(pipeline, rule, kwargs, fires):
    assert (rule in pipeline(make_candidate(**kwargs))[1].anti_signals_fired) is fires


def test_hard_dq_and_penalty_cap(pipeline):
    fit = pipeline(make_candidate(
        title="Research Scientist",
        career=[role("Research Scientist", "Object detection research using LangChain; bootcamp.",
                     company="Infosys")],
    ))[1]
    assert fit.hard_dq
    assert fit.anti_penalty == 0.50
