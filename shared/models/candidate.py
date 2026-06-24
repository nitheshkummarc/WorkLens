"""Candidate input model — mirrors `candidate_schema.json` exactly.

Parsed/validated by `shared/utils/jsonl_reader` (and any direct loader), consumed
by the scoring modules. Types are exact (interface_contract.md §1); Pydantic v2
validates at the boundary so malformed records are caught early.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

CompanySize = Literal[
    "1-10", "11-50", "51-200", "201-500",
    "501-1000", "1001-5000", "5001-10000", "10001+",
]


class Profile(BaseModel):
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float = Field(ge=0, le=50)
    current_title: str
    current_company: str
    current_company_size: CompanySize
    current_industry: str


class CareerEntry(BaseModel):
    company: str
    title: str
    start_date: str                      # ISO date "YYYY-MM-DD"
    end_date: Optional[str] = None       # null when current
    duration_months: int = Field(ge=0)
    is_current: bool
    industry: str
    company_size: CompanySize
    description: str


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: Literal["tier_1", "tier_2", "tier_3", "tier_4", "unknown"]


class Skill(BaseModel):
    name: str
    proficiency: Literal["beginner", "intermediate", "advanced", "expert"]
    endorsements: int = Field(ge=0)
    duration_months: Optional[int] = Field(default=None, ge=0)


class Certification(BaseModel):
    name: str
    issuer: str
    year: int


class Language(BaseModel):
    language: str
    proficiency: Literal["basic", "conversational", "professional", "native"]


class RedrobSignals(BaseModel):
    """All 23 platform/engagement signals."""

    profile_completeness_score: float = Field(ge=0, le=100)
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool
    profile_views_received_30d: int = Field(ge=0)
    applications_submitted_30d: int = Field(ge=0)
    recruiter_response_rate: float = Field(ge=0, le=1)
    avg_response_time_hours: float = Field(ge=0)
    skill_assessment_scores: dict[str, float] = Field(default_factory=dict)
    connection_count: int = Field(ge=0)
    endorsements_received: int = Field(ge=0)
    notice_period_days: int = Field(ge=0, le=180)
    expected_salary_range_inr_lpa: dict[str, float]
    preferred_work_mode: Literal["remote", "hybrid", "onsite", "flexible"]
    willing_to_relocate: bool
    github_activity_score: float = Field(ge=-1, le=100)        # -1 = no github
    search_appearance_30d: int = Field(ge=0)
    saved_by_recruiters_30d: int = Field(ge=0)
    interview_completion_rate: float = Field(ge=0, le=1)
    offer_acceptance_rate: float = Field(ge=-1, le=1)          # -1 = no history
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool


class Candidate(BaseModel):
    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    profile: Profile
    career_history: list[CareerEntry] = Field(min_length=1, max_length=10)
    education: list[Education] = Field(default_factory=list, max_length=5)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    redrob_signals: RedrobSignals


__all__ = [
    "CompanySize", "Profile", "CareerEntry", "Education", "Skill",
    "Certification", "Language", "RedrobSignals", "Candidate",
]
