"""Final score + streaming top-K selection — module6.

final = 0.0 if honeypot else capability_fit * behavioral_multiplier. The top 100
are kept with a bounded min-heap (size 100) over the stream — O(N log K) time,
O(K) memory. It does not collect all 100K scores and full-sort.

Heap element: (final, -candidate_num, Candidate, CapabilityProfile, CapabilityFit,
BehavioralProfile, HoneypotAnalysis) with candidate_num = int(candidate_id[5:]).
The leading (final, -candidate_num) pair is unique, so heapq never compares the
trailing Pydantic objects — carrying them lets module7 run on the retained 100
with no second pass. On a score tie the eviction drops the higher id, so the
smaller id is kept (matching the id-ascending tie-break).

After the stream the retained 100 are sorted by (round(final,6) desc,
candidate_id asc) to assign ranks 1..100, and the emitted score is round(final,6).
This makes the CSV satisfy the validator (non-increasing score; equal score means
id ascending) by construction.
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
from shared.models.ranking import RankedCandidate

_HeapElem = tuple


@dataclass(frozen=True)
class RankedEntry:
    """One retained top-K candidate with its full per-candidate context."""

    rank: int
    score: float                       # round(final, 6)
    final_raw: float                   # unrounded final (for diagnostics)
    candidate: Candidate
    capability: CapabilityProfile
    fit: CapabilityFit
    behavioral: BehavioralProfile
    honeypot: HoneypotAnalysis

    @property
    def ranked_candidate(self) -> RankedCandidate:
        return RankedCandidate(candidate_id=self.candidate.candidate_id, rank=self.rank, score=self.score)


def final_score(fit: CapabilityFit, behavioral: BehavioralProfile, honeypot: HoneypotAnalysis) -> float:
    """Honeypots sink to 0.0; otherwise capability_fit is rescaled by behaviour."""
    if honeypot.is_honeypot:
        return 0.0
    return fit.capability_fit * behavioral.behavioral_multiplier


class TopKRanker:
    """Streaming bounded-heap selector for the top-K candidates by final score."""

    def __init__(self, k: int = scoring.SUBMISSION_ROW_COUNT) -> None:
        self.k = k
        self._heap: list[_HeapElem] = []

    def add(
        self,
        candidate: Candidate,
        capability: CapabilityProfile,
        fit: CapabilityFit,
        behavioral: BehavioralProfile,
        honeypot: HoneypotAnalysis,
    ) -> None:
        final = final_score(fit, behavioral, honeypot)
        num = int(candidate.candidate_id[5:])
        elem = (final, -num, candidate, capability, fit, behavioral, honeypot)
        if len(self._heap) < self.k:
            heapq.heappush(self._heap, elem)
        else:
            # push + pop-smallest in one op; if elem is the smallest it is dropped.
            heapq.heappushpop(self._heap, elem)

    def finalize(self) -> list[RankedEntry]:
        """Sort retained candidates by (rounded final DESC, id ASC); assign ranks."""
        ordered = sorted(
            self._heap,
            key=lambda e: (-round(e[0], scoring.SCORE_ROUND_DECIMALS), e[2].candidate_id),
        )
        entries: list[RankedEntry] = []
        for rank, e in enumerate(ordered, start=1):
            final = e[0]
            entries.append(
                RankedEntry(
                    rank=rank,
                    score=round(final, scoring.SCORE_ROUND_DECIMALS),
                    final_raw=final,
                    candidate=e[2],
                    capability=e[3],
                    fit=e[4],
                    behavioral=e[5],
                    honeypot=e[6],
                )
            )
        return entries

    @property
    def size(self) -> int:
        return len(self._heap)


__all__ = ["TopKRanker", "RankedEntry", "final_score"]
