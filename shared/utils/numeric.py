"""Small numeric helpers shared by the scoring modules."""

from __future__ import annotations


def clamp01(value: float) -> float:
    """Clamp `value` to the closed interval [0, 1]."""
    return max(0.0, min(1.0, value))


__all__ = ["clamp01"]
