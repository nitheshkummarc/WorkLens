# module5_honeypot

**Responsibility (§4).** Flag *provably impossible* candidate profiles so module6
can force their final score to 0.0 (relevance tier 0). Two disjoint rules:

| Rule | Fires when | Spec basis |
|---|---|---|
| **H1** expert-but-unused | ≥3 skills at proficiency advanced/expert with `duration_months == 0` | "expert proficiency in skills with 0 years used" |
| **H2** tenure > working life | `Σ career_history.duration_months > years_of_experience·12·1.5 + 12` | "8 years at a company founded 3 years ago" class of impossibility |

H1 takes precedence when both could apply (they are disjoint in practice).

## Why only these two
Validated across the full public 100K pool at **0.043% (43/100,000)** — close to
the spec's expected ~80 and intentionally **under**-flagging (the safe direction:
it cannot trip the >10%-in-top-100 DQ, and any honeypot that slips through still
scores low on capability). An earlier six-rule draft fired on 16.94% of the pool;
the dropped rules were false-positive machines on this independently-sampled
synthetic data. *(Rate is validated on the public pool, not proven on the hidden
ground-truth set.)*

**A keyword-stuffer is NOT a honeypot.** A wrong-title profile with many AI skills
is sunk naturally by §2 (non-ML descriptions → low base_capability + 0.5 unverified
cap) and §1.3 anti-signals — the honeypot floor is reserved for impossibility.

## Output / API
`HoneypotAnalysis` (`shared/models/honeypot.py`): `is_honeypot`, `rule_fired`
(`"H1"`/`"H2"`/None), `evidence` (human-readable trigger).
```python
from modules.module5_honeypot import HoneypotDetector
analysis = HoneypotDetector().detect(candidate)
```

Thresholds (`HONEYPOT_H1_MIN_COUNT`, `HONEYPOT_H2_SLACK_*`) live in
`shared/config/scoring.py`.
