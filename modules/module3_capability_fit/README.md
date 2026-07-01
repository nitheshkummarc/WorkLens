# module3_capability_fit

Turns `base_capability` into `capability_fit`:

```
capability_fit = clamp01( min(base, 0.30 if hard_dq) * E * D - anti + nice )
```

- `E` — experience factor (peaks at 5-9 years)
- `D` — ML-depth factor (0.85-1.10, by years in ML roles)
- `anti` — anti-signal penalties (only research-only is a hard DQ)
- `nice` — nice-to-have bonus (capped)

`anti_signals.py` does the detection (keywords from `data/jd_rubric.json`);
`assembler.py` combines everything into the `CapabilityFit`.
