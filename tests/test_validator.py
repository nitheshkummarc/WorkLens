"""module8: the validator rejects each rule violation; the writer output is safe."""

from __future__ import annotations

import csv

import pytest

from shared.models.submission import SubmissionRow
from modules.module8_submission import SubmissionValidator, SubmissionWriter

POOL = {f"CAND_{i:07d}" for i in range(1, 101)}


def _rows(n=100):
    return [SubmissionRow(candidate_id=f"CAND_{i:07d}", rank=i, score=round(1.0 - i * 0.001, 6),
                          reasoning=f"reason {i}") for i in range(1, n + 1)]


def test_valid_submission_passes():
    assert SubmissionValidator(POOL).validate(_rows()) == []


def _wrong_count(rows): return rows[:99]
def _duplicate_rank(rows): rows[1].rank = 1; return rows
def _increasing(rows): rows[5].score = 9.9; return rows
def _identical(rows):
    for r in rows: r.score = 0.5
    return rows
def _not_in_pool(rows): rows[0].candidate_id = "CAND_9999999"; return rows
def _empty_reason(rows): rows[3].reasoning = "   "; return rows
def _tie_order(rows):
    rows[0].candidate_id, rows[0].score = "CAND_0000050", 0.9
    rows[1].score = 0.9
    return rows


@pytest.mark.parametrize("mutate,message", [
    (_wrong_count, "exactly 100"), (_duplicate_rank, "duplicate rank"), (_increasing, "increases"),
    (_identical, "identical"), (_not_in_pool, "not in pool"), (_empty_reason, "empty reasoning"),
    (_tie_order, "ascending"),
])
def test_rejections(mutate, message):
    assert any(message in e for e in SubmissionValidator(POOL).validate(mutate(_rows())))


def test_writer_format_and_formula_guard(tmp_path):
    rows = _rows()
    rows[0].reasoning = "=HYPERLINK(\"x\"), title"
    written = list(csv.reader(SubmissionWriter().write(rows, tmp_path / "out.csv").open(encoding="utf-8")))
    assert written[0] == ["candidate_id", "rank", "score", "reasoning"]
    assert written[1][2] == "0.999000"
    assert written[1][3].startswith("'=")
