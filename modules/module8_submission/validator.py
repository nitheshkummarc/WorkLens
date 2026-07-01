"""Final-output validation (§6) — module8's HARD GATE.

Independently re-checks the produced rows against every `validate_submission.py`
rule (it does not trust construction), plus two checks the official validator
can't do alone: real pool membership and the "scores not all identical" guard
(spec §6 "model isn't differentiating"). `rank.py` aborts with a non-zero exit if
`validate` returns any error — no invalid CSV is ever accepted as success.
"""

from __future__ import annotations

import re

from shared.config import scoring
from shared.models.submission import SubmissionRow

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")


class SubmissionValidator:
    """Re-validate the top-100 rows; returns a list of human-readable errors."""

    def __init__(self, pool_ids: set[str] | None = None) -> None:
        self.pool_ids = pool_ids or set()

    def validate(self, rows: list[SubmissionRow]) -> list[str]:
        errors: list[str] = []
        expected = scoring.SUBMISSION_ROW_COUNT

        if len(rows) != expected:
            errors.append(f"expected exactly {expected} data rows, found {len(rows)}")

        seen_ids: set[str] = set()
        seen_ranks: set[int] = set()
        for r in rows:
            if not _ID_PATTERN.match(r.candidate_id):
                errors.append(f"candidate_id not CAND_XXXXXXX: {r.candidate_id!r}")
            elif r.candidate_id in seen_ids:
                errors.append(f"duplicate candidate_id: {r.candidate_id}")
            else:
                seen_ids.add(r.candidate_id)
                if self.pool_ids and r.candidate_id not in self.pool_ids:
                    errors.append(f"candidate_id not in pool: {r.candidate_id}")

            if not (1 <= r.rank <= expected):
                errors.append(f"rank out of range 1..{expected}: {r.rank}")
            elif r.rank in seen_ranks:
                errors.append(f"duplicate rank: {r.rank}")
            else:
                seen_ranks.add(r.rank)

            if not isinstance(r.score, float):
                errors.append(f"score is not a float at rank {r.rank}: {r.score!r}")

        missing = set(range(1, expected + 1)) - seen_ranks
        if missing:
            errors.append(f"missing ranks: {sorted(missing)}")

        # score non-increasing by rank + equal-score → candidate_id ascending
        by_rank = sorted(rows, key=lambda r: r.rank)
        for a, b in zip(by_rank, by_rank[1:]):
            if a.score < b.score:
                errors.append(
                    f"score increases with rank: rank {a.rank} ({a.score}) < rank {b.rank} ({b.score})"
                )
            if a.score == b.score and a.candidate_id > b.candidate_id:
                errors.append(
                    f"equal scores at ranks {a.rank}/{b.rank} but ids not ascending: "
                    f"{a.candidate_id} > {b.candidate_id}"
                )

        # spec §6: a model that isn't differentiating sets every score identical
        if rows and len({r.score for r in rows}) == 1:
            errors.append("all scores identical — model is not differentiating")

        # reasoning present (Stage-4: empty reasoning is penalized)
        for r in rows:
            if not r.reasoning.strip():
                errors.append(f"empty reasoning at rank {r.rank}")

        return errors


__all__ = ["SubmissionValidator", "REQUIRED_HEADER"]
