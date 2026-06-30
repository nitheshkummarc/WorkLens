"""Per-candidate reasoning (§6) — module7.

Deterministic template, every claim pulled from the candidate's own fields /
matched evidence phrases — no hallucination (Stage-4 check). Output varies because
nodes, evidence snippets, behavioral values and concerns differ per candidate, and
the tone tracks rank: strong candidates lead with strengths, weak ones lead with
the concern (Stage-4 "rank consistency").

Template (§6):
  "{title} with {yrs} yrs; strengths: {top-2 nodes + 1 evidence snippet};
   {1 behavioral note}; concern: {missing Critical node | fired anti-signal | notice}."
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

_RANK_CONCERN_LEAD = 50  # ranks beyond this lead with the concern


def _label(node_name: str) -> str:
    """'N1 Retrieval & Search' -> 'Retrieval & Search'."""
    head, _, rest = node_name.partition(" ")
    return rest if (rest and head[:1] == "N" and head[1:].isdigit()) else node_name


def _fmt_years(years: float) -> str:
    return f"{years:g}"


class ReasoningGenerator:
    """Builds the reasoning string for a ranked candidate; setup done once."""

    def __init__(self, jd_profile: JDProfile) -> None:
        self.critical = list(jd_profile.critical_nodes)
        self.importance = {r.name: r.importance for r in jd_profile.required_capabilities}

    # -- pieces --------------------------------------------------------------
    def _strengths(self, entry: RankedEntry) -> str:
        present = [ev for ev in entry.capability.node_strengths if ev.strength > 0]
        present.sort(key=lambda ev: (ev.strength, self.importance.get(ev.node, 0.0)), reverse=True)
        if not present:
            return "limited demonstrated AI/ML capability"
        parts: list[str] = []
        for i, ev in enumerate(present[:2]):
            word = "strong" if ev.strength == 1.0 else "emerging"
            label = _label(ev.node)
            if i == 0 and ev.evidence_phrase:
                parts.append(f"{word} {label} ({ev.evidence_phrase})")
            else:
                parts.append(f"{word} {label}")
        return " and ".join(parts)

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
        rate = entry.candidate.redrob_signals.recruiter_response_rate
        return f"{phrase}, recruiter response rate {rate:.2f}"

    def _concern(self, entry: RankedEntry) -> str:
        # 1) a fired anti-signal (most material honest concern)
        for key in entry.fit.anti_signals_fired:
            if key in _ANTI_CONCERN:
                return _ANTI_CONCERN[key]
        # 2) the highest-importance Critical node with no evidence
        strengths = {ev.node: ev.strength for ev in entry.capability.node_strengths}
        missing = [n for n in self.critical if strengths.get(n, 0.0) == 0.0]
        if missing:
            missing.sort(key=lambda n: self.importance.get(n, 0.0), reverse=True)
            return f"no demonstrated {_label(missing[0])} evidence"
        # 3) logistics: a long notice period
        notice = entry.candidate.redrob_signals.notice_period_days
        if notice >= 90:
            return f"long notice period ({notice} days)"
        # 4) otherwise only partial coverage of the senior build-core
        weak_critical = [n for n in self.critical if strengths.get(n, 0.0) == 0.5]
        if weak_critical:
            weak_critical.sort(key=lambda n: self.importance.get(n, 0.0), reverse=True)
            return f"{_label(weak_critical[0])} is claimed but not yet demonstrated in production"
        return "depth beyond the core requirements is limited"

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
            return (f"{title} with {yrs} yrs; strengths: {strengths}; {behavior}. "
                    f"Concern: {concern}.")
        return (f"{title} with {yrs} yrs; ranked here mainly due to {concern}. "
                f"Still shows {strengths}; {behavior}.")


__all__ = ["ReasoningGenerator"]
