"""Final score and streaming top-K selection.

final = 0.0 if honeypot else round(capability_fit * behavioral_multiplier, 6)

Heap entries are (score, _Descending(candidate_id), payload...). On equal
scores the larger id compares smaller and is evicted first, matching the
score-desc / id-asc order for any id format. Ids are unique (the reader drops
duplicates), so payloads are never compared.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from shared.config import scoring
from shared.models.behavioral import BehavioralProfile
from shared.models.candidate import Candidate
from shared.models.capability import CapabilityProfile
from shared.models.capability_fit import CapabilityFit
from shared.models.honeypot import HoneypotAnalysis


@dataclass(frozen=True)
class RankedEntry:
    """A retained candidate and its scoring objects."""

    rank: int
    score: float
    candidate: Candidate
    capability: CapabilityProfile
    fit: CapabilityFit
    behavioral: BehavioralProfile
    honeypot: HoneypotAnalysis


class _Descending:
    """String key with reversed ordering, for the heap tie-break."""

    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value

    def __lt__(self, other: "_Descending") -> bool:
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Descending) and self.value == other.value


def final_score(fit: CapabilityFit, behavioral: BehavioralProfile, honeypot: HoneypotAnalysis) -> float:
    """Rounded final score; 0.0 for a honeypot."""
    if honeypot.is_honeypot:
        return 0.0
    return round(fit.capability_fit * behavioral.behavioral_multiplier,
                 scoring.SCORE_ROUND_DECIMALS)


class TopKRanker:
    """Keep the K highest-scoring candidates from a stream."""

    def __init__(self, k: int = scoring.SUBMISSION_ROW_COUNT) -> None:
        self.k = k
        self._heap: list[tuple] = []

    def add(
        self,
        candidate: Candidate,
        capability: CapabilityProfile,
        fit: CapabilityFit,
        behavioral: BehavioralProfile,
        honeypot: HoneypotAnalysis,
    ) -> None:
        score = final_score(fit, behavioral, honeypot)
        elem = (score, _Descending(candidate.candidate_id),
                candidate, capability, fit, behavioral, honeypot)
        if len(self._heap) < self.k:
            heapq.heappush(self._heap, elem)
        else:
            heapq.heappushpop(self._heap, elem)

    def finalize(self) -> list[RankedEntry]:
        """Return the retained candidates ordered by score desc, candidate_id asc."""
        ordered = sorted(self._heap, key=lambda e: (-e[0], e[2].candidate_id))
        return [
            RankedEntry(rank=rank, score=e[0], candidate=e[2], capability=e[3],
                        fit=e[4], behavioral=e[5], honeypot=e[6])
            for rank, e in enumerate(ordered, start=1)
        ]


__all__ = ["TopKRanker", "RankedEntry", "final_score"]
