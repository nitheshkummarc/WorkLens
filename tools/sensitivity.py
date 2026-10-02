"""Calibration sensitivity check.

Re-ranks a sample of the pool under randomly perturbed constants and reports
how much the top-K changes relative to the unperturbed ranking:

  - each node importance is multiplied by U(1 - spread, 1 + spread), then all
    importances are rescaled so the largest is 1.0 (base_capability depends
    only on their ratios);
  - each experience-band factor and ML-depth factor is shifted by
    U(-shift, +shift), clamped to the ranges the models allow.

Usage:
    python tools/sensitivity.py --candidates ./candidates.jsonl
"""

from __future__ import annotations

import argparse
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.config import paths, scoring
from shared.models.ontology import OntologyNode
from shared.utils.jsonl_reader import CandidateReader, latest_activity_date
from shared.utils.ontology_loader import load_ontology
from modules.module1_jd_rubric import build_jd_profile
from modules.module2_capability import CapabilityExtractor
from modules.module3_capability_fit import CapabilityFitAssembler
from modules.module4_behavioral import BehavioralScorer
from modules.module5_honeypot import HoneypotDetector
from modules.module6_ranking import TopKRanker

_ML_DEPTH_NAMES = ("ML_DEPTH_FACTOR_HIGH", "ML_DEPTH_FACTOR_SOLID",
                   "ML_DEPTH_FACTOR_SHALLOW", "ML_DEPTH_FACTOR_PIVOT", "ML_DEPTH_FACTOR_NONE")
_ML_DEPTH_RANGE = (0.85, 1.10)


def _rank(candidates, nodes, jd, k, as_of):
    extractor, fitter = CapabilityExtractor(nodes, jd.ml_nodes), CapabilityFitAssembler(jd)
    behavior, honeypots, ranker = BehavioralScorer(jd, as_of), HoneypotDetector(), TopKRanker(k)
    for c in candidates:
        cap = extractor.extract(c)
        ranker.add(c, cap, fitter.assemble(c, cap), behavior.score(c), honeypots.detect(c))
    return [e.candidate.candidate_id for e in ranker.finalize()]


def _perturbed_nodes(nodes, rng, spread):
    weights = [n.importance * rng.uniform(1 - spread, 1 + spread) for n in nodes]
    top = max(weights)
    return [OntologyNode(name=n.name, importance=w / top, strong_phrases=n.strong_phrases,
                         weak_phrases=n.weak_phrases) for n, w in zip(nodes, weights)]


def _perturbed_jd(jd, rng, shift):
    bands = [b.model_copy(update={"factor": min(1.0, max(0.0, b.factor + rng.uniform(-shift, shift)))})
             for b in jd.experience_bands]
    return jd.model_copy(update={"experience_bands": bands})


def _spearman(base, other):
    shared = [cid for cid in base if cid in other]
    n = len(shared)
    if n < 2:
        return float("nan")
    ra = {cid: i for i, cid in enumerate(sorted(shared, key=base.index))}
    rb = {cid: i for i, cid in enumerate(sorted(shared, key=other.index))}
    d2 = sum((ra[c] - rb[c]) ** 2 for c in shared)
    return 1 - 6 * d2 / (n * (n * n - 1))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--candidates", required=True, type=Path)
    p.add_argument("--sample", type=int, default=8000, help="first N candidates")
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--spread", type=float, default=0.15, help="relative importance perturbation")
    p.add_argument("--shift", type=float, default=0.05, help="absolute factor perturbation")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    candidates = list(itertools.islice(CandidateReader(args.candidates), args.sample))
    as_of = latest_activity_date(args.candidates)
    nodes = load_ontology(paths.ONTOLOGY_PATH)
    jd = build_jd_profile(nodes, paths.JD_RUBRIC_PATH)
    k = scoring.SUBMISSION_ROW_COUNT
    baseline = _rank(candidates, nodes, jd, k, as_of)

    rng = random.Random(args.seed)
    original_depth = {name: getattr(scoring, name) for name in _ML_DEPTH_NAMES}
    overlaps = {10: [], 50: [], 100: []}
    correlations = []
    try:
        for _ in range(args.trials):
            trial_nodes = _perturbed_nodes(nodes, rng, args.spread)
            trial_jd = _perturbed_jd(build_jd_profile(trial_nodes, paths.JD_RUBRIC_PATH), rng, args.shift)
            for name, value in original_depth.items():
                lo, hi = _ML_DEPTH_RANGE
                setattr(scoring, name, min(hi, max(lo, value + rng.uniform(-args.shift, args.shift))))
            ranked = _rank(candidates, trial_nodes, trial_jd, k, as_of)
            for top in overlaps:
                overlaps[top].append(len(set(baseline[:top]) & set(ranked[:top])) / top)
            correlations.append(_spearman(baseline, ranked))
    finally:
        for name, value in original_depth.items():
            setattr(scoring, name, value)

    print(f"sample={len(candidates)} trials={args.trials} spread=±{args.spread:.0%} "
          f"shift=±{args.shift} seed={args.seed}")
    for top, values in overlaps.items():
        print(f"top-{top:<3} mean overlap {sum(values) / len(values):.1%}  (min {min(values):.0%})")
    print(f"spearman on shared top-{k}: {min(correlations):.2f} - {max(correlations):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
