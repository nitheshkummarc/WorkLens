# module3_capability_fit

**Responsibility (§1 + §0).** Adjust module2's `base_capability` into the final
`capability_fit` by applying the JD rubric:

```
capability_fit = clamp01( min(base, 0.30 if hard_dq) · E · D − anti_penalty + nice_bonus )
```

| factor | source | §ref |
|---|---|---|
| `anti_penalty`, `hard_dq` | `AntiSignalDetector` (7 rules) | §1.3 |
| `experience_factor` (E) | `years_of_experience` → bands | §1.4 |
| `ml_depth_factor` (D ∈ [0.85,1.10]) | `ml_relevant_months` → bands (base-aware <1y case) | §1.5 |
| `nice_bonus` | nice-to-have nodes present × 0.03, cap 0.10 | §1.2 |

## Anti-signals (`anti_signals.py`)
Deterministic, vocabulary-driven (terms from `data/jd_rubric.json`, penalties from
the `JDProfile`). Only `research_only` is a **hard DQ** (caps base at 0.30);
`consulting_only` is a soft −0.125. Detections:
- **research_only** — research term in titles & no production term anywhere
- **consulting_only** — every employer is a consulting company
- **langchain_only** — LLM-wrapper terms but no pre-LLM ML evidence
- **framework_tutorial** — tutorial terms & no demonstrated-strong node
- **title_chasing** — ≥3 roles under 18 months
- **no_recent_handson** — senior title & no production term in current role
- **cv_speech_robotics** — vision/speech/robotics & zero retrieval/NLP/IR (N1/N3/N6) strength

Total penalty is capped (0.50). `ml_depth_factor` multiplies, so D=1.0 reproduces v1.

## API
```python
from modules.module3_capability_fit import CapabilityFitAssembler
assembler = CapabilityFitAssembler(jd_profile, anti_signal_vocab)  # vocab = jd_rubric["anti_signal_vocab"]
fit = assembler.assemble(candidate, capability_profile)
```
