"""module8: the hard validation gate rejects every spec violation."""

from __future__ import annotations

from shared.models.submission import SubmissionRow
from modules.module8_submission import SubmissionValidator


def _good_rows(n=100):
    return [SubmissionRow(candidate_id=f"CAND_{i:07d}", rank=i, score=round(1.0 - i * 0.001, 6),
                          reasoning=f"reason {i}") for i in range(1, n + 1)]


POOL = {f"CAND_{i:07d}" for i in range(1, 101)}


def test_good_submission_passes():
    assert SubmissionValidator(POOL).validate(_good_rows()) == []


def test_wrong_row_count_rejected():
    assert SubmissionValidator(POOL).validate(_good_rows(99))


def test_duplicate_rank_rejected():
    rows = _good_rows()
    rows[1].rank = 1
    assert any("duplicate rank" in e for e in SubmissionValidator(POOL).validate(rows))


def test_increasing_score_rejected():
    rows = _good_rows()
    rows[5].score = 9.9
    assert any("increase" in e for e in SubmissionValidator(POOL).validate(rows))


def test_all_identical_scores_rejected():
    rows = [SubmissionRow(candidate_id=f"CAND_{i:07d}", rank=i, score=0.5, reasoning="x")
            for i in range(1, 101)]
    assert any("identical" in e for e in SubmissionValidator(POOL).validate(rows))


def test_id_not_in_pool_rejected():
    rows = _good_rows()
    rows[0] = SubmissionRow(candidate_id="CAND_9999999", rank=1, score=rows[0].score, reasoning="x")
    assert any("not in pool" in e for e in SubmissionValidator(POOL).validate(rows))


def test_empty_reasoning_rejected():
    rows = _good_rows()
    rows[3].reasoning = "   "
    assert any("empty reasoning" in e for e in SubmissionValidator(POOL).validate(rows))


def test_tie_break_id_order_enforced():
    rows = _good_rows()
    # make ranks 1 and 2 tie on score but put ids in the wrong order
    rows[0] = SubmissionRow(candidate_id="CAND_0000050", rank=1, score=0.9, reasoning="a")
    rows[1] = SubmissionRow(candidate_id="CAND_0000002", rank=2, score=0.9, reasoning="b")
    assert any("ascending" in e for e in SubmissionValidator(POOL).validate(rows))
