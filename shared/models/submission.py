"""One CSV row — output of module8.

The CSV has header candidate_id,rank,score,reasoning (UTF-8) plus exactly 100 rows.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubmissionRow(BaseModel):
    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    rank: int = Field(ge=1, le=100)
    score: float
    reasoning: str              # from module7


__all__ = ["SubmissionRow"]
