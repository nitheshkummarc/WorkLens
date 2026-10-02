"""Project paths, resolved relative to this file."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = PROJECT_ROOT / "data"
ONTOLOGY_PATH: Path = DATA_DIR / "ai_capability_ontology.json"
JD_RUBRIC_PATH: Path = DATA_DIR / "jd_rubric.json"

OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
DEFAULT_OUTPUT_PATH: Path = OUTPUTS_DIR / "submission.csv"

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "ONTOLOGY_PATH",
    "JD_RUBRIC_PATH",
    "OUTPUTS_DIR",
    "DEFAULT_OUTPUT_PATH",
]
