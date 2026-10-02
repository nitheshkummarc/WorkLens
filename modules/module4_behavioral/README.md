# module4_behavioral

Uses 14 of the 23 `redrob_signals` to compute a `behavioral_multiplier`:

```
multiplier = 0.50 + 0.50 * (weighted sum of 8 sub-scores)
           = 0.50 if unavailable (inactive > 180 days or response rate < 0.10)
           * 0.80 if outside the home country
```

Sub-scores: recency, responsiveness, open to work, interview completion, offer acceptance, logistics, demand, trust.

- Behaviour rescales capability but cannot create it.
- Recency is measured against the run's reference date (the latest `last_active_date` in the input, or `--as-of`), not the clock.
- `offer_acceptance_rate == -1` (no history) is scored as neutral.
- Home country, city lists and preferred work modes come from `JDProfile.logistics`.

```python
from modules.module4_behavioral import BehavioralScorer
profile = BehavioralScorer(jd, as_of).score(candidate)
```
