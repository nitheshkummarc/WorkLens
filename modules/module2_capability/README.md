# module2_capability

**Responsibility (§2).** For each candidate, assign every ontology node a strength
`∈ {0.0, 0.5, 1.0}`, fold them into an importance-weighted `base_capability`, and
sum the §1.5 relevant-ML tenure (`ml_relevant_months`) — all in one text pass.

## node_strength rule (description-primary, assessment-secondary)
| strength | condition |
|---|---|
| **1.0** | a **strong** phrase in **demonstrated** text (career titles/descriptions), OR a skill at proficiency ≥ advanced with assessment ≥ 50 matching the node |
| **0.5** | a **strong** phrase only in **claimed** text (summary/headline/skills, unvalidated), OR a **weak/ambiguous** phrase in **demonstrated** text |
| **0.0** | no evidence, or only a weak phrase in claimed text (keyword-stuffer signature) |

Skills failing the `<30` assessment gate are dropped before matching.

**Precision lever:** requiring a *strong* phrase for the demonstrated-1.0 case stops
ambiguous terms ("search", "data", "production") in a non-AI description from
registering as full AI capability, while still giving plain-language but
domain-specific phrasing ("recommendation system") full credit. This is what
separates genuine fits from keyword-stuffers without an LLM.

## base_capability
`Σ_n (importance[n] · strength[n]) / Σ_n importance[n]` over all 9 nodes (§0).

## ml_relevant_months (§1.5)
Sum of `duration_months` over career roles whose title/description matches any
strong-or-weak phrase of nodes **N1–N7** (N8 data-eng / N9 scale-infra do not
count as applied ML). Reuses the same scan — no extra pass.

## Output / API
`CapabilityProfile` (`shared/models/capability.py`).
```python
from modules.module2_capability import CapabilityExtractor
extractor = CapabilityExtractor(nodes)   # derived structures precomputed once
profile = extractor.extract(candidate)
```

## Observed on the 50 real sample candidates
`base` min 0.000 / mean 0.182 / max 0.787. A `Recommendation Systems Engineer`
tops at 0.787 (strong N1–N4); a backend/data hybrid lands mid (0.368, N5/N8 strong
from described work, AI skills only weak); a Business Analyst floors at 0.000.
