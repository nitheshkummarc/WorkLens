"""module2/module3: evidence tiers, ML tenure and the capability fit."""

from __future__ import annotations

import pytest

from tests.conftest import make_candidate, role, skill

GENERIC = "General software work."


def _evidence(cap, prefix):
    return next(ev for ev in cap.node_strengths if ev.node.startswith(prefix + " "))


# (description, skills, assessments, summary, node, expected strength, expected source)
EVIDENCE_CASES = [
    ("Built a recommendation system for real users.", [], {}, "", "N1", 1.0, "career"),
    ("Built similarity features for analytics.", [skill("FAISS", "expert")], {"FAISS": 80.0}, "", "N2", 1.0, "skill_verified"),
    ("Improved recommendation quality.", [skill("Recommendation Systems", "expert")],
     {"Recommendation Systems": 90.0}, "", "N3", 1.0, "skill_verified"),
    (GENERIC, [skill("Qdrant", "expert")], {"Qdrant": 90.0}, "", "N2", 0.5, "claimed"),
    (GENERIC, [skill("FAISS", "expert")], {"FAISS": 10.0}, "", "N2", 0.0, "none"),
    (GENERIC, [], {}, "Built vector search features.", "N2", 0.5, "claimed"),
    ("Owned the production release process.", [], {}, "", "N5", 0.5, "career_weak"),
    ("Market research and reporting.", [], {}, "", "N1", 0.0, "none"),
    ("Built features, lighter weight than ranking systems at FAANG.", [], {}, "", "N1", 0.0, "none"),
    ("Now interested in transitioning toward NLP work.", [], {}, "", "N6", 0.0, "none"),
    ("Owned the search and discovery experience end-to-end.", [], {}, "", "N1", 1.0, "career"),
]


@pytest.mark.parametrize("desc,skills,assess,summary,node,strength,source", EVIDENCE_CASES)
def test_evidence_tiers(pipeline, desc, skills, assess, summary, node, strength, source):
    c = make_candidate(career=[role("Engineer", desc)], skills=skills, summary=summary,
                       skill_assessment_scores=assess)
    ev = _evidence(pipeline(c)[0], node)
    assert (ev.strength, ev.source) == (strength, source)


def test_keyword_stuffer_scores_far_below_demonstrated_work(pipeline):
    stuffer = make_candidate(
        cid="CAND_0000001", title="HR Manager",
        career=[role("HR Manager", "Managed recruitment, payroll, and employee relations.")],
        skills=[skill(s) for s in ("RAG", "Embeddings", "Vector Database", "LLM Fine-tuning", "Learning to Rank")],
    )
    builder = make_candidate(
        cid="CAND_0000002", title="Recommendation Systems Engineer", yoe=7.0,
        career=[role("Recommendation Systems Engineer",
                     "Built a recommendation system with embeddings and a ranking model, "
                     "evaluated with NDCG, deployed to production for real users.")],
    )
    stuffer_final, builder_final = pipeline(stuffer)[4], pipeline(builder)[4]
    assert stuffer_final < 0.3 < 0.5 < builder_final


def test_ml_depth_and_tenure_cap(pipeline):
    desc = "Built ranking and recommendation systems with embeddings, deployed to production."
    short = pipeline(make_candidate(cid="CAND_0000001", career=[role("ML Engineer", desc, duration_months=6)]))
    deep = pipeline(make_candidate(cid="CAND_0000002", career=[role("ML Engineer", desc, duration_months=60)]))
    overlap = pipeline(make_candidate(cid="CAND_0000003", yoe=5.0, career=[
        role("ML Engineer", desc, duration_months=48), role("ML Engineer", desc, duration_months=40, current=False)]))
    assert (short[1].ml_depth_factor, deep[1].ml_depth_factor) == (0.85, 1.10)
    assert overlap[0].ml_relevant_months == 60


def test_strongest_profiles_are_not_clamped_together(pipeline):
    full = ("Built a recommendation system with embeddings, learning to rank, NDCG evaluation, "
            "model serving, NLP, LoRA fine-tuning, data pipeline and distributed training.")
    best = pipeline(make_candidate(cid="CAND_0000001", career=[role("ML Engineer", full, duration_months=72)]))[1]
    less = pipeline(make_candidate(cid="CAND_0000002", career=[role(
        "ML Engineer", full.replace(", data pipeline and distributed training", ""), duration_months=72)]))[1]
    assert 0.0 <= less.capability_fit < best.capability_fit <= 1.0
