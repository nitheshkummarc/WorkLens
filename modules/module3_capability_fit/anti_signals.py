"""Anti-signal detection.

  research_only       research title, no production term in career text (hard DQ)
  consulting_only     every employer is a listed consulting firm
  langchain_only      LLM-wrapper terms, no earlier-ML terms and no retrieval/ranking
                      career evidence
  framework_tutorial  tutorial terms anywhere, no strong phrase in career history
  title_chasing       >= 3 completed roles under 18 months (current role excluded)
  no_recent_handson   senior current title, no production term in current role
  cv_speech_robotics  vision/speech terms, no evidence for the IR/NLP nodes
"""

from __future__ import annotations

from shared.config import scoring
from shared.models.candidate import Candidate
from shared.models.capability import CapabilityProfile
from shared.models.jd_profile import JDProfile
from shared.utils.phrase_matcher import PhraseGroup
from shared.utils.text_fields import claimed_text, demonstrated_text


class AntiSignalDetector:
    """Return (fired keys, capped penalty, hard_dq) for a candidate."""

    def __init__(self, jd_profile: JDProfile) -> None:
        vocab = jd_profile.anti_signal_vocab
        self.rules = {a.key: a for a in jd_profile.anti_signals}
        self.cap = jd_profile.anti_penalty_cap
        self.consulting = PhraseGroup(jd_profile.consulting_companies)
        self.research = PhraseGroup(vocab.research_terms)
        self.production = PhraseGroup(vocab.production_terms)
        self.llm_wrapper = PhraseGroup(vocab.llm_wrapper_terms)
        self.pre_llm_ml = PhraseGroup(vocab.pre_llm_ml_terms)
        self.tutorial = PhraseGroup(vocab.tutorial_terms)
        self.senior_titles = PhraseGroup(vocab.senior_titles)
        self.cv_domain = PhraseGroup(vocab.cv_domain_terms)
        self.ir_nlp_nodes = frozenset(vocab.ir_nlp_nodes)
        self.retrieval_nodes = frozenset(vocab.retrieval_nodes)

    def _research_only(self, titles: str, demo: str) -> bool:
        return self.research.any_match(titles) and not self.production.any_match(demo)

    def _consulting_only(self, companies: list[str]) -> bool:
        return bool(companies) and all(self.consulting.any_match(c) for c in companies)

    def _langchain_only(self, demo: str, capability: CapabilityProfile) -> bool:
        if not self.llm_wrapper.any_match(demo) or self.pre_llm_ml.any_match(demo):
            return False
        return not any(
            ev.source == "career" and ev.node in self.retrieval_nodes
            for ev in capability.node_strengths
        )

    def _framework_tutorial(self, demo: str, claimed: str, has_demonstrated_strong: bool) -> bool:
        mentions = self.tutorial.any_match(demo) or self.tutorial.any_match(claimed)
        return mentions and not has_demonstrated_strong

    @staticmethod
    def _title_chasing(candidate: Candidate) -> bool:
        short_completed = sum(
            1 for e in candidate.career_history
            if not e.is_current and e.duration_months < scoring.TITLE_CHASING_MAX_DURATION_MONTHS
        )
        return short_completed >= scoring.TITLE_CHASING_MIN_ROLES

    def _no_recent_handson(self, current_title: str, current_desc: str) -> bool:
        return self.senior_titles.any_match(current_title) and not self.production.any_match(current_desc)

    def _cv_speech_robotics(self, demo: str, capability: CapabilityProfile) -> bool:
        if not self.cv_domain.any_match(demo):
            return False
        return all(
            ev.strength == scoring.NODE_STRENGTH_NONE
            for ev in capability.node_strengths
            if ev.node in self.ir_nlp_nodes
        )

    def detect(
        self, candidate: Candidate, capability: CapabilityProfile
    ) -> tuple[list[str], float, bool]:
        history = candidate.career_history
        demo = demonstrated_text(candidate).lower()
        claimed = claimed_text(candidate, candidate.skills).lower()
        titles = "\n".join([candidate.profile.current_title] + [e.title for e in history]).lower()
        companies = [e.company.lower() for e in history]
        current_desc = "\n".join(e.description for e in history if e.is_current).lower()
        has_demonstrated_strong = any(ev.source == "career" for ev in capability.node_strengths)

        checks = {
            "research_only": self._research_only(titles, demo),
            "consulting_only": self._consulting_only(companies),
            "langchain_only": self._langchain_only(demo, capability),
            "framework_tutorial": self._framework_tutorial(demo, claimed, has_demonstrated_strong),
            "title_chasing": self._title_chasing(candidate),
            "no_recent_handson": self._no_recent_handson(
                candidate.profile.current_title.lower(), current_desc),
            "cv_speech_robotics": self._cv_speech_robotics(demo, capability),
        }

        fired = [key for key, hit in checks.items() if hit and key in self.rules]
        penalty = min(sum(self.rules[key].penalty for key in fired), self.cap)
        hard_dq = any(self.rules[key].is_hard_dq for key in fired)
        return fired, penalty, hard_dq


__all__ = ["AntiSignalDetector"]
