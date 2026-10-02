"""Submission CSV writer.

Reasoning that starts with = + - or @ is prefixed with an apostrophe so
spreadsheets do not evaluate it.
"""

from __future__ import annotations

import csv
from pathlib import Path

from shared.config import scoring
from shared.models.submission import SubmissionRow

HEADER = ["candidate_id", "rank", "score", "reasoning"]
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _fmt_score(score: float) -> str:
    return f"{score:.{scoring.SCORE_ROUND_DECIMALS}f}"


def _safe_text(text: str) -> str:
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


class SubmissionWriter:
    """Write rows ordered by rank, scores to six decimals."""

    def write(self, rows: list[SubmissionRow], path: Path | str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            for r in sorted(rows, key=lambda r: r.rank):
                writer.writerow([r.candidate_id, r.rank, _fmt_score(r.score), _safe_text(r.reasoning)])
        return out


__all__ = ["SubmissionWriter", "HEADER"]
