"""Honeypot analysis model (§4) — output of module5_honeypot.

Sole owner of `is_honeypot`. Consumed by module6 (forces final to 0.0) and
module7 (reasoning). Mirrors interface_contract.md §7.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class HoneypotAnalysis(BaseModel):
    candidate_id: str
    is_honeypot: bool
    rule_fired: Optional[Literal["H1", "H2"]] = None   # H1 expert-0-duration · H2 tenure>life
    evidence: Optional[str] = None                     # human-readable trigger detail


__all__ = ["HoneypotAnalysis"]
