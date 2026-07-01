"""Apply rubric adjustments and assemble the capability_fit score."""

from __future__ import annotations

from .anti_signals import AntiSignalDetector
from .assembler import CapabilityFitAssembler

__all__ = ["AntiSignalDetector", "CapabilityFitAssembler"]
