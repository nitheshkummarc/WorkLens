"""Assemble `CapabilityFit` (§1 adjustments + §0 capability_fit) — module3.

Combines module2's `base_capability` with the §1.3 anti-penalty, §1.4 experience
factor, §1.5 ML-depth factor, and §1.2 nice-to-have bonus into the frozen
capability_fit equation:

    capability_fit = clamp01( min(base, 0.30 if hard_dq) · E · D − anti + nice )

`ml_depth_factor` is multiplicative (∈ [0.85, 1.10]) so it only re-orders
already-capable candidates; setting it to 1.0 reproduces v1.
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

    # -- §1.4 ----------------------------------------------------------------
    def _experience_factor(self, years: float) -> float:
        for band in self.bands:
            if band.lo <= years < band.hi:
                return band.factor
        return self.bands[-1].factor

    # -- §1.5 ----------------------------------------------------------------
    @staticmethod
    def _ml_depth_factor(ml_months: int, base_capability: float) -> float:
        years = ml_months / 12.0
        if years >= scoring.ML_DEPTH_YEARS_HIGH:
            return scoring.ML_DEPTH_FACTOR_HIGH
        if years >= scoring.ML_DEPTH_YEARS_SOLID:
            return scoring.ML_DEPTH_FACTOR_SOLID
        if years >= scoring.ML_DEPTH_YEARS_SHALLOW:
            return scoring.ML_DEPTH_FACTOR_SHALLOW
        # < 1 year of ML tenure
        if base_capability > 0:
            return scoring.ML_DEPTH_FACTOR_PIVOT   # AI signal but ~no ML career → recent pivot
        return scoring.ML_DEPTH_FACTOR_NONE        # no ML at all → neutral (don't double-punish)

    # -- §1.2 ----------------------------------------------------------------
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
