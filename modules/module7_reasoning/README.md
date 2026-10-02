# module7_reasoning

Writes the one-line `reasoning` for each ranked candidate from a fixed template. Every clause comes from the candidate's own fields or a phrase that matched their profile.

Each line contains:
- title and years of experience;
- up to three capability areas, the first with its evidence phrase;
- applied-ML tenure, when it is four years or more;
- days since last activity and recruiter response rate;
- the most significant gap.

Partial evidence is worded by its source:
- "only self-reported" for evidence found only in the summary, headline or skills;
- "only indirect … in career history" for a generic career phrase, quoting the phrase.

Inactivity or a low response rate is named when it is the gap. When there is no gap the line ends with "No material gap identified." The first half of the list leads with strengths; the second half leads with the main gap. Thresholds are the `REASON_*` constants in `scoring.py`; anti-signal wording comes from the rubric.

```python
from modules.module7_reasoning import ReasoningGenerator
text = ReasoningGenerator(jd, as_of, list_size=100).reason(ranked_entry)
```
