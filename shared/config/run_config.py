"""Configuration for a single ranking run.

The AS_OF date is the dataset's latest last_active_date (2026-05-27); recency is
measured against it, never datetime.now(), so the run is reproducible.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .paths import DEFAULT_OUTPUT_PATH, JD_RUBRIC_PATH, ONTOLOGY_PATH

# Dataset max last_active_date — deterministic recency reference (no wall clock).
AS_OF_DATE: str = "2026-05-27"


class RunConfig(BaseModel):
    """All inputs/outputs and the recency reference for one `rank.py` invocation."""

    model_config = ConfigDict(frozen=True)

    candidates_path: Path                       # required: candidates.jsonl (read-streamed)
    job_description_path: Path                   # required: released JD (context)
    ontology_path: Path = ONTOLOGY_PATH          # data/ai_capability_ontology.json
    jd_rubric_path: Path = JD_RUBRIC_PATH        # data/jd_rubric.json
    output_path: Path = DEFAULT_OUTPUT_PATH      # outputs/submission.csv
    as_of_date: str = AS_OF_DATE


__all__ = ["RunConfig", "AS_OF_DATE"]
