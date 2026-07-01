"""Date math for recency scoring.

ISO dates only (the schema guarantees YYYY-MM-DD). Recency is measured against the
run's AS_OF date (the dataset's latest last_active_date), never the wall clock, so
runs are reproducible.
"""

from __future__ import annotations

from datetime import date


def parse_date(iso: str) -> date:
    """Parse an ISO date; tolerant of an appended time component."""
    return date.fromisoformat(iso[:10])


def days_between(start_iso: str, end_iso: str) -> int:
    """Whole days from start to end (negative if end precedes start)."""
    return (parse_date(end_iso) - parse_date(start_iso)).days


def days_since(when_iso: str, as_of_iso: str) -> int:
    """Days from `when` up to AS_OF, floored at 0 (future activity counts as 0)."""
    return max(0, days_between(when_iso, as_of_iso))


__all__ = ["parse_date", "days_between", "days_since"]
