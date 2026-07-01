# module4_behavioral

Turns the 23 `redrob_signals` into a `behavioral_multiplier` in [0.5, 1.0]:

```
multiplier = 0.50 + 0.50 * (weighted sum of 8 sub-scores)
```

Sub-scores: recency, responsiveness, open-to-work, interview, offer, logistics,
demand, trust. Behaviour only rescales capability — a stale, unresponsive candidate
is halved, not dropped. Recency is measured against the AS_OF date, not the clock,
and `-1`/missing signals count as neutral.
