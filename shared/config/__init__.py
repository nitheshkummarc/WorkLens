"""Config package — re-exports the focused config modules as one surface.

`scoring` is exposed as a namespace (import the module) so call sites read
`scoring.ANTI_PENALTY_CAP`, keeping each constant's section provenance visible.
Paths and run config are flat re-exports.
"""

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
from .run_config import AS_OF_DATE, RunConfig

__all__ = [
    "scoring",
    "RunConfig",
    "AS_OF_DATE",
    "PROJECT_ROOT",
    "DATA_DIR",
    "ONTOLOGY_PATH",
    "JD_RUBRIC_PATH",
    "OUTPUTS_DIR",
    "DEFAULT_OUTPUT_PATH",
]
