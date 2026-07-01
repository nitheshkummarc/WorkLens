# module7_reasoning

Writes the 1-2 sentence `reasoning` string for each of the top 100. It's a template
filled entirely from the candidate's own fields, so nothing is hallucinated; the
text varies per candidate and the tone follows the rank — strong candidates lead
with strengths, weaker ones lead with the concern.

Each line has the title and years, up to three demonstrated strength areas (the
first with a real evidence phrase), a behavioral note, and one honest concern.

```python
from modules.module7_reasoning import ReasoningGenerator
text = ReasoningGenerator(jd).reason(ranked_entry)
```
