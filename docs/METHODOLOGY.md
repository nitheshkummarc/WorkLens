# Methodology

## Overview

WorkLens ranks 100,000 candidate profiles against a structured job specification and returns the top 100 — in under two minutes, on a single CPU core, with no GPU, no network access, and no pre-computation. It is a deterministic, rule-based scoring engine.

The core design principle: **score what a candidate demonstrably did in their career history, not what they list as skills.** A description of building a recommendation system earns full credit; listing "RAG" as a skill earns half. This asymmetry is the primary defense against keyword-stuffed profiles.

---

## Scoring Pipeline

`final = 0` if the profile is provably impossible; otherwise `final = capability_fit × behavioral_multiplier`.

### 1. Job Specification → Structured Rubric

The job description is encoded as nine weighted capability areas (retrieval, embeddings, ranking, evaluation, production deployment, NLP, fine-tuning, data pipelines, distributed systems) with node-specific importance weights. Requirements the job explicitly rejects — pure research backgrounds, consulting-only careers, framework-tutorial evidence — become anti-signal penalties. All vocabulary lives in data files, not hardcoded in logic.

### 2. Capability Extraction from Evidence

For each capability area, evidence is sourced from two tiers:

- **Demonstrated** (career titles + descriptions): work someone actually did → full credit (1.0)
- **Claimed** (summary, headline, skills list): self-asserted → half credit (0.5), unless backed by a platform assessment score ≥ 50

The importance-weighted mean of all node strengths produces `base_capability ∈ [0, 1]`.

### 3. Fit Adjustment

The base capability is modulated by:

- **Experience factor** — the role targets 5–9 years; under- and over-experience are penalized
- **Domain depth factor** — rewards sustained tenure in relevant roles (≥4 years → 1.10×)
- **Anti-signal penalties** — subtractive, capped at 0.50
- **Nice-to-have bonus** — small additive reward for supplementary capabilities, capped at 0.10

### 4. Behavioral Multiplier

Twenty-three platform engagement signals are distilled into eight weighted sub-scores (recency, responsiveness, openness, interview history, offer history, logistics, demand, trust), producing a multiplier in [0.50, 1.00]. Behavior rescales capability — a strong but inactive candidate is halved, not dropped.

Recency is measured against a fixed reference date (the dataset's latest `last_active_date`), not the system clock. Missing or sentinel values (e.g., `offer_acceptance_rate == -1`) map to a neutral score. Absence of a signal is never treated as negative.

### 5. Impossibility Detection

Two conservative rules detect provably-impossible profiles:

- **H1:** ≥3 skills claimed at advanced/expert with zero months of use
- **H2:** Total career tenure exceeds `years_of_experience × 18 + 12` months

These fire on ~0.04% of the pool. Flagged candidates receive a final score of zero. Keyword-stuffers with plausible timelines are handled by the capability and anti-signal stages, not here.

### 6. Top-K Selection and Explanation

A bounded min-heap (size 100) retains only the highest-scoring candidates during the single streaming pass — O(N log K) time, O(K) memory, no full sort. Each retained candidate receives a one-sentence explanation built entirely from their own profile fields. A hard validation gate checks every output constraint before writing the CSV.

---

## Design Properties

- **Performance:** One pass over the input, fixed-size heap — ~2 minutes for 100K records on a single CPU core.
- **Determinism:** Same input always produces byte-identical output. No wall-clock dependency, no randomness, no floating-point order sensitivity.
- **Explainability:** Every ranking includes a fact-grounded reason referencing the candidate's own data. No fabricated claims.
- **Robustness:** Perturbing scoring weights by ±15% keeps ~97% of the top 10 stable — the output does not hinge on any single parameter.
