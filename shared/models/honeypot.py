"""HoneypotAnalysis, the output of module5."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class HoneypotAnalysis(BaseModel):
    candidate_id: str
    is_honeypot: bool
    rule_fired: Optional[Literal["H1", "H2"]] = None
    evidence: Optional[str] = None


__all__ = ["HoneypotAnalysis"]
