"""Streaming reader for candidates.jsonl (.jsonl or .jsonl.gz).

Malformed lines and duplicate ids are logged, counted and skipped.
"""

from __future__ import annotations

import gzip
import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from pydantic import ValidationError

from shared.models.candidate import Candidate

logger = logging.getLogger(__name__)


_LAST_ACTIVE = re.compile(r'"last_active_date"\s*:\s*"(\d{4}-\d{2}-\d{2})')


def _open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def latest_activity_date(path: Path | str) -> str | None:
    """Latest last_active_date in the file (YYYY-MM-DD), or None if there is none.

    Scans raw lines with a regex instead of parsing JSON, so it is cheap.
    """
    latest = None
    with _open_text(Path(path)) as handle:
        for line in handle:
            m = _LAST_ACTIVE.search(line)
            if m and (latest is None or m.group(1) > latest):
                latest = m.group(1)
    return latest


class CandidateReader:
    """Yield validated candidates.

    `pool_ids`, `skipped_records` and `duplicate_records` are complete only
    after iteration finishes.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.pool_ids: set[str] = set()
        self.skipped_records: int = 0
        self.duplicate_records: int = 0

    def __iter__(self) -> Iterator[Candidate]:
        with _open_text(self.path) as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    candidate = Candidate.model_validate(json.loads(line))
                except (json.JSONDecodeError, ValidationError) as exc:
                    self.skipped_records += 1
                    logger.warning("skipping line %d: %s", line_no, exc)
                    continue
                if candidate.candidate_id in self.pool_ids:
                    self.duplicate_records += 1
                    logger.warning("skipping line %d: duplicate candidate_id %s",
                                   line_no, candidate.candidate_id)
                    continue
                self.pool_ids.add(candidate.candidate_id)
                yield candidate


__all__ = ["CandidateReader", "latest_activity_date"]
