"""WorkLens-RedRob entrypoint: candidates.jsonl + JD to submission.csv.

One streaming pass over the 100K pool: each candidate is scored through modules 2-5,
fed into the module6 bounded top-K heap, and only the retained 100 get module7
reasoning. Module8 re-validates the rows (the hard gate) before writing.

Reproduce:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# allow running as `python rank.py` from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared.config import paths
from shared.config.run_config import AS_OF_DATE
from shared.utils.jsonl_reader import CandidateReader
from shared.utils.ontology_loader import load_ontology
from modules.module1_jd_rubric import build_jd_profile
from modules.module2_capability import CapabilityExtractor
from modules.module3_capability_fit import CapabilityFitAssembler
from modules.module4_behavioral import BehavioralScorer
from modules.module5_honeypot import HoneypotDetector
from modules.module6_ranking import TopKRanker
from modules.module7_reasoning import ReasoningGenerator
from modules.module8_submission import SubmissionValidator, SubmissionWriter
from shared.models.submission import SubmissionRow

logger = logging.getLogger("rank")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rank the top-100 candidates for the Senior AI Engineer JD.")
    p.add_argument("--candidates", required=True, type=Path, help="path to candidates.jsonl")
    p.add_argument("--out", type=Path, default=paths.DEFAULT_OUTPUT_PATH, help="output submission CSV path")
    p.add_argument("--ontology", type=Path, default=paths.ONTOLOGY_PATH)
    p.add_argument("--jd-rubric", type=Path, default=paths.JD_RUBRIC_PATH)
    p.add_argument("--as-of", default=AS_OF_DATE, help="recency reference date YYYY-MM-DD")
    p.add_argument("--limit", type=int, default=None, help="stop after N candidates (testing only)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)

    # -- one-time setup (outside the per-candidate loop) ---------------------
    rubric_raw = json.loads(Path(args.jd_rubric).read_text(encoding="utf-8"))
    nodes = load_ontology(args.ontology)
    jd = build_jd_profile(nodes, args.jd_rubric)

    extractor = CapabilityExtractor(nodes)
    fitter = CapabilityFitAssembler(jd, rubric_raw["anti_signal_vocab"])
    behaviorist = BehavioralScorer(args.as_of, rubric_raw["logistics_buckets"])
    honeypotter = HoneypotDetector()
    ranker = TopKRanker()
    reasoner = ReasoningGenerator(jd)

    # -- streaming scoring pass ----------------------------------------------
    reader = CandidateReader(args.candidates)
    t0 = time.time()
    n = honeypots = 0
    for candidate in reader:
        capability = extractor.extract(candidate)
        fit = fitter.assemble(candidate, capability)
        behavioral = behaviorist.score(candidate)
        honeypot = honeypotter.detect(candidate)
        honeypots += honeypot.is_honeypot
        ranker.add(candidate, capability, fit, behavioral, honeypot)
        n += 1
        if n % 20000 == 0:
            logger.info("scored %d candidates (%.0fs)", n, time.time() - t0)
        if args.limit and n >= args.limit:
            break
    scan_s = time.time() - t0
    logger.info("scored %d candidates in %.1fs (skipped %d); %d honeypots in pool",
                n, scan_s, reader.skipped_records, honeypots)

    # -- finalize ranking + reasoning ----------------------------------------
    entries = ranker.finalize()
    rows = [
        SubmissionRow(
            candidate_id=e.candidate.candidate_id,
            rank=e.rank,
            score=e.score,
            reasoning=reasoner.reason(e),
        )
        for e in entries
    ]

    # -- hard validation gate ------------------------------------------------
    errors = SubmissionValidator(reader.pool_ids).validate(rows)
    if errors:
        logger.error("SUBMISSION VALIDATION FAILED (%d):", len(errors))
        for e in errors:
            logger.error("  - %s", e)
        return 1

    out = SubmissionWriter().write(rows, args.out)
    hp_top = sum(1 for e in entries if e.honeypot.is_honeypot)
    logger.info("wrote %s (rows=%d, honeypots_in_top100=%d, top_score=%.6f, total=%.1fs)",
                out, len(rows), hp_top, rows[0].score, time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
