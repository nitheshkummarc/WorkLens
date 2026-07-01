"""CSV submission row model (§6) — output of module8_submission.

The emitted CSV header (exact order) is `candidate_id,rank,score,reasoning`,
UTF-8, header + exactly 100 data rows. Mirrors interface_contract.md §9.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubmissionRow(BaseModel):
    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    rank: int = Field(ge=1, le=100)
    score: float
    reasoning: str              # from module7


__all__ = ["SubmissionRow"]
