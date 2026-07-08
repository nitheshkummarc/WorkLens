# Scoring Design

Technical specification for WorkLens's deterministic scoring pipeline. This document covers every formula, constant, and decision boundary in the system.

---

## Core Formula

```
final_score(candidate):
    if honeypot(candidate):
        return 0.0
    return capability_fit(candidate) × behavioral_multiplier(candidate)
```

All scoring is deterministic — the same input always produces byte-identical output. No randomness, no wall-clock dependency, no external state.

---

## 1. Capability Scoring

### 1.1 Base Capability

Each candidate is scored against 9 capability nodes. Every node receives a strength based on evidence quality:

```
base_capability = Σ(importance[n] × strength[n]) / Σ(importance[n])
```

**Evidence tiers — how strength is assigned:**

| Strength | Evidence Source | Rationale |
|----------|---------------|-----------|
| **1.0** | Strong phrase found in career history (titles + descriptions) | Demonstrated work — highest confidence |
| **1.0** | Skill at advanced/expert with assessment score ≥ 50 | Platform-verified proficiency |
| **0.5** | Strong phrase found only in summary, headline, or skills list | Claimed but not demonstrated |
| **0.5** | Weak phrase found in career history | Ambiguous evidence in a credible context |
| **0.0** | No match, or skill with assessment < 30 | No evidence, or below-threshold claim (dropped) |

> **Why this matters:** The demonstrated-vs-claimed split is the core anti-gaming mechanism. A candidate who describes building a recommendation system in their career history earns full credit (1.0). A candidate who merely lists "RAG" as a skill earns half (0.5). This asymmetry is what prevents keyword-stuffed profiles from ranking above genuinely experienced candidates.

### 1.2 Capability Nodes

Nine capability areas, each weighted by importance to the role:

| Node | Weight | Strong Phrases (examples) | Weak Phrases |
|------|--------|--------------------------|-------------|
| N1 — Retrieval & Search | 1.0 | recommendation system, search relevance, ranking system, semantic search, RAG, elasticsearch | search, relevance, query |
| N2 — Embeddings & Vector | 1.0 | embeddings, sentence-transformers, vector database, FAISS, pinecone, dense retrieval, two-tower | vector, similarity, encoder |
| N3 — Ranking & LTR | 1.0 | learning to rank, lambdamart, re-ranking, ranking model, recommendation engine | ranking, scoring |
| N4 — Evaluation | 0.9 | NDCG, MRR, precision@k, A/B test, offline-online correlation | evaluation, metrics, benchmark |
| N5 — Production Deployment | 1.0 | deployed to production, model serving, feature store, real users, monitoring, drift | deployed, pipeline, serving |
| N6 — NLP / IR Foundations | 0.7 | NLP, text classification, NER, tokenization, language model | text, language |
| N7 — Fine-tuning | 0.3 | fine-tuning, LoRA, QLoRA, PEFT, instruction tuning, RLHF | prompt, GPT |
| N8 — Data & Feature Pipelines | 0.5 | data pipeline, Spark, Airflow, feature engineering, ETL, Kafka | data, pipeline, batch |
| N9 — Distributed / Scale | 0.4 | distributed training, latency optimization, quantization, throughput, sharding | scale, latency |

**Weight rationale:**
- **1.0 nodes** (N1, N2, N3, N5) are the core build deliverables — retrieval, embeddings, ranking, and production deployment
- **0.9** (N4) — evaluation is a non-negotiable supporting discipline, just below the build core
- **0.7** (N6) — foundational NLP/IR skills, valuable but not the primary deliverable
- **0.5** (N8) — data engineering supports the pipeline but isn't the role's focus
- **0.4** (N9) — scale/distributed is desirable but not required
- **0.3** (N7) — fine-tuning is a nice-to-have, lowest priority

All phrase families and weights are externalized in [`data/ai_capability_ontology.json`](../data/ai_capability_ontology.json) — no vocabulary is hardcoded in scoring logic.

### 1.3 Capability Fit

The base capability is adjusted through four modifiers to produce the final capability fit:

```
capability_fit = clamp₀₁(effective_base × E × D − anti_penalty + nice_bonus)
```

Where `effective_base = min(base, 0.30)` if a hard disqualifier fires, otherwise `effective_base = base`.

---

## 2. Experience Factor (E)

Captures total career seniority. The role targets 5–9 years; candidates outside that range are gently penalized:

| Years of Experience | Factor | Rationale |
|--------------------|--------|-----------|
| < 3 | 0.70 | Insufficient seniority for a senior role |
| 3 – 5 | 0.90 | Approaching but below the ideal range |
| **5 – 9** | **1.00** | **Ideal range — no adjustment** |
| 9 – 12 | 0.95 | Slight over-experience; may be less hands-on |
| > 12 | 0.85 | Significantly over-experienced for the level |

