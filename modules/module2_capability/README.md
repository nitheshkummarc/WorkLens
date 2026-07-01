# module2_capability

Scores each candidate's demonstrated capability into a `CapabilityProfile`.

Every ontology node gets a strength:

- **1.0** — a strong phrase in career history, or an assessment-verified skill (>=50)
- **0.5** — a strong phrase only in the skills list, or a weak phrase in career history
- **0.0** — no evidence (or only a weak phrase in the skills list)

These fold into an importance-weighted `base_capability`, plus `ml_relevant_months`
(months spent in ML-relevant roles). Requiring a strong phrase for the 1.0 case is
what keeps keyword-stuffers out of the top without an LLM.

```python
from modules.module2_capability import CapabilityExtractor
profile = CapabilityExtractor(nodes).extract(candidate)
```
