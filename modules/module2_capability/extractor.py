"""Score a candidate's demonstrated capability into a CapabilityProfile.

Gives every ontology node a strength (0, 0.5, or 1.0), then combines them into an
importance-weighted base_capability plus the relevant-ML tenure, in one text pass.

Strength rules (description-primary, assessment-secondary):

  1.0  a strong phrase in demonstrated text (career titles/descriptions), or a
       skill at advanced/expert whose assessment is >= 50.
  0.5  a strong phrase only in claimed text (summary/headline/skills), or a
       weak/ambiguous phrase in demonstrated text.
  0.0  no evidence, or only a weak phrase in claimed text (the stuffer signature).

Requiring a strong phrase for the 1.0 case is what stops vague words like "search"
or "data" in a non-AI description from counting as real AI capability. Skills that
fail the <30 assessment gate are dropped before matching.

Derived structures (importance sum, the N1-N7 ML-phrase set) are built once, so
the per-candidate path does no setup.
"""

from __future__ import annotations

from shared.config import scoring
from shared.models.candidate import Candidate, Skill
from shared.models.capability import CapabilityProfile, NodeEvidence
from shared.models.ontology import OntologyNode
from shared.utils.phrase_matcher import PhraseGroup
from shared.utils.text_fields import (
    career_entry_text,
    claimed_text,
    demonstrated_text,
)

# the genuine applied-ML/AI nodes. N8 (data-eng) and N9 (scale-infra) alone do
# NOT count a role as "applied ML".
_ML_NODE_COUNT = 7  # N1..N7

_STRONG_PROFICIENCIES = ("advanced", "expert")


class CapabilityExtractor:
    """Stateless-per-candidate extractor; derived constants computed once."""

    def __init__(self, nodes: list[OntologyNode]) -> None:
        self.nodes = nodes
        self.importance_sum = sum(n.importance for n in nodes)
        # N1–N7 strong+weak phrases, flattened once, for ML-relevance role tagging.
        self.ml_phrases: tuple[str, ...] = tuple(
            phrase
            for node in nodes[:_ML_NODE_COUNT]
            for phrase in (node.strong_phrases + node.weak_phrases)
        )
        self.ml_group = PhraseGroup(self.ml_phrases)
        self.strong_groups = {
            node.name: PhraseGroup(node.strong_phrases)
            for node in nodes
        }
        self.weak_groups = {
            node.name: PhraseGroup(node.weak_phrases)
            for node in nodes
        }
        self.all_phrase_groups = {
            node.name: PhraseGroup(node.strong_phrases + node.weak_phrases)
            for node in nodes
        }

    # -- node strength -------------------------------------------------------
    def _score_node(
        self,
        node: OntologyNode,
        demo_text: str,
        claimed: str,
        kept_skills: list[Skill],
        assessment: dict[str, float],
    ) -> NodeEvidence:
        # 1.0 — strong phrase demonstrated in career history.
        phrase = self.strong_groups[node.name].first_match(demo_text)
        if phrase is not None:
            return NodeEvidence(node=node.name, strength=1.0,
                                source="career_description", evidence_phrase=phrase)

        # 1.0: a validated skill (advanced/expert with assessment >= 50) matching the node.
        node_phrases = self.all_phrase_groups[node.name]
        for skill in kept_skills:
            if (skill.proficiency in _STRONG_PROFICIENCIES
                    and assessment.get(skill.name, -1.0) >= scoring.STRONG_ASSESS_MIN
                    and node_phrases.any_match(skill.name)):
                return NodeEvidence(node=node.name, strength=1.0,
                                    source="skill_verified", evidence_phrase=skill.name)

        # 0.5 — strong phrase claimed but not demonstrated.
        phrase = self.strong_groups[node.name].first_match(claimed)
        if phrase is not None:
            return NodeEvidence(node=node.name, strength=0.5,
                                source="skill_unverified", evidence_phrase=phrase)

        # 0.5 — weak/ambiguous phrase, but in demonstrated work.
        phrase = self.weak_groups[node.name].first_match(demo_text)
        if phrase is not None:
            return NodeEvidence(node=node.name, strength=0.5,
                                source="career_description", evidence_phrase=phrase)

        # 0.0 — nothing, or only a weak phrase in claimed text (stuffer signature).
        return NodeEvidence(node=node.name, strength=0.0, source="none", evidence_phrase=None)

    # -- ML tenure -----------------------------------------------------------
    def _ml_relevant_months(self, candidate: Candidate) -> int:
        total = 0
        for entry in candidate.career_history:
            if self.ml_group.any_match(career_entry_text(entry)):
                total += entry.duration_months
        return total

    # -- public --------------------------------------------------------------
    def extract(self, candidate: Candidate) -> CapabilityProfile:
        assessment = candidate.redrob_signals.skill_assessment_scores
        kept_skills = [
            s for s in candidate.skills
            if not (s.name in assessment and assessment[s.name] < scoring.STUFF_ASSESS_MIN)
        ]
        demo_text = demonstrated_text(candidate)
        claimed = claimed_text(candidate, kept_skills)

        evidences: list[NodeEvidence] = []
        weighted = 0.0
        for node in self.nodes:
            ev = self._score_node(node, demo_text, claimed, kept_skills, assessment)
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
