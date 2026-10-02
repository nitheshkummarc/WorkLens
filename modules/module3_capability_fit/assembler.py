"""capability_fit = clamp01((effective_base * E * D - anti_penalty + nice_bonus) / fit_max)

effective_base is base_capability, capped at HARD_DQ_BASE_CEILING on a hard DQ.
E: experience factor. D: ML-depth factor. fit_max is the largest value the
numerator can reach (max E * ML_DEPTH_FACTOR_HIGH + nice_bonus_cap), so the
strongest profiles are not clamped to the same score.
"""

from __future__ import annotations

from shared.config import scoring
from shared.models.candidate import Candidate
from shared.models.capability import CapabilityProfile
from shared.models.capability_fit import CapabilityFit
from shared.models.jd_profile import JDProfile
from shared.utils.numeric import clamp01

from .anti_signals import AntiSignalDetector


class CapabilityFitAssembler:
    """Turn a CapabilityProfile into a CapabilityFit."""

    def __init__(self, jd_profile: JDProfile) -> None:
        self.jd = jd_profile
        self.detector = AntiSignalDetector(jd_profile)
        self.bands = jd_profile.experience_bands
        self.nice_nodes = set(jd_profile.nice_to_have_nodes)
        self.fit_max = (max(b.factor for b in self.bands) * scoring.ML_DEPTH_FACTOR_HIGH
                        + jd_profile.nice_bonus_cap)

    def _experience_factor(self, years: float) -> float:
        for band in self.bands:
            if band.lo <= years < band.hi:
                return band.factor
        return self.bands[-1].factor

    @staticmethod
    def _ml_depth_factor(ml_months: int, base_capability: float) -> float:
        years = ml_months / 12.0
        if years >= scoring.ML_DEPTH_YEARS_HIGH:
            return scoring.ML_DEPTH_FACTOR_HIGH
        if years >= scoring.ML_DEPTH_YEARS_SOLID:
            return scoring.ML_DEPTH_FACTOR_SOLID
        if years >= scoring.ML_DEPTH_YEARS_SHALLOW:
            return scoring.ML_DEPTH_FACTOR_SHALLOW
        if base_capability > 0:
            return scoring.ML_DEPTH_FACTOR_PIVOT
        return scoring.ML_DEPTH_FACTOR_NONE

    def _nice(self, capability: CapabilityProfile) -> tuple[list[str], float]:
        items = [
            ev.node for ev in capability.node_strengths
            if ev.node in self.nice_nodes and ev.strength > 0
        ]
        bonus = min(len(items) * self.jd.nice_bonus_per_item, self.jd.nice_bonus_cap)
        return items, bonus

    def assemble(self, candidate: Candidate, capability: CapabilityProfile) -> CapabilityFit:
        fired, anti_penalty, hard_dq = self.detector.detect(candidate, capability)

        base = capability.base_capability
        effective_base = min(base, self.jd.hard_dq_base_ceiling) if hard_dq else base
        exp = self._experience_factor(candidate.profile.years_of_experience)
        depth = self._ml_depth_factor(capability.ml_relevant_months, base)
        nice_items, nice_bonus = self._nice(capability)

        fit = clamp01((effective_base * exp * depth - anti_penalty + nice_bonus) / self.fit_max)

        return CapabilityFit(
            candidate_id=candidate.candidate_id,
            base_capability=base,
            anti_signals_fired=fired,
            anti_penalty=anti_penalty,
            hard_dq=hard_dq,
            experience_factor=exp,
            ml_depth_factor=depth,
            nice_items=nice_items,
            nice_bonus=nice_bonus,
            capability_fit=fit,
        )


__all__ = ["CapabilityFitAssembler"]
