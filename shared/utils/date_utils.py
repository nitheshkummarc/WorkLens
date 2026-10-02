"""ISO date helpers for recency scoring."""

from __future__ import annotations

from datetime import date


def parse_date(iso: str) -> date:
    """Parse a YYYY-MM-DD date. A trailing time component is ignored."""
    return date.fromisoformat(iso[:10])


def days_between(start_iso: str, end_iso: str) -> int:
    """Whole days from start to end; negative if end is before start."""
    return (parse_date(end_iso) - parse_date(start_iso)).days


def days_since(when_iso: str, as_of_iso: str) -> int:
    """Days from `when` to `as_of`, floored at 0."""
    return max(0, days_between(when_iso, as_of_iso))


__all__ = ["parse_date", "days_between", "days_since"]
