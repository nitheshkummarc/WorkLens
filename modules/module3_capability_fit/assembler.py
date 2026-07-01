"""Assemble the CapabilityFit — module3.

Combines module2's base_capability with the anti-signal penalty, experience factor,
ML-depth factor, and nice-to-have bonus:

    capability_fit = clamp01( min(base, 0.30 if hard_dq) * E * D - anti + nice )

ml_depth_factor is a multiplier in [0.85, 1.10], so it only re-orders candidates
who already have a real base; setting it to 1.0 turns it off.
"""

from __future__ import annotations

from shared.config import scoring
from shared.models.candidate import Candidate
from shared.models.capability import CapabilityProfile
from shared.models.capability_fit import CapabilityFit
from shared.models.jd_profile import JDProfile

from .anti_signals import AntiSignalDetector


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class CapabilityFitAssembler:
    """Turn a CapabilityProfile into a CapabilityFit; setup done once at init."""

    def __init__(self, jd_profile: JDProfile, anti_signal_vocab: dict) -> None:
        self.jd = jd_profile
        self.detector = AntiSignalDetector(jd_profile, anti_signal_vocab)
        self.bands = jd_profile.experience_bands
        self.nice_nodes = set(jd_profile.nice_to_have_nodes)
        self.hard_dq_ceiling = jd_profile.hard_dq_base_ceiling

    # -- experience factor ---------------------------------------------------
    def _experience_factor(self, years: float) -> float:
        for band in self.bands:
            if band.lo <= years < band.hi:
                return band.factor
        return self.bands[-1].factor

    # -- ML-depth factor -----------------------------------------------------
    @staticmethod
    def _ml_depth_factor(ml_months: int, base_capability: float) -> float:
        years = ml_months / 12.0
        if years >= scoring.ML_DEPTH_YEARS_HIGH:
            return scoring.ML_DEPTH_FACTOR_HIGH
        if years >= scoring.ML_DEPTH_YEARS_SOLID:
            return scoring.ML_DEPTH_FACTOR_SOLID
        if years >= scoring.ML_DEPTH_YEARS_SHALLOW:
            return scoring.ML_DEPTH_FACTOR_SHALLOW
        # under 1 year of ML tenure
        if base_capability > 0:
            return scoring.ML_DEPTH_FACTOR_PIVOT   # AI signal but almost no ML career (recent pivot)
        return scoring.ML_DEPTH_FACTOR_NONE        # no ML at all - stay neutral, don't double-punish

    # -- nice-to-have bonus --------------------------------------------------
    def _nice(self, capability: CapabilityProfile) -> tuple[list[str], float]:
        items = [
            ev.node for ev in capability.node_strengths
            if ev.node in self.nice_nodes and ev.strength > 0
        ]
        bonus = min(len(items) * self.jd.nice_bonus_per_item, self.jd.nice_bonus_cap)
        return items, bonus

    # -- public --------------------------------------------------------------
    def assemble(self, candidate: Candidate, capability: CapabilityProfile) -> CapabilityFit:
        fired, anti_penalty, hard_dq = self.detector.detect(candidate, capability)

        base = capability.base_capability
        effective_base = min(base, self.hard_dq_ceiling) if hard_dq else base
        exp = self._experience_factor(candidate.profile.years_of_experience)
        depth = self._ml_depth_factor(capability.ml_relevant_months, base)
        nice_items, nice_bonus = self._nice(capability)

        fit = _clamp01(effective_base * exp * depth - anti_penalty + nice_bonus)

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
