"""Write the submission CSV — module8.

Header candidate_id,rank,score,reasoning (UTF-8), then 100 rows ordered by rank.
Scores use fixed 6-decimal formatting so the non-increasing and tie-break rules
survive a float round-trip. csv.writer quotes any reasoning with commas or quotes.
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
