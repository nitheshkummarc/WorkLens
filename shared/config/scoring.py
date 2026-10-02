"""Numeric scoring constants. Role vocabulary is in data/jd_rubric.json."""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Node strengths
# ---------------------------------------------------------------------------
NODE_STRENGTH_NONE: Final[float] = 0.0
NODE_STRENGTH_WEAK: Final[float] = 0.5     # claimed, or only loosely evidenced
NODE_STRENGTH_STRONG: Final[float] = 1.0   # demonstrated in career history, or assessed

# Nodes at or above this importance are treated as critical requirements.
CRITICAL_IMPORTANCE_MIN: Final[float] = 0.9

# Assessment gates on skill_assessment_scores (0-100).
STRONG_ASSESS_MIN: Final[float] = 50.0     # >= 50 promotes an advanced/expert skill to strong
STUFF_ASSESS_MIN: Final[float] = 30.0      # < 30 drops the skill before matching

# Phrases up to this length must match a whole word.
SHORT_TERM_MAX_LEN: Final[int] = 4

# A match is ignored when one of these words appears among the
# NEGATION_WINDOW_WORDS words before it in the same clause
# ("lighter weight than ranking systems", "transitioning toward NLP").
NEGATION_CUES: Final[frozenset[str]] = frozenset(
    {"than", "toward", "towards", "not", "no", "never", "without"}
)
NEGATION_WINDOW_WORDS: Final[int] = 3

# ---------------------------------------------------------------------------
# Experience factor by years_of_experience.
# Each band is (lo_inclusive, hi_exclusive, factor); the last band is open-ended.
# ---------------------------------------------------------------------------
EXPERIENCE_BANDS: Final[tuple[tuple[float, float, float], ...]] = (
    (0.0, 3.0, 0.70),
    (3.0, 5.0, 0.90),
    (5.0, 9.0, 1.00),
    (9.0, 12.0, 0.95),
    (12.0, float("inf"), 0.85),
)

# ---------------------------------------------------------------------------
# ML-depth factor by years in ML-relevant roles.
# ---------------------------------------------------------------------------
ML_DEPTH_YEARS_HIGH: Final[float] = 4.0
ML_DEPTH_YEARS_SOLID: Final[float] = 2.0
ML_DEPTH_YEARS_SHALLOW: Final[float] = 1.0

ML_DEPTH_FACTOR_HIGH: Final[float] = 1.10     # >= 4 years
ML_DEPTH_FACTOR_SOLID: Final[float] = 1.00    # 2-4 years
ML_DEPTH_FACTOR_SHALLOW: Final[float] = 0.95  # 1-2 years
ML_DEPTH_FACTOR_PIVOT: Final[float] = 0.85    # < 1 year, base_capability > 0
ML_DEPTH_FACTOR_NONE: Final[float] = 1.00     # < 1 year, base_capability == 0

# ---------------------------------------------------------------------------
# Anti-signals: key -> (penalty, is_hard_dq). A hard DQ also caps
# base_capability at HARD_DQ_BASE_CEILING.
# ---------------------------------------------------------------------------
ANTI_SIGNAL_PENALTIES: Final[dict[str, tuple[float, bool]]] = {
    "research_only":      (0.25,  True),
    "consulting_only":    (0.125, False),
    "langchain_only":     (0.20,  False),
    "framework_tutorial": (0.15,  False),
    "title_chasing":      (0.10,  False),
    "no_recent_handson":  (0.10,  False),
    "cv_speech_robotics": (0.15,  False),
}
ANTI_PENALTY_CAP: Final[float] = 0.50
HARD_DQ_BASE_CEILING: Final[float] = 0.30

# title_chasing: at least this many completed roles, each shorter than the limit.
TITLE_CHASING_MIN_ROLES: Final[int] = 3
TITLE_CHASING_MAX_DURATION_MONTHS: Final[int] = 18

# ---------------------------------------------------------------------------
# Nice-to-have bonus (additive).
# ---------------------------------------------------------------------------
NICE_BONUS_PER_ITEM: Final[float] = 0.03
NICE_BONUS_CAP: Final[float] = 0.10

