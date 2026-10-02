"""Capability evidence per ontology node.

Node strength, first rule that applies:

  1.0  career          strong phrase in career history
  1.0  skill_verified  advanced/expert skill matching any node phrase, assessment >= 50,
                       and a weak phrase for the node in career history
  0.5  claimed         strong phrase in summary, headline or skills, or a verified
                       skill without career support
  0.5  career_weak     weak phrase in career history only
  0.0  none

Skills assessed below 30 are dropped first. ml_relevant_months sums roles that
match any phrase of the rubric's ml_nodes, capped at stated experience.

Text is matched per part (title, description, summary, skill name) through a
cached PhraseIndex; repeated parts are not rescanned.
"""

from __future__ import annotations

from shared.config import scoring
from shared.models.candidate import Candidate, Skill
from shared.models.capability import CapabilityProfile, NodeEvidence
from shared.models.ontology import OntologyNode
from shared.utils.phrase_matcher import PhraseIndex
from shared.utils.text_fields import claimed_parts, demonstrated_parts

_STRONG_PROFICIENCIES = ("advanced", "expert")


def _first_in(phrases: tuple[str, ...], found: frozenset[str]) -> str | None:
    for phrase in phrases:
        if phrase in found:
            return phrase
    return None


class CapabilityExtractor:
    """Build a CapabilityProfile per candidate."""

    def __init__(self, nodes: list[OntologyNode], ml_nodes: list[str]) -> None:
        self.nodes = nodes
        self.importance_sum = sum(n.importance for n in nodes)
        self.index = PhraseIndex(tuple(p for n in nodes for p in n.strong_phrases + n.weak_phrases))
        ml = set(ml_nodes)
        self.ml_phrases = frozenset(
            p for n in nodes if n.name in ml for p in n.strong_phrases + n.weak_phrases
        )
        self.node_phrases = {n.name: frozenset(n.strong_phrases + n.weak_phrases) for n in nodes}

    def _score_node(
        self,
        node: OntologyNode,
        demo: frozenset[str],
        claimed: frozenset[str],
        verified: list[tuple[str, frozenset[str]]],
    ) -> NodeEvidence:
        phrase = _first_in(node.strong_phrases, demo)
        if phrase is not None:
            return NodeEvidence(node=node.name, strength=scoring.NODE_STRENGTH_STRONG,
                                source="career", evidence_phrase=phrase)

        node_phrases = self.node_phrases[node.name]
        skill = next((name for name, found in verified if not found.isdisjoint(node_phrases)), None)
        weak_career = _first_in(node.weak_phrases, demo)
        if skill is not None and weak_career is not None:
            return NodeEvidence(node=node.name, strength=scoring.NODE_STRENGTH_STRONG,
                                source="skill_verified", evidence_phrase=skill)

        phrase = _first_in(node.strong_phrases, claimed) or skill
        if phrase is not None:
            return NodeEvidence(node=node.name, strength=scoring.NODE_STRENGTH_WEAK,
                                source="claimed", evidence_phrase=phrase)

        if weak_career is not None:
            return NodeEvidence(node=node.name, strength=scoring.NODE_STRENGTH_WEAK,
                                source="career_weak", evidence_phrase=weak_career)

        return NodeEvidence(node=node.name, strength=scoring.NODE_STRENGTH_NONE,
                            source="none", evidence_phrase=None)

    def _ml_relevant_months(self, candidate: Candidate) -> int:
        match = self.index.matches_any_part
        total = sum(
            entry.duration_months
            for entry in candidate.career_history
            if not match((entry.title, entry.description)).isdisjoint(self.ml_phrases)
        )
        return min(total, round(candidate.profile.years_of_experience * 12))

    def _verified_skills(self, skills: list[Skill], assessment: dict[str, float]):
        """(name, phrases found in name) for advanced/expert skills assessed >= 50."""
        return [
            (s.name, self.index.matches(s.name))
            for s in skills
            if s.proficiency in _STRONG_PROFICIENCIES
            and assessment.get(s.name, -1.0) >= scoring.STRONG_ASSESS_MIN
        ]

    def extract(self, candidate: Candidate) -> CapabilityProfile:
        assessment = candidate.redrob_signals.skill_assessment_scores
        kept_skills = [
            s for s in candidate.skills
            if not (s.name in assessment and assessment[s.name] < scoring.STUFF_ASSESS_MIN)
        ]
        demo = self.index.matches_any_part(demonstrated_parts(candidate))
        claimed = self.index.matches_any_part(claimed_parts(candidate, kept_skills))
        verified = self._verified_skills(kept_skills, assessment)

        evidences: list[NodeEvidence] = []
        weighted = 0.0
        for node in self.nodes:
            ev = self._score_node(node, demo, claimed, verified)
            evidences.append(ev)
            weighted += node.importance * ev.strength

        base = weighted / self.importance_sum if self.importance_sum else 0.0
        return CapabilityProfile(
            candidate_id=candidate.candidate_id,
            node_strengths=evidences,
            base_capability=base,
            ml_relevant_months=self._ml_relevant_months(candidate),
        )


__all__ = ["CapabilityExtractor"]