---

## 3. Domain Depth Factor (D)

Distinguishes total seniority from domain-specific depth. Two candidates with identical capability evidence but different tenure in relevant roles should be ranked differently.

A career history role is **domain-relevant** if its title or description matches any strong or weak phrase from nodes N1–N7 (the core technical nodes). `domain_months = Σ duration_months` over all matching roles.

| Domain Years | Factor | Rationale |
|-------------|--------|-----------|
| ≥ 4 | **1.10** | Deep domain tenure — meets the ideal profile |
| 2 – 4 | 1.00 | Solid but below ideal depth — neutral |
| 1 – 2 | 0.95 | Real but shallow tenure — mild discount |
| < 1 (with capability signal) | 0.85 | Recent pivot or skills-only claim — demote |
| No relevant roles (capability ≈ 0) | 1.00 | Neutral — base capability already handles this |

**Properties:**
- D ∈ [0.85, 1.10] — bounded and safe by construction
- Multiplicative on `base_capability` — only meaningfully re-orders candidates who already have a real base score
- `clamp₀₁` prevents the 1.10 boost from exceeding 1.0

---

## 4. Anti-Signal Penalties

Subtractive penalties for negative indicators detected in the candidate's profile. Total penalty is capped at 0.50.

| Anti-Signal | Detection | Penalty | Hard DQ? |
|------------|-----------|---------|----------|
| Pure research, no production | All titles/descriptions are research/academic; no production deployment evidence | −0.25 | **Yes** (caps base at 0.30) |
| Consulting-only career | Every employer is a consulting firm and no product company experience | −0.125 | No |
| Wrapper-only, no fundamentals | Only recent wrapper/API terms, no pre-existing production evidence | −0.20 | No |
| Framework-tutorial profile | Skills/descriptions dominated by tutorial/demo/bootcamp terms | −0.15 | No |
| Title-chasing | ≥3 roles each under 18 months with rising seniority titles | −0.10 | No |
| No recent hands-on (senior) | Current title is management/architect with no recent individual contributor signal | −0.10 | No |
| Domain mismatch (CV/Speech/Robotics) | Strong vision/speech/robotics evidence with zero retrieval/NLP/IR nodes | −0.15 | No |

> **Why "pure research" is the only hard DQ:** It carries both the 0.30 cap and the −0.25 penalty. The cap bounds how high a research-only profile can register; the penalty pushes it further down within that ceiling. After experience adjustment: `clamp₀₁(min(base, 0.30) × E − 0.25 + nice) ≈ 0.05`. This reflects the role's strongest non-honeypot requirement — production deployment is non-negotiable.

### Nice-to-Have Bonus

Small additive bonus for supplementary capability nodes (N7 Fine-tuning, N9 Distributed/Scale):

- **+0.03** per qualifying node
- **Cap: +0.10** total

---

## 5. Behavioral Multiplier

Converts 23 platform engagement signals into a rescaling factor. Behavior modifies capability — it never overrides it.

```
behavioral_multiplier = 0.50 + 0.50 × behavioral_raw     ∈ [0.50, 1.00]
behavioral_raw = Σ(weight[k] × sub_score[k])              ∈ [0, 1], weights sum to 1.0
```

### Sub-Scores

| Sub-Score | Weight | Input Signals | Scoring |
|-----------|--------|--------------|---------|
| **Recency** | 0.30 | `last_active_date` vs. fixed reference date | ≤30d → 1.0 · ≤60d → 0.9 · ≤90d → 0.75 · ≤180d → 0.5 · else → 0.25 |
| **Responsiveness** | 0.25 | `recruiter_response_rate`, `avg_response_time_hours` | response_rate × time_factor (≤24h → 1.0 · ≤72h → 0.9 · else → 0.8) |
| **Open to Work** | 0.10 | `open_to_work_flag` | true → 1.0 · false → 0.4 |
| **Interview** | 0.10 | `interview_completion_rate` | Direct value; missing → 0.5 (neutral) |
| **Offer** | 0.05 | `offer_acceptance_rate` | Direct value; −1 sentinel → 0.5 (neutral) |
| **Logistics** | 0.10 | `notice_period_days`, `location`, `preferred_work_mode` | Mean of three sub-factors (see below) |
| **Demand** | 0.07 | `saved_by_recruiters_30d`, `search_appearance_30d` | Log-normalized mean, capped |
| **Trust** | 0.03 | `verified_email`, `verified_phone`, `linkedin_connected` | Fraction of verifications that are true |

### Logistics Sub-Factors