# ---------------------------------------------------------------------------
# Behavioral multiplier = FLOOR + SLOPE * behavioral_raw. Weights sum to 1.0.
# ---------------------------------------------------------------------------
BEHAVIORAL_WEIGHTS: Final[dict[str, float]] = {
    "recency":        0.30,
    "responsiveness": 0.25,
    "open":           0.10,
    "interview":      0.10,
    "offer":          0.05,
    "logistics":      0.10,
    "demand":         0.07,
    "trust":          0.03,
}
BEHAVIORAL_MULTIPLIER_FLOOR: Final[float] = 0.50
BEHAVIORAL_MULTIPLIER_SLOPE: Final[float] = 0.50

# A candidate this inactive or unresponsive is treated as unavailable and gets
# the floor multiplier.
UNAVAILABLE_DAYS: Final[int] = 180
UNAVAILABLE_RESPONSE_RATE: Final[float] = 0.10

# Applied to the multiplier for candidates outside the rubric's home country
# (the employer does not sponsor work visas).
OUTSIDE_HOME_COUNTRY_FACTOR: Final[float] = 0.80

# Recency: (max_days_inclusive, score) on days since last_active_date.
RECENCY_BANDS: Final[tuple[tuple[float, float], ...]] = (
    (30.0, 1.00),
    (60.0, 0.90),
    (90.0, 0.75),
    (180.0, 0.50),
)
RECENCY_DEFAULT: Final[float] = 0.25

# Responsiveness time factor on avg_response_time_hours.
RESPONSE_TIME_BANDS: Final[tuple[tuple[float, float], ...]] = (
    (24.0, 1.00),
    (72.0, 0.90),
)
RESPONSE_TIME_DEFAULT: Final[float] = 0.80

OPEN_TRUE: Final[float] = 1.0
OPEN_FALSE: Final[float] = 0.4

OFFER_NEUTRAL: Final[float] = 0.5        # offer_acceptance_rate == -1 (no history)

# Logistics: notice period bands, (max_days_inclusive, score).
NOTICE_BANDS: Final[tuple[tuple[float, float], ...]] = (
    (30.0, 1.0),
    (60.0, 0.8),
    (90.0, 0.6),
)
NOTICE_DEFAULT: Final[float] = 0.4

# Logistics: location factor.
LOCATION_OFFICE: Final[float] = 1.00      # office city
LOCATION_WELCOME: Final[float] = 0.85     # other city named in the JD
LOCATION_RELOCATE: Final[float] = 0.85    # in India, willing to relocate
LOCATION_INDIA: Final[float] = 0.55       # in India, not relocating
LOCATION_OUTSIDE: Final[float] = 0.30     # outside India (no visa sponsorship)

# Logistics: work-mode factor.
WORKMODE_PREFERRED: Final[float] = 1.0    # hybrid, flexible, onsite
WORKMODE_REMOTE: Final[float] = 0.7

# Demand: mean of two log-scaled counts, each capped.
DEMAND_SAVED_CAP: Final[float] = 20.0     # saved_by_recruiters_30d
DEMAND_SEARCH_CAP: Final[float] = 500.0   # search_appearance_30d

# ---------------------------------------------------------------------------
# Honeypot rules
# ---------------------------------------------------------------------------
# H1: at least MIN_COUNT skills at these proficiencies with duration_months == 0.
HONEYPOT_H1_PROFICIENCIES: Final[tuple[str, ...]] = ("advanced", "expert")
HONEYPOT_H1_MIN_COUNT: Final[int] = 3
# H2: total career months > years_of_experience * 12 * SLACK_MULT + SLACK_ADD_MONTHS.
HONEYPOT_H2_SLACK_MULT: Final[float] = 1.5
HONEYPOT_H2_SLACK_ADD_MONTHS: Final[int] = 12

# ---------------------------------------------------------------------------
# Reasoning text thresholds (module7)
# ---------------------------------------------------------------------------
REASON_ML_TENURE_YEARS: Final[float] = 4.0     # tenure listed as a strength at or above this
REASON_STALE_DAYS: Final[int] = 90             # inactivity named as a gap above this
REASON_LOW_RESPONSE_RATE: Final[float] = 0.30  # response rate named as a gap below this
REASON_LONG_NOTICE_DAYS: Final[int] = 90       # notice period named as a gap at or above this

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
SUBMISSION_ROW_COUNT: Final[int] = 100
SCORE_ROUND_DECIMALS: Final[int] = 6

__all__ = [name for name in dir() if name.isupper()]
