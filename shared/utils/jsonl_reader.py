"""Stream-read and validate `candidates.jsonl` (interface_contract.md §1a).

Yields validated `Candidate` objects one at a time (constant memory over the
~465 MB / 100K-row pool) and, as a side effect of iteration, accumulates the set
of all valid candidate ids seen. That `pool_ids` set is threaded into module8 so
its "every top-100 id exists in the pool" check is a real membership test.

Robustness: a single malformed/invalid line is skipped (warned, counted) — never
fatal. Only catastrophic I/O (unreadable file) aborts the run.
"""

from __future__ import annotations

import gzip
import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from shared.models.candidate import Candidate

logger = logging.getLogger(__name__)


class CandidateReader:
    """Iterable over a JSONL candidate file; exposes pool ids + skip count.

    Accepts either a plain `.jsonl` or a gzipped `.jsonl.gz` file (the bundle
    ships the pool gzipped) — the format is chosen from the suffix, so the same
    reproduce command works on either. `pool_ids` and `skipped_records` fill in
    *as the stream is consumed*, so read them after iteration completes.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.pool_ids: set[str] = set()
        self.skipped_records: int = 0

    def _open(self) -> TextIO:
        """Open as UTF-8 text, transparently decompressing a `.gz` file."""
        if self.path.suffix == ".gz":
            return gzip.open(self.path, mode="rt", encoding="utf-8")
        return self.path.open(encoding="utf-8")

    def __iter__(self) -> Iterator[Candidate]:
        with self._open() as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    candidate = Candidate.model_validate(json.loads(line))
                except Exception as exc:  # malformed JSON or schema violation
                    self.skipped_records += 1
                    logger.warning("skipping line %d: %s", line_no, exc)
                    continue
                self.pool_ids.add(candidate.candidate_id)
                yield candidate


__all__ = ["CandidateReader"]
