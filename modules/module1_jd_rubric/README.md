# module1_jd_rubric

**Responsibility (§1).** Build a single `JDProfile` for the Senior AI Engineer role,
once per run, by composing three sources:

- **ontology importances** (`data/ai_capability_ontology.json`) → the 9 required
  capabilities with their node-specific weights;
- **JD selections / vocabulary** (`data/jd_rubric.json`) → nice-to-have nodes,
  anti-signal keys, consulting-company list, logistics target cities;
- **numeric constants** (`shared/config/scoring.py`) → anti-signal penalties +
  hard-DQ flags, experience bands, nice-bonus per-item/cap, the penalty/ceiling caps.

## Output
`JDProfile` (see `shared/models/jd_profile.py`). `required_capabilities` carry both
`importance` (the scoring value) and a display-only `tier` bucket derived from it
(`Critical ≥0.9 · High ≥0.7 · Medium ≥0.5 · Nice <0.5`). The tier is never a
scoring input.

## Notes
- Runs **once** at startup; the immutable result is reused for every candidate
  (one-time-init performance contract, PHASE0 §3c).
- Only `research_only` is a hard DQ — asserted by the smoke check.
- `nice_to_have_nodes` are validated against the ontology node names (typo guard).

## API
```python
from modules.module1_jd_rubric import build_jd_profile
jd = build_jd_profile(nodes, rubric_path)   # nodes from shared.utils.load_ontology
```
