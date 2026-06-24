"""Project-root path resolution for WorkLens-RedRob.

Pure path handling (pattern reused from WorkLens `shared/config/paths.py`): every
anchor is derived from this file's location, so the project relocates cleanly and
nothing depends on the current working directory. No I/O happens at import time.

Layout (this file is `worklens_redrob/shared/config/paths.py`):
    parents[0] = shared/config
    parents[1] = shared
    parents[2] = worklens_redrob/   <- PROJECT_ROOT
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# Committed data artifacts (the ontology + JD rubric live in `data/`).
DATA_DIR: Path = PROJECT_ROOT / "data"
ONTOLOGY_PATH: Path = DATA_DIR / "ai_capability_ontology.json"
JD_RUBRIC_PATH: Path = DATA_DIR / "jd_rubric.json"

# Generated submission output (git-ignored).
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
