"""Anti-signal detection — deterministic, driven by the rubric vocabulary.

Each rule maps a JD "do NOT want" pattern to a key. The penalty and hard-DQ flag
come from the JDProfile (i.e. from scoring.py); the detection keywords come from
jd_rubric.json's anti_signal_vocab and the consulting-company list, so no terms
are hardcoded here. The vocab is lowercased once at init.

Only research_only is a hard DQ. consulting_only is a soft 0.125 penalty (the
employer is decorrelated from the work content in this data). The total penalty is
capped.
"""

from __future__ import annotations

from shared.config import scoring
from shared.models.candidate import Candidate
from shared.models.capability import CapabilityProfile
from shared.models.jd_profile import JDProfile
from shared.utils.text_fields import demonstrated_text


def _lower_tuple(values) -> tuple[str, ...]:
    return tuple(v.lower() for v in values)


def _any_in(terms: tuple[str, ...], text: str) -> bool:
    return any(term in text for term in terms)


class AntiSignalDetector:
    """Detect the anti-signals for a candidate; returns fired keys + penalty."""

    def __init__(self, jd_profile: JDProfile, anti_signal_vocab: dict) -> None:
        self.rules = {a.key: a for a in jd_profile.anti_signals}
        self.cap = jd_profile.anti_penalty_cap
        self.consulting = _lower_tuple(jd_profile.consulting_companies)

        research = anti_signal_vocab["research_only"]
        self.research_terms = _lower_tuple(research["research_terms"])
        self.production_terms = _lower_tuple(research["production_terms"])

        langchain = anti_signal_vocab["langchain_only"]
        self.llm_wrapper_terms = _lower_tuple(langchain["llm_wrapper_terms"])
        self.pre_llm_ml_terms = _lower_tuple(langchain["pre_llm_ml_terms"])

        self.tutorial_terms = _lower_tuple(
            anti_signal_vocab["framework_tutorial"]["tutorial_terms"]
        )
        self.senior_titles = _lower_tuple(
            anti_signal_vocab["no_recent_handson"]["senior_titles"]
        )
        self.cv_domain_terms = _lower_tuple(
            anti_signal_vocab["cv_speech_robotics"]["domain_terms"]
        )
        # Nodes that must be absent for the CV/speech rule to fire (retrieval/NLP/IR).
        self._ir_nlp_prefixes = ("N1", "N3", "N6")

    # -- individual rules ----------------------------------------------------
    def _research_only(self, titles: str, demo: str) -> bool:
        return _any_in(self.research_terms, titles) and not _any_in(self.production_terms, demo)

    def _consulting_only(self, companies: list[str]) -> bool:
        if not companies:
            return False
        return all(any(c in company for c in self.consulting) for company in companies)

    def _langchain_only(self, demo: str) -> bool:
        return _any_in(self.llm_wrapper_terms, demo) and not _any_in(self.pre_llm_ml_terms, demo)

    def _framework_tutorial(self, demo: str, claimed: str, has_demonstrated_strong: bool) -> bool:
        return (_any_in(self.tutorial_terms, demo) or _any_in(self.tutorial_terms, claimed)) \
            and not has_demonstrated_strong

    def _title_chasing(self, candidate: Candidate) -> bool:
        short = sum(
            1 for e in candidate.career_history
            if e.duration_months < scoring.TITLE_CHASING_MAX_DURATION_MONTHS
        )
        return short >= scoring.TITLE_CHASING_MIN_ROLES

    def _no_recent_handson(self, candidate: Candidate, current_desc: str) -> bool:
        title = candidate.profile.current_title.lower()
        is_senior = _any_in(self.senior_titles, title)
        return is_senior and not _any_in(self.production_terms, current_desc)

    def _cv_speech_robotics(self, demo: str, strengths: dict[str, float]) -> bool:
        if not _any_in(self.cv_domain_terms, demo):
            return False
        ir_nlp = sum(
            strengths.get(name, 0.0)
            for name in strengths
            if name[:2] in self._ir_nlp_prefixes
        )
        return ir_nlp == 0.0

    # -- public --------------------------------------------------------------
    def detect(
        self, candidate: Candidate, capability: CapabilityProfile
    ) -> tuple[list[str], float, bool]:
        demo = demonstrated_text(candidate).lower()
        titles = " ".join(
            [candidate.profile.current_title] + [e.title for e in candidate.career_history]
        ).lower()
        companies = [e.company.lower() for e in candidate.career_history]
        current_desc = " ".join(
            e.description for e in candidate.career_history if e.is_current
        ).lower()
        claimed = " ".join(s.name for s in candidate.skills).lower()
        strengths = {ev.node: ev.strength for ev in capability.node_strengths}
        has_demonstrated_strong = any(
            ev.strength == 1.0 and ev.source == "career_description"
            for ev in capability.node_strengths
        )

        checks = {
            "research_only": self._research_only(titles, demo),
            "consulting_only": self._consulting_only(companies),
            "langchain_only": self._langchain_only(demo),
            "framework_tutorial": self._framework_tutorial(demo, claimed, has_demonstrated_strong),
            "title_chasing": self._title_chasing(candidate),
            "no_recent_handson": self._no_recent_handson(candidate, current_desc),
            "cv_speech_robotics": self._cv_speech_robotics(demo, strengths),
        }

        fired = [key for key, hit in checks.items() if hit and key in self.rules]
        penalty = min(sum(self.rules[key].penalty for key in fired), self.cap)
        hard_dq = any(self.rules[key].is_hard_dq for key in fired)
        return fired, penalty, hard_dq


__all__ = ["AntiSignalDetector"]
