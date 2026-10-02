"""Rank a candidate pool and write the submission CSV.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./output.csv

Exit codes: 0 success, 1 output failed validation, 2 invalid arguments,
configuration or output path.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Allow `python rank.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared.config import paths, scoring
from shared.models.submission import SubmissionRow
from shared.utils.date_utils import parse_date
from shared.utils.jsonl_reader import CandidateReader, latest_activity_date
from shared.utils.ontology_loader import load_ontology
from modules.module1_jd_rubric import build_jd_profile
from modules.module2_capability import CapabilityExtractor
from modules.module3_capability_fit import CapabilityFitAssembler
from modules.module4_behavioral import BehavioralScorer
from modules.module5_honeypot import HoneypotDetector
from modules.module6_ranking import TopKRanker
from modules.module7_reasoning import ReasoningGenerator
from modules.module8_submission import SubmissionValidator, SubmissionWriter

logger = logging.getLogger("rank")

_PROGRESS_EVERY = 20_000


def _existing_file(value: str) -> Path:
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file not found: {value}")
    return path


def _iso_date(value: str) -> str:
    try:
        parse_date(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a YYYY-MM-DD date, got {value!r}") from None
    return value


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        number = 0
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Rank candidates against the job rubric and write the submission CSV.")
    p.add_argument("--candidates", required=True, type=_existing_file,
                   help="candidate pool (.jsonl or .jsonl.gz)")
    p.add_argument("--out", type=Path, default=paths.DEFAULT_OUTPUT_PATH,
                   help="output CSV path")
    p.add_argument("--ontology", type=_existing_file, default=paths.ONTOLOGY_PATH)
    p.add_argument("--jd-rubric", type=_existing_file, default=paths.JD_RUBRIC_PATH)
    p.add_argument("--as-of", type=_iso_date, default=None,
                   help="reference date for recency, YYYY-MM-DD "
                        "(default: latest last_active_date in the input)")
    p.add_argument("--top-k", type=_positive_int, default=scoring.SUBMISSION_ROW_COUNT,
                   help="number of candidates to output")
    p.add_argument("--limit", type=_positive_int, default=None,
                   help="stop after N candidates (for testing)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)

    try:
        nodes = load_ontology(args.ontology)
        jd = build_jd_profile(nodes, args.jd_rubric)
    except (OSError, ValueError) as exc:
        logger.error("invalid configuration: %s", exc)
        return 2

    as_of = args.as_of or latest_activity_date(args.candidates)
    if as_of is None:
        logger.error("no last_active_date found in %s; pass --as-of", args.candidates)
        return 2
    logger.info("recency reference date: %s", as_of)

    extractor = CapabilityExtractor(nodes, jd.ml_nodes)
    fitter = CapabilityFitAssembler(jd)
    behavior = BehavioralScorer(jd, as_of)
    honeypots = HoneypotDetector()
    ranker = TopKRanker(args.top_k)
    reasoner = ReasoningGenerator(jd, as_of, args.top_k)

    reader = CandidateReader(args.candidates)
    t0 = time.time()
    n = honeypot_count = 0
    for candidate in reader:
        capability = extractor.extract(candidate)
        fit = fitter.assemble(candidate, capability)
        behavioral = behavior.score(candidate)
        honeypot = honeypots.detect(candidate)
        honeypot_count += honeypot.is_honeypot
        ranker.add(candidate, capability, fit, behavioral, honeypot)
        n += 1
        if n % _PROGRESS_EVERY == 0:
            logger.info("scored %d candidates (%.0fs)", n, time.time() - t0)
        if args.limit and n >= args.limit:
            break
    logger.info("scored %d candidates in %.1fs (%d malformed, %d duplicate ids skipped); "
                "%d honeypots in pool",
                n, time.time() - t0, reader.skipped_records, reader.duplicate_records,
                honeypot_count)

    entries = ranker.finalize()
    rows = [
        SubmissionRow(candidate_id=e.candidate.candidate_id, rank=e.rank,
                      score=e.score, reasoning=reasoner.reason(e))
        for e in entries
    ]

    errors = SubmissionValidator(reader.pool_ids, args.top_k).validate(rows)
    if errors:
        logger.error("submission validation failed (%d errors):", len(errors))
        for error in errors:
            logger.error("  - %s", error)
        return 1

    try:
        out = SubmissionWriter().write(rows, args.out)
    except OSError as exc:
        logger.error("cannot write %s: %s", args.out, exc)
        return 2
    honeypots_in_top = sum(1 for e in entries if e.honeypot.is_honeypot)
    logger.info("wrote %s (rows=%d, honeypots_in_top=%d, top_score=%.6f, total=%.1fs)",
                out, len(rows), honeypots_in_top, rows[0].score, time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
