"""Output validation: the official validate_submission.py rules, plus pool
membership and a non-identical-scores check."""

from __future__ import annotations

import re

from shared.config import scoring
from shared.config.run_config import CANDIDATE_ID_PATTERN
from shared.models.submission import SubmissionRow

_ID_PATTERN = re.compile(CANDIDATE_ID_PATTERN)


class SubmissionValidator:
    """`validate` returns a list of error messages; empty means valid."""

    def __init__(self, pool_ids: set[str] | None = None,
                 expected_rows: int = scoring.SUBMISSION_ROW_COUNT) -> None:
        self.pool_ids = pool_ids or set()
        self.expected = expected_rows

    def validate(self, rows: list[SubmissionRow]) -> list[str]:
        errors: list[str] = []
        expected = self.expected

        if len(rows) != expected:
            errors.append(f"expected exactly {expected} data rows, found {len(rows)}")

        seen_ids: set[str] = set()
        seen_ranks: set[int] = set()
        for r in rows:
            if not _ID_PATTERN.match(r.candidate_id):
                errors.append(f"candidate_id does not match {CANDIDATE_ID_PATTERN}: {r.candidate_id!r}")
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

        missing = set(range(1, expected + 1)) - seen_ranks
        if missing:
            errors.append(f"missing ranks: {sorted(missing)}")

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

        if rows and len({r.score for r in rows}) == 1:
            errors.append("all scores are identical")

        for r in rows:
            if not r.reasoning.strip():
                errors.append(f"empty reasoning at rank {r.rank}")

        return errors


__all__ = ["SubmissionValidator"]
