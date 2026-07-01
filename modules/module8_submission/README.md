# module8_submission

- **`SubmissionValidator`** — re-checks the rows against every rule in the official
  `validate_submission.py`, plus two it can't do alone: pool membership and a
  "scores not all identical" guard. `rank.py` exits non-zero if it finds any error,
  so an invalid CSV is never written.
- **`SubmissionWriter`** — writes `candidate_id,rank,score,reasoning` (UTF-8), 100
  rows ordered by rank, scores at 6 decimals.

```python
from modules.module8_submission import SubmissionValidator, SubmissionWriter
errors = SubmissionValidator(pool_ids).validate(rows)
if not errors:
    SubmissionWriter().write(rows, out_path)
```
