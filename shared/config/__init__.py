"""Scoring constants, project paths and input/output format settings."""

from __future__ import annotations

from . import scoring
from .paths import (
    DATA_DIR,
    DEFAULT_OUTPUT_PATH,
    JD_RUBRIC_PATH,
    ONTOLOGY_PATH,
    OUTPUTS_DIR,
    PROJECT_ROOT,
)
from .run_config import CANDIDATE_ID_PATTERN

__all__ = [
    "scoring",
    "CANDIDATE_ID_PATTERN",
    "PROJECT_ROOT",
    "DATA_DIR",
    "ONTOLOGY_PATH",
    "JD_RUBRIC_PATH",
    "OUTPUTS_DIR",
    "DEFAULT_OUTPUT_PATH",
]
