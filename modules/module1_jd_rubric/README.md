# module1_jd_rubric

Builds the `JDProfile` used for the whole run from the ontology importances, the role vocabulary in `data/jd_rubric.json`, and the constants in `shared/config/scoring.py`.

- Lower-cases all vocabulary once.
- Marks nodes with importance ≥ 0.9 as critical.
- Raises `ValueError` if the rubric names an unknown ontology node, an anti-signal without a penalty, or is missing a key. `rank.py` reports this and exits with code 2.

```python
from modules.module1_jd_rubric import build_jd_profile
jd = build_jd_profile(nodes, "data/jd_rubric.json")
```
