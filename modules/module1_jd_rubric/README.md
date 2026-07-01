# module1_jd_rubric

Builds one `JDProfile` for the run by combining the ontology importances, the JD
selections in `data/jd_rubric.json`, and the constants in `shared/config/scoring.py`.
It runs once at startup and is reused for every candidate.

`tier` (Critical / High / Medium / Nice) is only a display bucket of `importance`;
scoring always uses the node-specific `importance`, never the tier.

```python
from modules.module1_jd_rubric import build_jd_profile
jd = build_jd_profile(nodes, "data/jd_rubric.json")
```
