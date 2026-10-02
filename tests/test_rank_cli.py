"""End-to-end runs of rank.py on a small synthetic pool."""

from __future__ import annotations

import csv
import json

import pytest

import rank
from tests.conftest import candidate_record, role

DESCRIPTIONS = [
    "Built a recommendation system with embeddings, evaluated with NDCG, deployed to production.",
    "Built a search relevance pipeline with learning to rank.",
    "Worked on dashboards and reporting.",
    "Managed payroll and recruitment.",
]


@pytest.fixture
def pool(tmp_path):
    path = tmp_path / "candidates.jsonl"
    records = [
        candidate_record(cid=f"CAND_{i:07d}", yoe=3 + i % 8,
                         career=[role("Engineer", DESCRIPTIONS[i % 4], duration_months=36)],
                         recruiter_response_rate=0.1 + (i % 9) / 10)
        for i in range(1, 151)
    ]
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def test_valid_and_deterministic(pool, tmp_path):
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    assert rank.main(["--candidates", str(pool), "--out", str(first)]) == 0
    assert rank.main(["--candidates", str(pool), "--out", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    rows = list(csv.DictReader(first.open(encoding="utf-8")))
    assert [int(r["rank"]) for r in rows] == list(range(1, 101))
    scores = [float(r["score"]) for r in rows]
    assert scores == sorted(scores, reverse=True)
    assert all(r["reasoning"].strip() for r in rows)


def test_top_k_controls_row_count(pool, tmp_path):
    out = tmp_path / "out.csv"
    assert rank.main(["--candidates", str(pool), "--out", str(out), "--top-k", "10"]) == 0
    assert len(list(csv.DictReader(out.open(encoding="utf-8")))) == 10


@pytest.mark.parametrize("extra,code", [
    (["--limit", "50"], 1),            # fewer candidates than rows required
    (["--out", "{tmp}"], 2),           # output path is a directory
])
def test_failures_write_nothing(pool, tmp_path, extra, code):
    args = [a.replace("{tmp}", str(tmp_path)) for a in extra]
    out = tmp_path / "out.csv"
    full = ["--candidates", str(pool), "--out", str(out)] + args
    assert rank.main(full) == code
    assert not out.exists()


@pytest.mark.parametrize("extra", [["--as-of", "27-05-2026"], ["--limit", "0"], ["--top-k", "x"]])
def test_invalid_arguments_exit_2(pool, extra):
    with pytest.raises(SystemExit) as exc:
        rank.main(["--candidates", str(pool)] + extra)
    assert exc.value.code == 2


def test_missing_input_exits_2(tmp_path):
    with pytest.raises(SystemExit) as exc:
        rank.main(["--candidates", str(tmp_path / "missing.jsonl")])
    assert exc.value.code == 2
