"""SubmissionRow: one row of the output CSV."""

from __future__ import annotations

from pydantic import BaseModel, Field

from shared.config.run_config import CANDIDATE_ID_PATTERN


class SubmissionRow(BaseModel):
    candidate_id: str = Field(pattern=CANDIDATE_ID_PATTERN)
    rank: int = Field(ge=1)
    score: float
    reasoning: str


__all__ = ["SubmissionRow"]