| Factor | Scoring |
|--------|---------|
| **Notice period** | ≤30d → 1.0 · ≤60d → 0.8 · ≤90d → 0.6 · else → 0.4 |
| **Location** | Office cities (Pune/Noida) → 1.0 · Target cities (Hyderabad/Mumbai/Delhi NCR) → 0.85 · India + willing to relocate → 0.85 · India, not relocating → 0.55 · Outside India → 0.30 |
| **Work mode** | Hybrid/onsite → 1.0 · Remote → 0.7 |

### Missing Signal Handling

All `-1` sentinels and absent fields map to **neutral** (typically 0.5), never to 0. Absence of a signal is never treated as a negative indicator.

### Why a Multiplier (Not Additive)

- Keeps capability as the **primary ranking axis** — behavioral signals only re-order candidates within similar capability bands
- A multiplier floor of 0.50 ensures strong but inactive candidates are halved, not dropped
- Two equally-capable candidates are separated by up to 2× based on availability and engagement

---

## 6. Honeypot Detection

Two high-precision rules detect provably-impossible profiles. Any match sets `final_score = 0.0`.

| Rule | Condition | Interpretation |
|------|-----------|---------------|
| **H1** — Expert-but-unused cluster | ≥3 skills at advanced/expert with `duration_months == 0` | Claims expertise in skills they have never used |
| **H2** — Tenure exceeds working life | `Σ career_months > years_of_experience × 18 + 12` | More career history than their stated working life allows (generous slack for overlapping roles) |

**Design properties:**
- **High precision, conservative thresholds** — fires on ~0.04% of the pool. Favors false negatives over false positives (burying a real candidate is worse than missing one impossible profile)
- **Keyword-stuffers are NOT honeypots** — a wrong-title profile with many listed skills is sunk by the capability scoring (unverified skills capped at 0.5) and anti-signal penalties, not by honeypot detection
- These rules are reserved for *provably impossible* profiles only

---

## 7. Final Ranking

```
For each candidate in the input stream:
    base   = base_capability(candidate)                      # Importance-weighted node strengths
    if hard_dq: base = min(base, 0.30)                       # Cap for "pure research, no production"
    fit    = clamp₀₁(base × E × D − anti_penalty + nice)    # Apply all modifiers
    M      = 0.50 + 0.50 × behavioral_raw                   # Behavioral multiplier
    final  = 0.0 if honeypot else fit × M                    # Final score

Top-K selection via streaming bounded min-heap (K=100):
    → O(N log K) time, O(K) memory
    → Score descending, candidate ID ascending for ties
    → Heap carries full scoring context per candidate (no second pass)
```

### Output Schema

| Column | Type | Constraint |
|--------|------|-----------|
| `candidate_id` | string | `CAND_XXXXXXX` format, must exist in pool, unique |
| `rank` | int | 1–100, each exactly once |
| `score` | float | `round(final, 6)`, non-increasing with rank |
| `reasoning` | string | 1–2 sentences, fact-grounded, varied per candidate |

### Reasoning Generation

Each ranked candidate receives a deterministic, template-based explanation:

```
"{title}, {years} yrs — {strengths with evidence}. {behavioral note}. Concern: {concern}."
```

- Every claim references the candidate's own fields or a matched evidence phrase
- Content varies because capability nodes, evidence, tenure, and concerns differ per candidate
- Tone follows rank — top candidates lead with strengths, lower-ranked candidates lead with concerns

---

## 8. Configuration Reference

All constants referenced in this document are centralized in two locations:

| Source | Contains | File |
|--------|----------|------|
| Scoring constants | Penalties, weight tables, experience bands, thresholds, behavioral weights | [`shared/config/scoring.py`](../shared/config/scoring.py) |
| Job specification | Capability node definitions, phrase families, importance weights | [`data/ai_capability_ontology.json`](../data/ai_capability_ontology.json) |
| Role vocabulary | Anti-signal keywords, consulting companies, target cities, logistics buckets | [`data/jd_rubric.json`](../data/jd_rubric.json) |

To adapt WorkLens to a different role: modify the JSON data files and update the constants in `scoring.py`. No structural code changes are required.

---

## 9. Known Limitations

Documented transparently:

- **Vocabulary coverage** — Rule-based matching can miss candidates whose work is phrased outside the ontology's phrase families. Mitigated by including plain-language forms (e.g., "built a recommendation system" matches without buzzwords)
- **Missing-signal assumption** — The neutral mapping for absent signals assumes missingness is non-informative. If missingness correlates with candidate quality, behavioral scoring may be systematically biased
- **Assessment data sparsity** — Only ~24% of candidates carry any `skill_assessment_scores`. Description-content scoring is the primary anti-gaming mechanism; assessment gating is a secondary defense
- **Honeypot residual risk** — Some impossibility patterns (e.g., company founding date vs. claimed tenure) cannot be verified from the available schema fields
