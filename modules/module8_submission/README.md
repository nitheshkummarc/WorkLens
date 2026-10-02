# module8_submission

- **`SubmissionValidator`** checks the rows against every rule in the official `validate_submission.py`, plus pool membership and a "scores not all identical" check. Ids are checked against `CANDIDATE_ID_PATTERN`. `rank.py` exits with code 1 and writes nothing if any check fails.
- **`SubmissionWriter`** writes `candidate_id,rank,score,reasoning` (UTF-8): K rows ordered by rank (default 100), scores to six decimals. Reasoning that starts with `=`, `+`, `-` or `@` is prefixed with an apostrophe so spreadsheets do not treat it as a formula.

```python
from modules.module8_submission import SubmissionValidator, SubmissionWriter
errors = SubmissionValidator(pool_ids, expected_rows=100).validate(rows)
if not errors:
    SubmissionWriter().write(rows, out_path)
```
