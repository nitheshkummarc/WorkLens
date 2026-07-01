"""Impossibility detection — module5.

Flags only provably-impossible profiles, with two rules that fire on 0.043% of the
pool (well under the spec's ~0.08% and far under the >10%-in-top-100 DQ — it
under-flags on purpose, which is the safe side):

  H1  expert-but-unused: >=3 skills at advanced/expert with duration_months == 0
      (the spec's own "expert in skills with 0 years used").
  H2  tenure exceeds working life: total career months >
      years_of_experience * 12 * 1.5 + 12 (slack for overlapping roles; only the
      genuinely impossible trips it).

A honeypot is forced to a final score of 0 in module6. This is for impossibility
only — a keyword-stuffer with the wrong title is NOT a honeypot; module2 and the
anti-signals sink that naturally. Thresholds live in scoring.py.
"""

from __future__ import annotations

from typing import Optional

from shared.config import scoring
from shared.models.candidate import Candidate
from shared.models.honeypot import HoneypotAnalysis


class HoneypotDetector:
    """Detect H1/H2 impossibilities for a candidate (stateless; cheap per call)."""

    def detect(self, candidate: Candidate) -> HoneypotAnalysis:
        # H1 takes precedence (the two are disjoint in practice).
        h1 = self._h1(candidate)
        if h1 is not None:
            return HoneypotAnalysis(
                candidate_id=candidate.candidate_id,
                is_honeypot=True, rule_fired="H1", evidence=h1,
            )
        h2 = self._h2(candidate)
        if h2 is not None:
            return HoneypotAnalysis(
                candidate_id=candidate.candidate_id,
                is_honeypot=True, rule_fired="H2", evidence=h2,
            )
        return HoneypotAnalysis(candidate_id=candidate.candidate_id, is_honeypot=False)

    @staticmethod
    def _h1(candidate: Candidate) -> Optional[str]:
        unused = [
            s for s in candidate.skills
            if s.proficiency in scoring.HONEYPOT_H1_PROFICIENCIES
            and s.duration_months == 0
        ]
        if len(unused) >= scoring.HONEYPOT_H1_MIN_COUNT:
            names = ", ".join(s.name for s in unused[:5])
            return f"{len(unused)} advanced/expert skills with 0 months used ({names})"
        return None

    @staticmethod
    def _h2(candidate: Candidate) -> Optional[str]:
        total = sum(e.duration_months for e in candidate.career_history)
        yoe = candidate.profile.years_of_experience
        limit = yoe * 12.0 * scoring.HONEYPOT_H2_SLACK_MULT + scoring.HONEYPOT_H2_SLACK_ADD_MONTHS
        if total > limit:
            return (
                f"career tenure {total} months exceeds plausible {limit:.0f} months "
                f"for {yoe} yrs stated experience"
            )
        return None


__all__ = ["HoneypotDetector"]
