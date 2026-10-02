# module2_capability

Scores a candidate's capability evidence into a `CapabilityProfile`.

Each ontology node gets a strength and a source label:

| Strength | Source | Evidence |
|---|---|---|
| 1.0 | `career` | strong phrase in career history |
| 1.0 | `skill_verified` | advanced/expert skill with assessment ≥ 50, backed by at least a weak phrase in career history |
| 0.5 | `claimed` | strong phrase only in summary, headline or skills, or an assessed skill with no career support |
| 0.5 | `career_weak` | only a weak phrase in career history |
| 0.0 | `none` | no evidence |

Skills with an assessment below 30 are ignored. `base_capability` is the importance-weighted mean of the strengths. `ml_relevant_months` sums the durations of roles matching any phrase of the rubric's `ml_nodes`, capped at the candidate's stated experience.

A match preceded by a negation or comparison cue in the same clause ("lighter weight than ranking systems", "transitioning toward NLP") is ignored.

```python
from modules.module2_capability import CapabilityExtractor
profile = CapabilityExtractor(nodes, jd.ml_nodes).extract(candidate)
```
