"""Behavioral multiplier: 0.50 + 0.50 * behavioral_raw, then two adjustments.

behavioral_raw is the weighted sum of eight sub-scores built from 14 of the 23
redrob_signals. A candidate inactive for more than UNAVAILABLE_DAYS or with a
response rate below UNAVAILABLE_RESPONSE_RATE gets the floor multiplier. A
candidate outside the rubric's home country has the multiplier scaled by
OUTSIDE_HOME_COUNTRY_FACTOR. Not used: profile_completeness_score, signup_date,
profile_views_received_30d, applications_submitted_30d, connection_count,
endorsements_received, expected_salary_range_inr_lpa, github_activity_score
(skill_assessment_scores is used by module2).
"""

from __future__ import annotations

import math

from shared.config import scoring
from shared.models.behavioral import BehavioralProfile
from shared.models.candidate import Candidate
from shared.models.jd_profile import JDProfile
from shared.utils.date_utils import days_since
from shared.utils.numeric import clamp01


def _band(value: float, bands: tuple[tuple[float, float], ...], default: float) -> float:
    """Score of the first band whose inclusive upper bound is >= value, else default."""
    for threshold, score in bands:
        if value <= threshold:
            return score
    return default


def _lognorm(value: float, cap: float) -> float:
    """log1p-scaled count in [0, 1], saturating at `cap`."""
    return clamp01(math.log1p(min(value, cap)) / math.log1p(cap))


class BehavioralScorer:
    """Build a BehavioralProfile per candidate."""

    def __init__(self, jd_profile: JDProfile, as_of_date: str) -> None:
        self.as_of = as_of_date
        self.weights = scoring.BEHAVIORAL_WEIGHTS
        self.logistics = jd_profile.logistics

    def _location_factor(self, candidate: Candidate) -> float:
        location = candidate.profile.location.lower()
        if any(city in location for city in self.logistics.office):
            return scoring.LOCATION_OFFICE
        if any(city in location for city in self.logistics.welcome):
            return scoring.LOCATION_WELCOME
        if candidate.profile.country.lower() == self.logistics.home_country:
            if candidate.redrob_signals.willing_to_relocate:
                return scoring.LOCATION_RELOCATE
            return scoring.LOCATION_INDIA
        return scoring.LOCATION_OUTSIDE

    def _logistics(self, candidate: Candidate) -> float:
        sig = candidate.redrob_signals
        notice = _band(sig.notice_period_days, scoring.NOTICE_BANDS, scoring.NOTICE_DEFAULT)
        location = self._location_factor(candidate)
        workmode = (
            scoring.WORKMODE_PREFERRED
            if sig.preferred_work_mode in self.logistics.preferred_work_modes
            else scoring.WORKMODE_REMOTE
        )
        return (notice + location + workmode) / 3.0

    def score(self, candidate: Candidate) -> BehavioralProfile:
        sig = candidate.redrob_signals
        days = days_since(sig.last_active_date, self.as_of)

        recency = _band(days, scoring.RECENCY_BANDS, scoring.RECENCY_DEFAULT)
        time_factor = _band(
            sig.avg_response_time_hours,
            scoring.RESPONSE_TIME_BANDS, scoring.RESPONSE_TIME_DEFAULT,
        )
        subs = {
            "recency": recency,
            "responsiveness": sig.recruiter_response_rate * time_factor,
            "open": scoring.OPEN_TRUE if sig.open_to_work_flag else scoring.OPEN_FALSE,
            "interview": sig.interview_completion_rate,
            "offer": (sig.offer_acceptance_rate if sig.offer_acceptance_rate >= 0
                      else scoring.OFFER_NEUTRAL),
            "logistics": self._logistics(candidate),
            "demand": (
                _lognorm(sig.saved_by_recruiters_30d, scoring.DEMAND_SAVED_CAP)
                + _lognorm(sig.search_appearance_30d, scoring.DEMAND_SEARCH_CAP)
            ) / 2.0,
            "trust": (sig.verified_email + sig.verified_phone + sig.linkedin_connected) / 3.0,
        }
        raw = clamp01(sum(self.weights[k] * v for k, v in subs.items()))
        unavailable = (days > scoring.UNAVAILABLE_DAYS
                       or sig.recruiter_response_rate < scoring.UNAVAILABLE_RESPONSE_RATE)
        multiplier = scoring.BEHAVIORAL_MULTIPLIER_FLOOR
        if not unavailable:
            multiplier += scoring.BEHAVIORAL_MULTIPLIER_SLOPE * raw
        if candidate.profile.country.lower() != self.logistics.home_country:
            multiplier *= scoring.OUTSIDE_HOME_COUNTRY_FACTOR

        return BehavioralProfile(
            candidate_id=candidate.candidate_id,
            behavioral_raw=raw,
            behavioral_multiplier=multiplier,
            **subs,
        )


__all__ = ["BehavioralScorer"]
