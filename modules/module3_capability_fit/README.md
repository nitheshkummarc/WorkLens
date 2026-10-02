# module3_capability_fit

Turns `base_capability` into `capability_fit`:

```
capability_fit = clamp01((min(base, 0.30 if hard_dq) * E * D - anti + nice) / 1.2)
```

- `E`: experience factor (1.0 at 5-9 years)
- `D`: ML-depth factor (0.85-1.10, by years in ML-relevant roles)
- `anti`: anti-signal penalties, capped at 0.50; only `research_only` is a hard DQ
- `nice`: nice-to-have bonus, capped at 0.10
- `1.2`: the largest value the numerator can reach, so top profiles are not clamped together

`anti_signals.py` implements the seven rules using the vocabulary in `JDProfile`. `title_chasing` counts only completed roles; `langchain_only` does not fire when the career shows retrieval or ranking work. `assembler.py` combines everything into a `CapabilityFit`.

```python
from modules.module3_capability_fit import CapabilityFitAssembler
fit = CapabilityFitAssembler(jd).assemble(candidate, capability)
```
