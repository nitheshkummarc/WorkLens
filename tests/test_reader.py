"""CandidateReader and the reference-date scan: plain and gzip input, bad lines, duplicates."""

from __future__ import annotations

import gzip
import json

from shared.utils.jsonl_reader import CandidateReader, latest_activity_date
from tests.conftest import candidate_record


def _line(cid, last_active="2026-05-20"):
    return json.dumps(candidate_record(cid=cid, last_active_date=last_active))


def test_reads_gzip_and_finds_latest_date(tmp_path):
    path = tmp_path / "pool.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("\n".join([_line("CAND_0000001", "2026-01-02"), _line("CAND_0000002", "2026-03-04")]))
    assert [c.candidate_id for c in CandidateReader(path)] == ["CAND_0000001", "CAND_0000002"]
    assert latest_activity_date(path) == "2026-03-04"


def test_skips_malformed_and_duplicate_records(tmp_path):
    bad_schema = json.dumps({**candidate_record(cid="CAND_0000003"), "candidate_id": "bad"})
    path = tmp_path / "pool.jsonl"
    path.write_text("\n".join([_line("CAND_0000001"), "{not json", bad_schema, "",
                               _line("CAND_0000001"), _line("CAND_0000002")]), encoding="utf-8")
    reader = CandidateReader(path)
    assert [c.candidate_id for c in reader] == ["CAND_0000001", "CAND_0000002"]
    assert (reader.skipped_records, reader.duplicate_records) == (2, 1)
    assert reader.pool_ids == {"CAND_0000001", "CAND_0000002"}
