"""Per-candidate reasoning — module7.

A deterministic template; every claim comes from the candidate's own fields or a
matched evidence phrase, so nothing is hallucinated. Output varies because the
nodes, evidence, ML tenure, behavioral values and concerns differ per candidate,
and the tone follows the rank: strong candidates lead with strengths, weaker ones
lead with the concern.

Each line has: title + years; up to three demonstrated strength areas (the first
with a concrete evidence phrase) plus applied-ML tenure when it's substantial; a
behavioral note (recency, responsiveness, availability); and one specific, honest
concern (a fired anti-signal, a missing JD area, a long notice period, or a
nice-to-have gap for otherwise-complete profiles).
"""

from __future__ import annotations

from shared.models.jd_profile import JDProfile
from modules.module6_ranking.ranker import RankedEntry

# readable concern text per anti-signal key (honest, profile-grounded)
_ANTI_CONCERN = {
    "research_only": "research/academic background with little production-deployment evidence",
    "consulting_only": "consulting-services career, where work content is harder to verify",
    "langchain_only": "recent LLM-wrapper focus without earlier ML-production evidence",
    "framework_tutorial": "tutorial/demo-level evidence rather than shipped systems",
    "title_chasing": "several short stints rather than sustained ownership",
    "no_recent_handson": "senior/managerial title with limited recent hands-on signal",
    "cv_speech_robotics": "vision/speech focus rather than retrieval/NLP/IR",
}

_RANK_CONCERN_LEAD = 50   # ranks beyond this lead with the concern
_ML_TENURE_YEARS = 4      # surface applied-ML tenure as a strength at/above this


def _label(node_name: str) -> str:
    """'N1 Retrieval & Search' -> 'Retrieval & Search'."""
    head, _, rest = node_name.partition(" ")
    return rest if (rest and head[:1] == "N" and head[1:].isdigit()) else node_name


def _fmt_years(years: float) -> str:
    return f"{years:g}"


def _cap_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


class ReasoningGenerator:
    """Builds the reasoning string for a ranked candidate; setup done once."""

    def __init__(self, jd_profile: JDProfile) -> None:
        self.critical = list(jd_profile.critical_nodes)
        self.nice = list(jd_profile.nice_to_have_nodes)
        self.importance = {r.name: r.importance for r in jd_profile.required_capabilities}

    def _ranked_present(self, capability) -> list:
        present = [ev for ev in capability.node_strengths if ev.strength > 0]
        present.sort(key=lambda ev: (ev.strength, self.importance.get(ev.node, 0.0)), reverse=True)
        return present

    # -- strengths -----------------------------------------------------------
    def _strengths(self, entry: RankedEntry) -> str:
        present = self._ranked_present(entry.capability)
        if not present:
            return "limited demonstrated AI/ML capability"

        strong = [ev for ev in present if ev.strength == 1.0][:3]
        weak = [ev for ev in present if ev.strength == 0.5]

        segments: list[str] = []
        if strong:
            lead = strong[0]
            names = [f"{_label(lead.node)} ({lead.evidence_phrase})"] + [_label(e.node) for e in strong[1:]]
            segments.append("strong " + ", ".join(names))
            if len(strong) < 2 and weak:
                segments.append("emerging " + _label(weak[0].node))
        else:
            lead = weak[0]
            segments.append(f"emerging {_label(lead.node)} ({lead.evidence_phrase})"
                            + (", " + ", ".join(_label(e.node) for e in weak[1:3]) if weak[1:3] else ""))

        text = "; ".join(segments)
        ml_years = entry.capability.ml_relevant_months / 12.0
        if ml_years >= _ML_TENURE_YEARS:
            text += f"; ~{ml_years:.0f} yrs applied-ML tenure"
        return text

    # -- behavioral ----------------------------------------------------------
    def _behavioral_note(self, entry: RankedEntry) -> str:
        recency = entry.behavioral.recency
        if recency >= 1.0:
            phrase = "active in the last month"
        elif recency >= 0.9:
            phrase = "active recently"
        elif recency >= 0.75:
            phrase = "active this quarter"
        elif recency >= 0.5:
            phrase = "last active ~6 months ago"
        else:
            phrase = "limited recent activity"
        sig = entry.candidate.redrob_signals
        note = f"{phrase}, recruiter response {sig.recruiter_response_rate:.2f}"
        if sig.open_to_work_flag:
            note += ", open to work"
        return note

    # -- concern (always specific) -------------------------------------------
    def _concern(self, entry: RankedEntry) -> str:
        strengths = {ev.node: ev.strength for ev in entry.capability.node_strengths}

        # 1) a fired anti-signal (most material honest concern)
        for key in entry.fit.anti_signals_fired:
            if key in _ANTI_CONCERN:
                return _ANTI_CONCERN[key]
        # 2) the highest-importance Critical node with no evidence at all
        missing = sorted((n for n in self.critical if strengths.get(n, 0.0) == 0.0),
                         key=lambda n: self.importance.get(n, 0.0), reverse=True)
        if missing:
            return f"no demonstrated {_label(missing[0])} evidence"
        # 3) logistics: a long notice period
        notice = entry.candidate.redrob_signals.notice_period_days
        if notice >= 90:
            return f"long notice period ({notice} days)"
        # 4) a Critical node claimed but not demonstrated in production
        weak_critical = sorted((n for n in self.critical if strengths.get(n, 0.0) == 0.5),
                               key=lambda n: self.importance.get(n, 0.0), reverse=True)
        if weak_critical:
            return f"{_label(weak_critical[0])} is claimed but not yet demonstrated in production"
        # 5) core is fully covered — point at a nice-to-have gap or thin ML tenure
        missing_nice = sorted((n for n in self.nice if strengths.get(n, 0.0) == 0.0),
                              key=lambda n: self.importance.get(n, 0.0), reverse=True)
        if missing_nice:
            return f"limited {_label(missing_nice[0])} depth beyond the core"
        ml_years = entry.capability.ml_relevant_months / 12.0
        if ml_years < _ML_TENURE_YEARS:
            return f"strong on the core but only ~{ml_years:.0f} yrs of applied-ML tenure"
        return "very strong across the board; no material gap flagged"

    # -- public --------------------------------------------------------------
    def reason(self, entry: RankedEntry) -> str:
        if entry.honeypot.is_honeypot:  # defensive — honeypots score 0, shouldn't reach top-100
            return f"Profile flagged as implausible ({entry.honeypot.evidence}); not a credible fit."

        title = entry.candidate.profile.current_title
        yrs = _fmt_years(entry.candidate.profile.years_of_experience)
        strengths = self._strengths(entry)
        behavior = self._behavioral_note(entry)
        concern = self._concern(entry)

        if entry.rank <= _RANK_CONCERN_LEAD:
            return f"{title}, {yrs} yrs — {strengths}. {_cap_first(behavior)}. Concern: {concern}."
        return f"{title}, {yrs} yrs — ranked here mainly due to {concern}. Still {strengths}; {behavior}."


__all__ = ["ReasoningGenerator"]
