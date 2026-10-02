"""Shared fixtures and a synthetic candidate factory."""

from __future__ import annotations

import pytest

from shared.config import paths
from shared.models.candidate import Candidate
from shared.utils.ontology_loader import load_ontology
from modules.module1_jd_rubric import build_jd_profile
from modules.module2_capability import CapabilityExtractor
from modules.module3_capability_fit import CapabilityFitAssembler
from modules.module4_behavioral import BehavioralScorer
from modules.module5_honeypot import HoneypotDetector
from modules.module6_ranking import final_score

AS_OF = "2026-05-27"

_DEFAULT_SIGNALS = dict(
    profile_completeness_score=80.0, signup_date="2024-01-01", last_active_date="2026-05-20",
    open_to_work_flag=True, profile_views_received_30d=10, applications_submitted_30d=2,
    recruiter_response_rate=0.5, avg_response_time_hours=24.0, skill_assessment_scores={},
    connection_count=100, endorsements_received=20, notice_period_days=30,
    expected_salary_range_inr_lpa={"min": 20.0, "max": 40.0}, preferred_work_mode="hybrid",
    willing_to_relocate=True, github_activity_score=10.0, search_appearance_30d=50,
    saved_by_recruiters_30d=5, interview_completion_rate=0.8, offer_acceptance_rate=0.6,
    verified_email=True, verified_phone=True, linkedin_connected=True,
)


def candidate_record(cid="CAND_0000001", title="ML Engineer", summary="", skills=None,
                     career=None, yoe=6.0, location="Pune", country="India",
                     **signal_overrides) -> dict:
    """Return a schema-valid candidate dict; override only what a test needs."""
    signals = {**_DEFAULT_SIGNALS, **signal_overrides}
    if career is None:
        career = [role(title, "Worked on software.", duration_months=int(yoe * 12))]
    return dict(
        candidate_id=cid,
        profile=dict(anonymized_name="Anon", headline=title, summary=summary, location=location,
                     country=country, years_of_experience=yoe, current_title=title,
                     current_company=career[0]["company"], current_company_size="201-500",
                     current_industry="Software"),
        career_history=career, education=[], skills=skills or [],
        certifications=[], languages=[], redrob_signals=signals,
    )


def make_candidate(**kwargs) -> Candidate:
    return Candidate.model_validate(candidate_record(**kwargs))


def skill(name, proficiency="advanced", endorsements=10, duration_months=24):
    return dict(name=name, proficiency=proficiency, endorsements=endorsements,
                duration_months=duration_months)


def role(title, description, duration_months=48, company="Acme", current=True):
    return dict(company=company, title=title, start_date="2020-01-01",
                end_date=None if current else "2023-01-01", duration_months=duration_months,
                is_current=current, industry="Software", company_size="201-500",
                description=description)


@pytest.fixture(scope="session")
def nodes():
    return load_ontology(paths.ONTOLOGY_PATH)


@pytest.fixture(scope="session")
def jd(nodes):
    return build_jd_profile(nodes, paths.JD_RUBRIC_PATH)


@pytest.fixture(scope="session")
def pipeline(nodes, jd):
    """Score one candidate through modules 2-6; returns (cap, fit, beh, hp, final)."""
    m2 = CapabilityExtractor(nodes, jd.ml_nodes)
    m3 = CapabilityFitAssembler(jd)
    m4 = BehavioralScorer(jd, AS_OF)
    m5 = HoneypotDetector()

    def score(c):
        cap = m2.extract(c)
        fit = m3.assemble(c, cap)
        beh = m4.score(c)
        hp = m5.detect(c)
        return cap, fit, beh, hp, final_score(fit, beh, hp)

    return score
