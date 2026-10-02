"""Input and output format settings."""

from __future__ import annotations

# Candidate id format, enforced on input records and on output rows.
CANDIDATE_ID_PATTERN: str = r"^CAND_[0-9]{7}$"

__all__ = ["CANDIDATE_ID_PATTERN"]
