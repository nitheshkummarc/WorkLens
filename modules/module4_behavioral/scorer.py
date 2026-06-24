"""Behavioral multiplier (§3) — module4.

Turns the 23 `redrob_signals` into 8 weighted sub-scores → `behavioral_raw` →
`behavioral_multiplier = 0.50 + 0.50·raw ∈ [0.50, 1.00]`. Behavior is a
*modifier* on capability, never the driver: a fully unavailable candidate is
halved, not eliminated (the floor), and a strong-but-stale candidate can fall
below an available twin — intended per the JD's "down-weight the unavailable".

All weights/tables come from `shared/config/scoring.py`; logistics city buckets
come from `data/jd_rubric.json`. `-1` sentinels and missing values map to neutral
(§3.3: absence ≠ negative). Recency is measured against AS_OF, not the clock.
"""

from __future__ import annotations

import math

from shared.config import scoring
from shared.models.behavioral import BehavioralProfile
from shared.models.candidate import Candidate
from shared.utils.date_utils import days_since


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _band(value: float, bands: tuple[tuple[float, float], ...], default: float) -> float:
    """First score whose inclusive threshold the value falls under, else default."""
    for threshold, score in bands:
        if value <= threshold:
            return score
    return default


def _lognorm(value: float, cap: float) -> float:
    """log1p-normalized count, saturating at `cap` → [0, 1]."""
    return _clamp01(math.log1p(min(value, cap)) / math.log1p(cap))


_PREFERRED_WORK_MODES = ("hybrid", "flexible", "onsite")


class BehavioralScorer:
    """Compute the behavioral multiplier; setup (weights, city buckets) done once."""

    def __init__(self, as_of_date: str, logistics_buckets: dict) -> None:
        self.as_of = as_of_date
        self.weights = scoring.BEHAVIORAL_WEIGHTS
        self.office_cities = tuple(c.lower() for c in logistics_buckets["office"])
        self.welcome_cities = tuple(c.lower() for c in logistics_buckets["welcome"])

    # -- logistics sub-factors (§3.2) ---------------------------------------
    def _location_factor(self, candidate: Candidate) -> float:
        location = candidate.profile.location.lower()
        country = candidate.profile.country.lower()
        if any(city in location for city in self.office_cities):
            return scoring.LOCATION_OFFICE
        if any(city in location for city in self.welcome_cities):
            return scoring.LOCATION_WELCOME
        if country == "india":
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
            if sig.preferred_work_mode in _PREFERRED_WORK_MODES
            else scoring.WORKMODE_REMOTE
        )
        return (notice + location + workmode) / 3.0

    # -- public --------------------------------------------------------------
    def score(self, candidate: Candidate) -> BehavioralProfile:
        sig = candidate.redrob_signals

        recency = _band(
            days_since(sig.last_active_date, self.as_of),
            scoring.RECENCY_BANDS, scoring.RECENCY_DEFAULT,
        )
        time_factor = _band(
            sig.avg_response_time_hours,
            scoring.RESPONSE_TIME_BANDS, scoring.RESPONSE_TIME_DEFAULT,
        )
        responsiveness = sig.recruiter_response_rate * time_factor
        open_ = scoring.OPEN_TRUE if sig.open_to_work_flag else scoring.OPEN_FALSE
        interview = sig.interview_completion_rate
        offer = sig.offer_acceptance_rate if sig.offer_acceptance_rate >= 0 else scoring.OFFER_NEUTRAL
        logistics = self._logistics(candidate)
        demand = (
            _lognorm(sig.saved_by_recruiters_30d, scoring.DEMAND_SAVED_CAP)
            + _lognorm(sig.search_appearance_30d, scoring.DEMAND_SEARCH_CAP)
        ) / 2.0
        trust = sum(
            (sig.verified_email, sig.verified_phone, sig.linkedin_connected)
        ) / 3.0

        subs = {
            "recency": recency,
            "responsiveness": responsiveness,
            "open": open_,
            "interview": interview,
            "offer": offer,
            "logistics": logistics,
            "demand": demand,
            "trust": trust,
        }
        raw = _clamp01(sum(self.weights[k] * v for k, v in subs.items()))
        multiplier = (
            scoring.BEHAVIORAL_MULTIPLIER_FLOOR
            + scoring.BEHAVIORAL_MULTIPLIER_SLOPE * raw
        )

        return BehavioralProfile(
            candidate_id=candidate.candidate_id,
            recency=recency,
            responsiveness=_clamp01(responsiveness),
            open=open_,
            interview=interview,
            offer=offer,
            logistics=logistics,
            demand=demand,
            trust=trust,
            behavioral_raw=raw,
            behavioral_multiplier=multiplier,
        )


__all__ = ["BehavioralScorer"]
