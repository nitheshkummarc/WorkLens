"""Reasoning text for ranked candidates.

Template: title and years; up to three capability areas (first with its
evidence phrase) and applied-ML tenure if >= 4 years; activity and response
rate; the main gap, if any. The first half of the ranked list leads with
strengths, the second half with the gap. Thresholds are in scoring.py and
anti-signal wording in the rubric.
"""

from __future__ import annotations

from typing import Optional

from shared.config import scoring
from shared.models.capability import CapabilityProfile, NodeEvidence
from shared.models.jd_profile import JDProfile
from shared.utils.date_utils import days_since
from modules.module6_ranking.ranker import RankedEntry

def _label(node_name: str) -> str:
    """'N1 Retrieval & Search' -> 'Retrieval & Search'."""
    head, _, rest = node_name.partition(" ")
    return rest if (rest and head[:1] == "N" and head[1:].isdigit()) else node_name


def _fmt_years(years: float) -> str:
    return f"{round(years, 1):g}"


def _cap_first(text: str) -> str:
    return text[:1].upper() + text[1:]


def _activity(days: int) -> str:
    if days == 0:
        return "active on the reference date"
    return f"last active {days} day{'s' if days != 1 else ''} ago"


class ReasoningGenerator:
    """Build the reasoning string for a ranked candidate."""

    def __init__(self, jd_profile: JDProfile, as_of_date: str,
                 list_size: int = scoring.SUBMISSION_ROW_COUNT) -> None:
        self.as_of = as_of_date
        self.lead_with_strengths = max(1, list_size // 2)
        self.concerns = jd_profile.anti_signal_concerns
        self.importance = {r.name: r.importance for r in jd_profile.required_capabilities}
        self.critical = sorted(jd_profile.critical_nodes,
                               key=lambda n: self.importance.get(n, 0.0), reverse=True)
        self.nice = sorted(jd_profile.nice_to_have_nodes,
                           key=lambda n: self.importance.get(n, 0.0), reverse=True)

    def _strengths(self, capability: CapabilityProfile) -> str:
        present = sorted(
            (ev for ev in capability.node_strengths if ev.strength > 0),
            key=lambda ev: (ev.strength, self.importance.get(ev.node, 0.0)),
            reverse=True,
        )
        if not present:
            return "limited AI/ML capability evidence"

        strong = [ev for ev in present if ev.strength == scoring.NODE_STRENGTH_STRONG][:3]
        partial = [ev for ev in present if ev.strength == scoring.NODE_STRENGTH_WEAK]

        if strong:
            names = [f"{_label(strong[0].node)} ({strong[0].evidence_phrase})"]
            names += [_label(ev.node) for ev in strong[1:]]
            text = "strong " + ", ".join(names)
            if len(strong) < 2 and partial:
                text += "; partial " + _label(partial[0].node)
        else:
            names = [f"{_label(partial[0].node)} ({partial[0].evidence_phrase})"]
            names += [_label(ev.node) for ev in partial[1:3]]
            text = "partial " + ", ".join(names)

        ml_years = capability.ml_relevant_months / 12.0
        if ml_years >= scoring.REASON_ML_TENURE_YEARS:
            text += f"; ~{_fmt_years(ml_years)} yrs applied-ML tenure"
        return text

    def _behavior(self, entry: RankedEntry) -> str:
        sig = entry.candidate.redrob_signals
        note = (f"{_activity(days_since(sig.last_active_date, self.as_of))}, "
                f"recruiter response rate {sig.recruiter_response_rate:.2f}")
        if sig.open_to_work_flag:
            note += ", open to work"
        return note

    @staticmethod
    def _partial_evidence(node: str, ev: NodeEvidence) -> str:
        if ev.source == "claimed":
            return f"only self-reported {_label(node)} evidence"
        return f'only indirect {_label(node)} evidence in career history ("{ev.evidence_phrase}")'

    def _concern(self, entry: RankedEntry) -> tuple[Optional[str], bool]:
        """(gap or None, is_behavioral). Checked in priority order."""
        evidence = {ev.node: ev for ev in entry.capability.node_strengths}
        sig = entry.candidate.redrob_signals

        for key in entry.fit.anti_signals_fired:
            if key in self.concerns:
                return self.concerns[key], False

        for node in self.critical:
            if node in evidence and evidence[node].strength == scoring.NODE_STRENGTH_NONE:
                return f"no demonstrated {_label(node)} evidence", False

        days = days_since(sig.last_active_date, self.as_of)
        behavioral = []
        if days > scoring.REASON_STALE_DAYS:
            behavioral.append(f"no platform activity in {days} days")
        if sig.recruiter_response_rate < scoring.REASON_LOW_RESPONSE_RATE:
            behavioral.append(f"a low recruiter response rate ({sig.recruiter_response_rate:.2f})")
        if behavioral:
            return " and ".join(behavioral), True

        if sig.notice_period_days >= scoring.REASON_LONG_NOTICE_DAYS:
            return f"a long notice period ({sig.notice_period_days} days)", False

        for node in self.critical:
            if node in evidence and evidence[node].strength == scoring.NODE_STRENGTH_WEAK:
                return self._partial_evidence(node, evidence[node]), False

        for node in self.nice:
            if node in evidence and evidence[node].strength == scoring.NODE_STRENGTH_NONE:
                return f"limited {_label(node)} depth", False

        ml_years = entry.capability.ml_relevant_months / 12.0
        if ml_years < scoring.REASON_ML_TENURE_YEARS:
            return f"only ~{_fmt_years(ml_years)} yrs of applied-ML tenure", False

        return None, False

    def reason(self, entry: RankedEntry) -> str:
        if entry.honeypot.is_honeypot:
            # Reachable only when fewer than K candidates score above 0.
            return f"Profile flagged as implausible ({entry.honeypot.evidence}); not a credible fit."

        profile = entry.candidate.profile
        head = f"{profile.current_title}, {_fmt_years(profile.years_of_experience)} yrs"
        strengths = self._strengths(entry.capability)
        behavior = self._behavior(entry)
        concern, behavioral_concern = self._concern(entry)

        if concern is None:
            return f"{head} — {strengths}. {_cap_first(behavior)}. No material gap identified."
        if entry.rank <= self.lead_with_strengths:
            return f"{head} — {strengths}. {_cap_first(behavior)}. Concern: {concern}."
        if behavioral_concern:
            return f"{head} — main gap: {concern}. {_cap_first(strengths)}."
        return f"{head} — main gap: {concern}. {_cap_first(strengths)}; {behavior}."


__all__ = ["ReasoningGenerator"]
