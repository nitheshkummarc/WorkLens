"""Single source of truth for every NUMERIC scoring constant in WorkLens-RedRob.

All values are taken **verbatim** from `REDROB_SCORING_DESIGN.md` (frozen design v1)
and cited by section. No logic lives here — only constants. Modules import these;
nothing numeric is hardcoded in module logic (interface_contract.md §11).

Ownership boundary (`shared/config` vs `data/jd_rubric.json`):
  - THIS FILE owns the *numbers*: penalties, bands, bonuses, behavioral weights,
    sub-score tables, honeypot thresholds, clamp caps, multiplier floor.
  - `data/jd_rubric.json` owns the JD *selections / vocabulary*: which nodes are
    nice-to-have, anti-signal detection keywords, the consulting-company list, and
    the logistics target-city sets. `module1_jd_rubric` composes `JDProfile` by
    pairing the vocab/keys from the data file with the penalties/bands defined here.
    => each constant has exactly one home; no number is duplicated across sources.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# §2 — node strength levels (node_strength ∈ {0.0, 0.5, 1.0})
# ---------------------------------------------------------------------------
NODE_STRENGTH_NONE: Final[float] = 0.0
NODE_STRENGTH_WEAK: Final[float] = 0.5     # claimed but unproven (skills/summary, no assessment)
NODE_STRENGTH_STRONG: Final[float] = 1.0   # demonstrated in career_history description / assessment ≥50

# §2 — assessment gates on `skill_assessment_scores` (0..100)
STRONG_ASSESS_MIN: Final[float] = 50.0     # ≥50 → promote a claimed skill to strong
STUFF_ASSESS_MIN: Final[float] = 30.0      # <30 → drop the skill (keyword stuffing)

# §2 — phrase matching: terms this short or shorter match on word boundaries
# (so "rag"/"map"/"ltr" never match inside "storage"/"roadmap"/"alter"); longer
# terms match as substrings so stems ("tokeniz*") tolerate suffixes.
SHORT_TERM_MAX_LEN: Final[int] = 4

# ---------------------------------------------------------------------------
# §1.4 — experience_factor E, keyed on years_of_experience (half-open bands)
#   <3 → 0.70 · 3–5 → 0.90 · 5–9 → 1.00 · 9–12 → 0.95 · >12 → 0.85
# Each tuple is (lo_inclusive, hi_exclusive, factor); last band is open-ended.
# ---------------------------------------------------------------------------
EXPERIENCE_BANDS: Final[tuple[tuple[float, float, float], ...]] = (
    (0.0, 3.0, 0.70),
    (3.0, 5.0, 0.90),
    (5.0, 9.0, 1.00),
    (9.0, 12.0, 0.95),
    (12.0, float("inf"), 0.85),
)

# ---------------------------------------------------------------------------
# §1.5 — ml_depth_factor D, keyed on relevant-ML tenure (ml_years = ml_months/12)
#   ≥4 → 1.10 · 2–<4 → 1.00 · 1–<2 → 0.95 · <1 w/ base>0 → 0.85 · no ML role → 1.00
# The <1 case is base-dependent (pivot vs no-ML), resolved in module3 logic.
# ---------------------------------------------------------------------------
ML_DEPTH_YEARS_HIGH: Final[float] = 4.0
ML_DEPTH_YEARS_SOLID: Final[float] = 2.0
ML_DEPTH_YEARS_SHALLOW: Final[float] = 1.0

ML_DEPTH_FACTOR_HIGH: Final[float] = 1.10     # ml_years ≥ 4 (meets ideal "4–5 yrs in applied ML")
ML_DEPTH_FACTOR_SOLID: Final[float] = 1.00    # 2–<4 (neutral)
ML_DEPTH_FACTOR_SHALLOW: Final[float] = 0.95  # 1–<2 (mild discount)
ML_DEPTH_FACTOR_PIVOT: Final[float] = 0.85    # <1 yr but base>0 (recent pivot / skills-only)
ML_DEPTH_FACTOR_NONE: Final[float] = 1.00     # no ML role (base≈0) — don't double-punish

ML_DEPTH_MIN: Final[float] = 0.85
ML_DEPTH_MAX: Final[float] = 1.10

# ---------------------------------------------------------------------------
# §1.3 — anti-signals → anti_penalty (subtractive; total capped). key → (penalty, is_hard_dq).
# Only "research_only" is a hard DQ (caps base_capability at HARD_DQ_BASE_CEILING).
# Detection vocabulary for each key lives in data/jd_rubric.json.
# ---------------------------------------------------------------------------
ANTI_SIGNAL_PENALTIES: Final[dict[str, tuple[float, bool]]] = {
    "research_only":     (0.25,  True),
    "consulting_only":   (0.125, False),  # soft penalty (employer decorrelated from work content)
    "langchain_only":    (0.20,  False),
    "framework_tutorial":(0.15,  False),
    "title_chasing":     (0.10,  False),
    "no_recent_handson": (0.10,  False),
    "cv_speech_robotics":(0.15,  False),
}
ANTI_PENALTY_CAP: Final[float] = 0.50          # total anti-penalty cap
HARD_DQ_BASE_CEILING: Final[float] = 0.30      # hard_dq caps base_capability at this

# Detection thresholds referenced by §1.3 rules (logic lives in module3).
TITLE_CHASING_MIN_ROLES: Final[int] = 3        # ≥3 short rising-seniority roles
TITLE_CHASING_MAX_DURATION_MONTHS: Final[int] = 18

# ---------------------------------------------------------------------------
# §1.2 — nice-to-have bonus (additive). Which nodes count is in jd_rubric.json.
# ---------------------------------------------------------------------------
NICE_BONUS_PER_ITEM: Final[float] = 0.03
NICE_BONUS_CAP: Final[float] = 0.10

# ---------------------------------------------------------------------------
# §3 — behavioral_raw = Σ W[k]·sub_k  (weights sum to 1.0)
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
# §3.4 — behavioral_multiplier = 0.50 + 0.50·behavioral_raw ∈ [0.50, 1.00]
BEHAVIORAL_MULTIPLIER_FLOOR: Final[float] = 0.50
BEHAVIORAL_MULTIPLIER_SLOPE: Final[float] = 0.50

# §3.1 — recency sub-score: days since last_active vs AS_OF.
#   (max_days_inclusive, score); beyond the last band → RECENCY_DEFAULT.
RECENCY_BANDS: Final[tuple[tuple[float, float], ...]] = (
    (30.0, 1.00),
    (60.0, 0.90),
    (90.0, 0.75),
    (180.0, 0.50),
)
RECENCY_DEFAULT: Final[float] = 0.25

# §3.1 — responsiveness time_factor on avg_response_time_hours.
RESPONSE_TIME_BANDS: Final[tuple[tuple[float, float], ...]] = (
    (24.0, 1.00),
    (72.0, 0.90),
)
RESPONSE_TIME_DEFAULT: Final[float] = 0.80

# §3.1 — open: open_to_work_flag
OPEN_TRUE: Final[float] = 1.0
OPEN_FALSE: Final[float] = 0.4

# §3.1 — neutral fallbacks for missing/sentinel signals (§3.3: absence ≠ negative)
INTERVIEW_NEUTRAL: Final[float] = 0.5   # interview_completion_rate missing
OFFER_NEUTRAL: Final[float] = 0.5       # offer_acceptance_rate == -1 (no history)

# §3.2 — logistics sub-factors -------------------------------------------------
# notice_factor on notice_period_days: (max_days_inclusive, score); beyond → default.
NOTICE_BANDS: Final[tuple[tuple[float, float], ...]] = (
    (30.0, 1.0),
    (60.0, 0.8),
    (90.0, 0.6),
)
NOTICE_DEFAULT: Final[float] = 0.4

# location_factor values (city → bucket membership lives in jd_rubric.json / module4).
LOCATION_OFFICE: Final[float] = 1.00      # Pune / Noida (office cities)
LOCATION_WELCOME: Final[float] = 0.85     # Hyderabad / Mumbai / Delhi NCR (explicitly welcomed)
LOCATION_RELOCATE: Final[float] = 0.85    # willing_to_relocate & country == India
LOCATION_INDIA: Final[float] = 0.55       # in India, not relocating
LOCATION_OUTSIDE: Final[float] = 0.30     # outside India (no visa sponsorship)

# workmode_factor on preferred_work_mode (JD is hybrid Pune/Noida).
WORKMODE_PREFERRED: Final[float] = 1.0    # hybrid / flexible / onsite
WORKMODE_REMOTE: Final[float] = 0.7       # remote

# §3.1 — demand: mean of log-normalized counts, each capped.
DEMAND_SAVED_CAP: Final[float] = 20.0     # saved_by_recruiters_30d
DEMAND_SEARCH_CAP: Final[float] = 500.0   # search_appearance_30d

# ---------------------------------------------------------------------------
# §4 — honeypot detection (H1/H2 only; validated 0.043% pool-wide)
# ---------------------------------------------------------------------------
# H1: count(proficiency ∈ {advanced, expert} AND duration_months == 0) ≥ 3
HONEYPOT_H1_PROFICIENCIES: Final[tuple[str, ...]] = ("advanced", "expert")
HONEYPOT_H1_MIN_COUNT: Final[int] = 3
# H2: Σ career_history.duration_months > years_of_experience·12·MULT + ADD_MONTHS
HONEYPOT_H2_SLACK_MULT: Final[float] = 1.5
HONEYPOT_H2_SLACK_ADD_MONTHS: Final[int] = 12

# ---------------------------------------------------------------------------
# §0 / §5 — output
# ---------------------------------------------------------------------------
SUBMISSION_ROW_COUNT: Final[int] = 100     # exactly 100 ranked rows
SCORE_ROUND_DECIMALS: Final[int] = 6       # score = round(final, 6); sort on rounded score

__all__ = [name for name in dir() if name.isupper()]
