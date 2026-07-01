"""Honeypot analysis — output of module5.

A honeypot forces the final score to 0.0 in module6. Consumed by module6 and
module7 (reasoning).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class HoneypotAnalysis(BaseModel):
    candidate_id: str
    is_honeypot: bool
    rule_fired: Optional[Literal["H1", "H2"]] = None   # H1 expert-but-unused, H2 tenure>life
    evidence: Optional[str] = None                     # human-readable trigger detail


__all__ = ["HoneypotAnalysis"]
