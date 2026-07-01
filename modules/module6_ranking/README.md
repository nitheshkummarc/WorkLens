# module6_ranking

`final = 0.0 if honeypot else capability_fit * behavioral_multiplier`, and selects
the top 100 with a bounded min-heap over the stream — O(N log K) time, O(K) memory,
no full sort. The heap carries each candidate's profile objects, so module7 can
write reasoning with no second pass. Ties are broken by candidate_id ascending, in
both the heap eviction and the final sort, so the CSV satisfies the validator.

```python
from modules.module6_ranking import TopKRanker
ranker = TopKRanker(k=100)
ranker.add(candidate, capability, fit, behavioral, honeypot)   # per candidate
entries = ranker.finalize()                                    # ranked top 100
```
