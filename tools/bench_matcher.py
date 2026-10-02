"""Benchmark module2 against a reference implementation of the same rules.

The reference scans the joined, lower-cased texts with one compiled regex per
phrase, as the original implementation did, and applies the same negation rule
to each regex match. The current CapabilityExtractor uses str.find with a
cached per-part PhraseIndex. The script checks that both produce identical
CapabilityProfiles, then reports the timings.

Usage:
    python tools/bench_matcher.py --candidates ./candidates.jsonl
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.config import paths, scoring
from shared.models.capability import CapabilityProfile, NodeEvidence
from shared.utils.jsonl_reader import CandidateReader
from shared.utils.ontology_loader import load_ontology
from shared.utils.phrase_matcher import _negated
from shared.utils.text_fields import claimed_text, demonstrated_text
from modules.module1_jd_rubric import build_jd_profile
from modules.module2_capability import CapabilityExtractor


def regex_pattern(phrase: str) -> re.Pattern[str]:
    """Reference regex for one phrase under the PhraseGroup rules, without negation.

    Matches lower-cased text, like PhraseGroup.
    """
    stem = phrase.endswith("*")
    core = re.escape((phrase[:-1] if stem else phrase).lower())
    bounded = not stem and len(phrase) <= scoring.SHORT_TERM_MAX_LEN
    return re.compile(rf"\b{core}\b" if bounded else rf"\b{core}")


class ReferenceExtractor:
    """Same rules as CapabilityExtractor; regex over joined text, no caching."""

    def __init__(self, nodes, ml_nodes) -> None:
        self.nodes = nodes
        self.importance_sum = sum(n.importance for n in nodes)
        self.patterns = {p: regex_pattern(p) for n in nodes for p in n.strong_phrases + n.weak_phrases}
        self.ml_phrases = tuple(p for n in nodes if n.name in ml_nodes
                                for p in n.strong_phrases + n.weak_phrases)

    def _found(self, phrase, text):
        return any(not _negated(text, m.start()) for m in self.patterns[phrase].finditer(text))

    def _first(self, phrases, text):
        return next((p for p in phrases if self._found(p, text)), None)

    def extract(self, c) -> CapabilityProfile:
        assessment = c.redrob_signals.skill_assessment_scores
        kept = [s for s in c.skills
                if not (s.name in assessment and assessment[s.name] < scoring.STUFF_ASSESS_MIN)]
        demo = demonstrated_text(c).lower()
        claimed = claimed_text(c, kept).lower()
        verified = [s.name for s in kept if s.proficiency in ("advanced", "expert")
                    and assessment.get(s.name, -1.0) >= scoring.STRONG_ASSESS_MIN]
        evidences, weighted = [], 0.0
        for node in self.nodes:
            ev = None
            if (p := self._first(node.strong_phrases, demo)) is not None:
                ev = NodeEvidence(node=node.name, strength=1.0, source="career", evidence_phrase=p)
            skill = next((name for name in verified
                          if self._first(node.strong_phrases + node.weak_phrases, name.lower())), None)
            supported = self._first(node.weak_phrases, demo) is not None
            if ev is None and skill is not None and supported:
                ev = NodeEvidence(node=node.name, strength=1.0, source="skill_verified",
                                  evidence_phrase=skill)
            if ev is None and (p := self._first(node.strong_phrases, claimed) or skill) is not None:
                ev = NodeEvidence(node=node.name, strength=0.5, source="claimed", evidence_phrase=p)
            if ev is None and (p := self._first(node.weak_phrases, demo)) is not None:
                ev = NodeEvidence(node=node.name, strength=0.5, source="career_weak", evidence_phrase=p)
            if ev is None:
                ev = NodeEvidence(node=node.name, strength=0.0, source="none")
            evidences.append(ev)
            weighted += node.importance * ev.strength
        total = sum(e.duration_months for e in c.career_history
                    if self._first(self.ml_phrases, f"{e.title}\n{e.description}".lower()) is not None)
        return CapabilityProfile(
            candidate_id=c.candidate_id, node_strengths=evidences,
            base_capability=weighted / self.importance_sum,
            ml_relevant_months=min(total, round(c.profile.years_of_experience * 12)),
        )


def _time(extractor, candidates):
    start = time.perf_counter()
    profiles = [extractor.extract(c) for c in candidates]
    return time.perf_counter() - start, profiles


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--candidates", required=True, type=Path)
    p.add_argument("--sample", type=int, default=10_000, help="first N candidates")
    args = p.parse_args()

    candidates = list(itertools.islice(CandidateReader(args.candidates), args.sample))
    nodes = load_ontology(paths.ONTOLOGY_PATH)
    ml_nodes = build_jd_profile(nodes, paths.JD_RUBRIC_PATH).ml_nodes

    ref_s, ref_out = _time(ReferenceExtractor(nodes, ml_nodes), candidates)
    cur_s, cur_out = _time(CapabilityExtractor(nodes, ml_nodes), candidates)
    identical = [x.model_dump() for x in ref_out] == [x.model_dump() for x in cur_out]

    print(f"candidates={len(candidates)}")
    print(f"reference (regex, joined text)   {ref_s:6.2f}s")
    print(f"current (str.find, cached parts) {cur_s:6.2f}s")
    print(f"speed-up {ref_s / cur_s:.1f}x   identical output: {identical}")
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
