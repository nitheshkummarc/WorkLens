# module6_ranking

Computes `final = 0.0 if honeypot else round(capability_fit * behavioral_multiplier, 6)` and keeps the top K (default 100) with a bounded min-heap over the stream: O(N log K) time, no full sort.

- The heap carries each candidate's scoring objects, so module7 needs no second pass.
- Scores are rounded before entering the heap, so eviction and final order use the value written to the CSV.
- Ties are broken by candidate_id ascending, in both eviction and the final sort, for any id format.

```python
from modules.module6_ranking import TopKRanker
ranker = TopKRanker(k=100)
ranker.add(candidate, capability, fit, behavioral, honeypot)   # per candidate
entries = ranker.finalize()                                    # ranked top 100
```
