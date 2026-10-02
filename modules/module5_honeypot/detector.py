"""Honeypot detection for internally impossible profiles (final score 0).

  H1  >= 3 skills at advanced/expert with duration_months == 0
  H2  total career months > years_of_experience * 12 * 1.5 + 12
"""

from __future__ import annotations

from typing import Optional

from shared.config import scoring
from shared.models.candidate import Candidate
from shared.models.honeypot import HoneypotAnalysis


class HoneypotDetector:
    """Apply rules H1 and H2. H1 is checked first."""

    def detect(self, candidate: Candidate) -> HoneypotAnalysis:
        for rule, check in (("H1", self._h1), ("H2", self._h2)):
            evidence = check(candidate)
            if evidence is not None:
                return HoneypotAnalysis(candidate_id=candidate.candidate_id,
                                        is_honeypot=True, rule_fired=rule, evidence=evidence)
        return HoneypotAnalysis(candidate_id=candidate.candidate_id, is_honeypot=False)

    @staticmethod
    def _h1(candidate: Candidate) -> Optional[str]:
        unused = [
            s for s in candidate.skills
            if s.proficiency in scoring.HONEYPOT_H1_PROFICIENCIES and s.duration_months == 0
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
            return (f"career tenure of {total} months exceeds the plausible {limit:.0f} months "
                    f"for {yoe:g} years of stated experience")
        return None


__all__ = ["HoneypotDetector"]
