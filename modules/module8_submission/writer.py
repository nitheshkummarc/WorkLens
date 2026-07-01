"""CSV serialization (§6) — module8.

Writes the exact submission format: header `candidate_id,rank,score,reasoning`,
UTF-8, then 100 data rows ordered by rank. Scores are written with fixed 6-decimal
formatting (the rounded final), so the file is unambiguous and the non-increasing /
tie-break invariants survive a float round-trip. `csv.writer` quotes any reasoning
containing commas or quotes.
"""

from __future__ import annotations

import csv
from pathlib import Path

from shared.config import scoring
from shared.models.submission import SubmissionRow

HEADER = ["candidate_id", "rank", "score", "reasoning"]


def _fmt_score(score: float) -> str:
    return f"{score:.{scoring.SCORE_ROUND_DECIMALS}f}"


class SubmissionWriter:
    """Serialize ranked rows to the spec CSV."""

    def write(self, rows: list[SubmissionRow], path: Path | str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(rows, key=lambda r: r.rank)
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            for r in ordered:
                writer.writerow([r.candidate_id, r.rank, _fmt_score(r.score), r.reasoning])
        return out


__all__ = ["SubmissionWriter", "HEADER"]
