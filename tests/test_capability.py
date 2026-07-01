"""module2/module3: description-primary scoring, the anti-stuffer lever."""

from __future__ import annotations

from tests.conftest import make_candidate, role, skill


def test_demonstrated_work_scores_strong(pipeline):
    c = make_candidate(
        title="Recommendation Systems Engineer", yoe=7.0,
        career=[role("Recommendation Systems Engineer",
                     "Built a recommendation system with embeddings and a ranking model, "
                     "evaluated with NDCG, deployed to production for real users.")],
    )
    cap, fit, beh, hp, final = pipeline(c)
    assert cap.base_capability > 0.6
    assert fit.capability_fit > 0.6
    assert final > 0.4


def test_keyword_stuffer_scored_low(pipeline):
    # non-AI title + non-AI career description, but skills list stuffed with AI terms
    c = make_candidate(
        title="HR Manager", yoe=6.0,
        career=[role("HR Manager", "Managed recruitment, payroll, and employee relations.")],
        skills=[skill("RAG"), skill("Embeddings"), skill("Vector Database"),
                skill("LLM Fine-tuning"), skill("Learning to Rank")],
    )
    cap, fit, beh, hp, final = pipeline(c)
    assert cap.base_capability <= 0.5      # unverified skills capped at weak
    # far below a demonstrated fit (>0.6) and the real-run top-100 cutoff (~0.75)
    assert final < 0.35


def test_unverified_skill_capped_but_assessment_promotes(pipeline, nodes):
    # same skill, once unverified (weak) and once assessment-verified (strong)
    base = dict(title="Data Scientist",
                career=[role("Data Scientist", "General analytics and reporting.")],
                skills=[skill("FAISS", "expert")])
    weak = pipeline(make_candidate(cid="CAND_0000001", **base))[0]
    strong = pipeline(make_candidate(cid="CAND_0000002",
                                     skill_assessment_scores={"FAISS": 80.0}, **base))[0]
    assert strong.base_capability > weak.base_capability


def test_base_capability_in_range_and_all_nodes_present(pipeline, nodes):
    c = make_candidate()
    cap = pipeline(c)[0]
    assert 0.0 <= cap.base_capability <= 1.0
    assert len(cap.node_strengths) == len(nodes)


def test_ml_depth_factor_rewards_tenure(pipeline):
    desc = "Built ranking and recommendation systems with embeddings, deployed to production."
    short = make_candidate(cid="CAND_0000001", yoe=6.0,
                           career=[role("ML Engineer", desc, duration_months=6)])
    deep = make_candidate(cid="CAND_0000002", yoe=6.0,
                          career=[role("ML Engineer", desc, duration_months=60)])
    short_fit = pipeline(short)[1]
    deep_fit = pipeline(deep)[1]
    assert deep_fit.ml_depth_factor >= short_fit.ml_depth_factor
    assert 0.85 <= short_fit.ml_depth_factor <= 1.10
