# Methodology

## Overview

WorkLens ranks 100,000 candidate profiles against a structured job specification and returns the top 100. It runs in about 17-30 seconds on a single CPU core, with no GPU, no network access and no pre-computation. It is a deterministic, rule-based scoring engine; there is no trained model.

The central rule: **score what a candidate did in their career history, not what they list as skills.** Describing a recommendation system in a role description earns full credit for that capability; listing "RAG" as a skill earns half. This is the main defence against keyword-stuffed profiles.

---

## Scoring Pipeline

`final = 0` if the profile is internally impossible; otherwise `final = capability_fit × behavioral_multiplier`, rounded to six decimals.

### 1. Job specification to rubric

The job description is encoded as nine weighted capability areas: retrieval, embeddings, ranking, evaluation, production deployment, NLP, fine-tuning, data pipelines and distributed systems. Patterns the job explicitly rejects (research-only backgrounds, consulting-only careers, tutorial-level evidence, and others) become anti-signal penalties. All vocabulary lives in data files; all numbers live in `shared/config/scoring.py`.

### 2. Capability evidence

For each capability area, evidence is graded by where it appears:

- **Career history** (titles and descriptions): a specific technical phrase earns full credit (1.0). A generic phrase such as "production" or "pipeline" earns half (0.5).
- **Self-reported** (summary, headline, skills): a specific phrase earns half credit (0.5). An advanced/expert skill with a platform assessment of 50 or more earns full credit when the career history at least loosely supports it; otherwise it also counts as half. Skills with an assessment below 30 are ignored.
- **Context:** a phrase inside a comparison or a statement of non-experience ("lighter weight than ranking systems", "transitioning toward NLP") is not counted.

The importance-weighted mean of the node strengths gives `base_capability` in [0, 1].

### 3. Fit adjustment

The base capability is adjusted by:

- **Experience factor**: the role targets 5-9 years; shorter and much longer careers are discounted.
- **ML-depth factor**: rewards years spent in ML-relevant roles (1.10 at four years or more, 0.85 for under a year).
- **Anti-signal penalties**: subtracted, capped at 0.50 in total.
- **Nice-to-have bonus**: a small addition for supplementary capabilities, capped at 0.10.

The result is divided by its largest possible value (1.2), so `capability_fit` stays in [0, 1] and the strongest profiles keep distinct scores.

### 4. Behavioral multiplier

Fourteen of the 23 platform signals are combined into eight weighted sub-scores (recency, responsiveness, open to work, interview completion, offer acceptance, logistics, demand, trust), giving a multiplier in [0.50, 1.00]. Behaviour rescales capability but cannot create it.

Two availability rules follow the job description directly:
- a candidate inactive for more than 180 days or with a recruiter response rate below 10% is treated as unavailable and gets the floor multiplier (0.50);
- a candidate outside the home country has the multiplier scaled by 0.80, because the company does not sponsor work visas.

Recency is measured against a reference date taken from the input (the latest `last_active_date`, or `--as-of`), not the system clock. A missing offer history (`offer_acceptance_rate == -1`) is scored as neutral.

### 5. Impossibility detection

Two conservative rules detect internally impossible profiles:

- **H1:** three or more skills claimed at advanced/expert with zero months of use.
- **H2:** total career tenure exceeds `years_of_experience × 18 + 12` months.

They flag 43 of the 100,000 profiles. A flagged candidate scores zero. Keyword-stuffed profiles with a plausible timeline are handled by the capability and anti-signal stages instead.

### 6. Top-K selection and explanation

A bounded min-heap of size K (100 by default) keeps the highest-scoring candidates during the single pass. Each retained candidate gets a one-line explanation built from their own profile: title, experience, strongest capability areas with an evidence phrase, recent activity, and the most significant gap. A validation step checks every output rule before the CSV is written.

---

## Properties

- **Performance:** one pass over the input plus a fast scan for the reference date; about 17-30 seconds for 100K records on a single core, about 2.8× faster than the submitted version (see PERFORMANCE.md).
- **Match quality:** an independent review against the job description (RANKING_REVIEW.md) grades all 10 of the top 10 as strong matches, and 94 of the top 100 as strong or good.
- **Determinism:** the same input produces a byte-identical CSV. There is no wall-clock dependency and no randomness, and scores are rounded before ranking.
- **Configuration, not code:** the role (ontology and rubric JSON), the numbers (`scoring.py`), the id format and the list size are all configurable; the reference date is detected from the data.
- **Explainability:** every row's reason is assembled from the candidate's own fields, and its wording follows how strong the evidence is.
- **Robustness:** with node importances perturbed by ±15% and the experience and ML-depth factors by ±0.05 (8 trials on an 8,000-candidate sample), the top 10 overlaps the unperturbed top 10 by 96% on average and the top 100 by 96%. Reproduce with `python tools/sensitivity.py --candidates ./candidates.jsonl`.
