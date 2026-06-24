# module4_behavioral

**Responsibility (§3).** Turn the 23 `redrob_signals` into a behavioral
*multiplier* on capability — never a driver, never zeroing a strong candidate.

```
behavioral_raw        = Σ W[k]·sub_k          (weights sum to 1.0)
behavioral_multiplier = 0.50 + 0.50·raw  ∈ [0.50, 1.00]
```

| sub-score | W | from |
|---|---|---|
| recency | 0.30 | days since `last_active_date` vs **AS_OF** (banded) |
| responsiveness | 0.25 | `recruiter_response_rate` × time-factor(`avg_response_time_hours`) |
| open | 0.10 | `open_to_work_flag` (1.0 / 0.4) |
| interview | 0.10 | `interview_completion_rate` |
| offer | 0.05 | `offer_acceptance_rate` (−1 → neutral 0.5) |
| logistics | 0.10 | mean(notice, location, workmode) — §3.2 |
| demand | 0.07 | mean(log-norm `saved_by_recruiters_30d` cap 20, `search_appearance_30d` cap 500) |
| trust | 0.03 | fraction of {verified_email, verified_phone, linkedin_connected} |

**Location factor (§3.2):** Pune/Noida → 1.0; Hyderabad/Mumbai/Delhi NCR → 0.85;
else relocate-willing & India → 0.85; else India → 0.55; outside India → 0.30.
City buckets come from `data/jd_rubric.json`.

**Sentinels (§3.3):** `-1` (`offer_acceptance_rate`, `github_activity_score`) and
missing values map to neutral — absence is never a penalty. Recency uses AS_OF
(`2026-05-27`), never the wall clock, so runs are reproducible.

## API
```python
from modules.module4_behavioral import BehavioralScorer
scorer = BehavioralScorer(as_of_date, logistics_buckets)  # buckets = jd_rubric["logistics_buckets"]
behavioral = scorer.score(candidate)
```
