"""module4: sub-score bands, logistics and the availability rules."""

from __future__ import annotations

import pytest

from shared.config import scoring
from tests.conftest import make_candidate


def _beh(pipeline, **kwargs):
    return pipeline(make_candidate(**kwargs))[2]


@pytest.mark.parametrize("last_active,score", [
    ("2026-05-01", 1.0), ("2026-04-15", 0.9), ("2026-03-15", 0.75), ("2026-02-01", 0.5), ("2025-01-01", 0.25),
])
def test_recency_bands(pipeline, last_active, score):
    assert _beh(pipeline, last_active_date=last_active).recency == score


def test_best_profile_and_neutral_offer(pipeline):
    best = _beh(pipeline, last_active_date="2026-05-27", recruiter_response_rate=1.0,
                avg_response_time_hours=1.0, interview_completion_rate=1.0, offer_acceptance_rate=1.0,
                saved_by_recruiters_30d=50, search_appearance_30d=900)
    assert best.behavioral_multiplier == 1.0
    assert _beh(pipeline, offer_acceptance_rate=-1.0).offer == scoring.OFFER_NEUTRAL


def test_location_and_work_mode_ordering(pipeline):
    office = _beh(pipeline, location="Pune, Maharashtra")
    welcome = _beh(pipeline, location="Hyderabad, Telangana")
    india = _beh(pipeline, location="Jaipur, Rajasthan", willing_to_relocate=False)
    assert office.logistics > welcome.logistics > india.logistics
    assert (_beh(pipeline, preferred_work_mode="remote").logistics
            < _beh(pipeline, preferred_work_mode="hybrid").logistics)


@pytest.mark.parametrize("overrides", [
    dict(last_active_date="2025-10-01"),          # 238 days
    dict(recruiter_response_rate=0.05),
])
def test_unavailable_candidates_get_the_floor(pipeline, overrides):
    assert _beh(pipeline, **overrides).behavioral_multiplier == scoring.BEHAVIORAL_MULTIPLIER_FLOOR


def test_outside_home_country_is_scaled(pipeline):
    home = _beh(pipeline, location="Pune, Maharashtra")
    abroad = _beh(pipeline, location="Berlin", country="Germany")
    assert abroad.behavioral_multiplier < home.behavioral_multiplier * scoring.OUTSIDE_HOME_COUNTRY_FACTOR + 1e-9
