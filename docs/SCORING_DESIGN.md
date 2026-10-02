# Scoring Design

Specification of every formula, constant and decision boundary in WorkLens. Values match `shared/config/scoring.py`, `data/ai_capability_ontology.json` and `data/jd_rubric.json`.

---

## Core Formula

```
final_score(candidate):
    if honeypot(candidate):
        return 0.0
    return round(capability_fit(candidate) × behavioral_multiplier(candidate), 6)
```

The same input always produces a byte-identical output: there is no randomness and no external state. Recency is measured against a reference date taken from the input (the latest `last_active_date`), not the clock.

---

## 1. Capability Scoring

### 1.1 Base capability

```
base_capability = Σ(importance[n] × strength[n]) / Σ(importance[n])
```

| Strength | Source label | Evidence |
|----------|--------------|----------|
| 1.0 | `career` | strong phrase in career history (titles and descriptions) |
| 1.0 | `skill_verified` | advanced/expert skill matching any of the node's phrases, assessment ≥ 50, **and** at least a weak phrase for the node in career history |
| 0.5 | `claimed` | strong phrase only in summary, headline or skills; or a verified skill with no career support |
| 0.5 | `career_weak` | only a weak phrase in career history |
| 0.0 | `none` | no evidence, or only a weak phrase in self-reported text |

Rules are checked in the order shown; the first that applies sets the strength. Skills with an assessment score below 30 are removed before matching.

**Why verified skills need career support.** An assessment shows that someone knows a topic. The job description asks for work "deployed to real users", which an assessment cannot show. So an assessed skill upgrades existing career evidence to full credit, but on its own counts as a claim. Before this rule, 25 of the 46 weak top-100 entries in the review (RANKING_REVIEW.md) had core credit from assessed skills alone. A verified skill may still match through a weak phrase ("Recommendation Systems" for N3); 114 of 366 verified matches on the pool do.

Separating demonstrated from self-reported evidence is the main defence against keyword stuffing. An HR Manager whose career text has no AI content but who lists nine AI skills scores a final score of about 0.22. The full-pool top-100 cutoff is about 0.58.

### 1.2 Phrase matching

- Every phrase must start at a word boundary, so "search" does not match inside "research".
- Phrases of four characters or fewer must also end at a word boundary, so "rag" does not match "ragged" and "map" does not match "roadmap".
- Longer phrases may run into a longer word, so "pipeline" matches "pipelines".
- A trailing `*` marks a stem: "tokeniz\*" matches "tokenizer" and "tokenization".
- **Negation and comparison.** A match is ignored when one of `NEGATION_CUES` (than, toward, towards, not, no, never, without) appears among the `NEGATION_WINDOW_WORDS` (3) words before it in the same clause. On the provided pool this suppresses exactly four patterns, all correctly:

| Suppressed phrase | Context | Role texts |
|---|---|---|
| ranking system | "lighter weight **than** ranking systems at FAANG" | 369 |
| nlp, llm | "transitioning **toward** NLP/LLM work" | 366 |
| production | "more on the modeling side **than** the productionization" | 359 |
| benchmark | "ship models **without** offline benchmarks" | 43 |

### 1.3 Capability nodes

| Node | Weight | Strong phrases (examples) | Weak phrases |
|------|--------|---------------------------|--------------|
| N1 Retrieval & Search | 1.0 | recommendation system, search relevance, semantic search, RAG, elasticsearch, hybrid search, search and discovery, matching layer, query understanding, index refresh | search, relevance, personalization, query |
| N2 Embeddings & Vector | 1.0 | embeddings, sentence-transformers, vector database, vector search, FAISS, pgvector, pinecone, dense retrieval, two-tower | vector, similarity, encoder |
| N3 Ranking & Recommendation / LTR | 1.0 | learning to rank, LTR, lambdamart, re-ranking, ranking model, recommendation engine, ranking layer, ranking algorithm | ranking, scoring, recommend |
| N4 Evaluation & Experimentation | 0.9 | NDCG, MRR, MAP, precision@k, A/B test, offline-online correlation, evaluation framework, evaluation methodology, offline metrics, offline experimentation | evaluation, metrics, benchmark, experiment |
| N5 ML Production & Deployment | 1.0 | deployed to production, model serving, feature store, real users, monitoring, drift | deployed, production, pipeline, serving |
| N6 NLP / IR foundations | 0.7 | NLP, text classification, NER, tokenization, language model | text, language, embedding |
| N7 LLM & Fine-tuning | 0.3 | fine-tuning, LoRA, QLoRA, PEFT, instruction tuning, RLHF | llm, prompt, gpt |
| N8 Data & Feature pipelines | 0.5 | data pipeline, Spark, Airflow, feature engineering, ETL, Kafka | data, pipeline, batch, stream |
| N9 Distributed / Scale / Inference-opt | 0.4 | distributed training, latency optimization, quantization, throughput, sharding | scale, latency, optimize |

Weight rationale:
- **1.0** (N1, N2, N3, N5): the core build work of the role.
- **0.9** (N4): evaluation is required by the job description but supports the core work.
- **0.7** (N6): foundational NLP/IR.
- **0.5** (N8): data engineering supports the role but is not its focus.
- **0.4** (N9) and **0.3** (N7): desirable, not required. N7 and N9 are also the nice-to-have nodes (section 5).

The plain-language phrases (search and discovery, matching layer, ranking layer, evaluation framework, …) name the job description's core concepts without buzzwords, following its line 073: a candidate who built a recommendation system is a fit even without the words "RAG" or "Pinecone". Each was checked against every distinct text in the pool and matches only search, ranking or evaluation work.

---

## 2. Capability Fit

```
capability_fit = clamp01((effective_base × E × D − anti_penalty + nice_bonus) / fit_max)
effective_base = min(base, 0.30) if a hard-DQ anti-signal fires, else base
fit_max        = max(E) × ML_DEPTH_FACTOR_HIGH + nice_bonus_cap = 1.0 × 1.10 + 0.10 = 1.2
```

Dividing by `fit_max` keeps the score in [0, 1] without clamping the strongest profiles to the same value. Before this change, 8 of the top 10 sat at exactly 1.0 and only behaviour ordered them.

### 2.1 Experience factor (E)

| Years of experience | Factor |
|--------------------|--------|
| < 3 | 0.70 |
| 3 to < 5 | 0.90 |
| **5 to < 9** | **1.00** |
| 9 to < 12 | 0.95 |
| ≥ 12 | 0.85 |

### 2.2 ML-depth factor (D)

A role is ML-relevant if its title or description matches any phrase of the rubric's `ml_nodes` (N1-N7 for this role). `ml_relevant_months` is the sum of those roles' durations, capped at the candidate's stated experience.

| ML years | Factor | Meaning |
|----------|--------|---------|
| ≥ 4 | 1.10 | meets the role's 4-5 years of applied ML |
| 2 to < 4 | 1.00 | neutral |
| 1 to < 2 | 0.95 | shallow |
| < 1, with capability evidence | 0.85 | recent pivot or self-reported only |
| < 1, no capability evidence | 1.00 | base is already near zero; no double penalty |

---

## 3. Anti-Signal Penalties

Subtractive; the total is capped at 0.50.

| Key | Fires when | Penalty | Hard DQ |
|-----|-----------|---------|---------|
| `research_only` | a research title (research scientist, postdoc, research intern, …) and no production term anywhere in the career | −0.25 | yes (base capped at 0.30) |
| `consulting_only` | every employer is a listed consulting firm | −0.125 | no |
| `langchain_only` | LLM-wrapper terms in career text, no earlier-ML terms, **and** no retrieval/ranking career evidence (`retrieval_nodes`) | −0.20 | no |
| `framework_tutorial` | tutorial/bootcamp/course terms anywhere, and no strong phrase in career history | −0.15 | no |
| `title_chasing` | at least 3 **completed** roles, each shorter than 18 months (the current role is excluded) | −0.10 | no |
| `no_recent_handson` | current title is senior/managerial and the current role description has no production term | −0.10 | no |
| `cv_speech_robotics` | vision/speech/robotics terms in career text and no evidence at all for the rubric's `ir_nlp_nodes` | −0.15 | no |

`research_only` is the only hard disqualifier because the role requires production deployment. With both the cap and the penalty applied, a research-only profile ends near zero.

**`langchain_only` and retrieval work.** The job description's exemption is "substantial pre-LLM-era ML production experience … people who understood retrieval and ranking". Before the retrieval-evidence check, all 12 firings on the pool hit candidates with production retrieval work (for example FAISS semantic search plus a later RAG chatbot); one was pushed to rank 1,095.

**Firing on the provided pool.** `consulting_only` fires on 9,745 candidates and `title_chasing` on 1,487. The other five rules fire on none. The pool's only research-flavoured title is "AI Research Engineer"; no current title is managerial; profiles with vision terms or LLM-wrapper terms always carry retrieval or NLP evidence. The rules are kept because they encode requirements from the job description, and each is tested firing and not firing (`tests/test_anti_signals.py`).

---

## 4. Behavioral Multiplier

```
behavioral_raw        = Σ(weight[k] × sub_score[k])            weights sum to 1.0
behavioral_multiplier = 0.50 + 0.50 × behavioral_raw          in [0.50, 1.00]
                        0.50 if unavailable
                        × 0.80 if outside the home country
```

### 4.1 Sub-scores

| Sub-score | Weight | Signals | Scoring |
|-----------|--------|---------|---------|
| Recency | 0.30 | days since `last_active_date` | ≤30d 1.0 · ≤60d 0.9 · ≤90d 0.75 · ≤180d 0.5 · else 0.25 |
| Responsiveness | 0.25 | `recruiter_response_rate`, `avg_response_time_hours` | rate × time factor (≤24h 1.0 · ≤72h 0.9 · else 0.8) |
| Open to work | 0.10 | `open_to_work_flag` | true 1.0 · false 0.4 |
| Interview | 0.10 | `interview_completion_rate` | value as given |
| Offer | 0.05 | `offer_acceptance_rate` | value as given; −1 (no history) → 0.5 |
| Logistics | 0.10 | notice period, location, work mode | mean of three factors (below) |
| Demand | 0.07 | `saved_by_recruiters_30d`, `search_appearance_30d` | mean of log1p-scaled counts, capped at 20 and 500 |
| Trust | 0.03 | `verified_email`, `verified_phone`, `linkedin_connected` | fraction true |

### 4.2 Logistics factors

| Factor | Scoring |
|--------|---------|
| Notice period | ≤30d 1.0 · ≤60d 0.8 · ≤90d 0.6 · else 0.4 |
| Location | office city 1.0 · other welcomed city 0.85 · in the home country and willing to relocate 0.85 · in the home country, not relocating 0.55 · outside 0.30 |
| Work mode | a preferred mode (hybrid, flexible, onsite) 1.0 · otherwise 0.7 |

Cities, the home country and the preferred work modes come from the rubric's `logistics` section.

### 4.3 Availability rules

- **Unavailable:** inactive for more than `UNAVAILABLE_DAYS` (180) or a recruiter response rate below `UNAVAILABLE_RESPONSE_RATE` (0.10). The multiplier is set to the floor (0.50). This implements the job description's line 074: "a perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is, for hiring purposes, not actually available".
- **Outside the home country:** the multiplier is scaled by `OUTSIDE_HOME_COUNTRY_FACTOR` (0.80). The employer does not sponsor work visas, and the location factor alone moved the score by only about 1-2%.

On the provided pool 20,315 candidates are unavailable and 24,887 are outside India.

### 4.4 Signals not used

`profile_completeness_score`, `signup_date`, `profile_views_received_30d`, `applications_submitted_30d`, `connection_count`, `endorsements_received`, `expected_salary_range_inr_lpa` and `github_activity_score`. `skill_assessment_scores` is used by capability scoring. See DESIGN_DECISIONS.md for the reasons.

### 4.5 Why a multiplier

- Capability stays the primary ranking axis; behaviour reorders candidates of similar capability.
- The floor keeps a strong but unavailable candidate in the list at a reduced score rather than removing them.

---

## 5. Nice-to-Have Bonus

+0.03 for each nice-to-have node (N7, N9) with any evidence, capped at +0.10.

---

## 6. Honeypot Detection

| Rule | Condition | Meaning |
|------|-----------|---------|
| H1 | ≥ 3 skills at advanced/expert with `duration_months == 0` | claims expertise in skills never used |
| H2 | `Σ duration_months > years_of_experience × 18 + 12` | more career history than the stated experience allows, with slack for overlapping roles |

On the provided pool these flag 43 candidates (0.043%): 21 by H1 and 22 by H2. A flagged candidate's final score is 0.

---

## 7. Ranking

```
for each candidate in the input stream:
    fit   = capability_fit(candidate)
    M     = behavioral_multiplier(candidate)
    final = 0.0 if honeypot else round(fit × M, 6)
    offer (final, reversed candidate_id) to a min-heap of size K (default 100, --top-k)

sort the retained K by final descending, candidate_id ascending; assign ranks 1..K
```

O(N log K) time. Equal scores keep the smaller candidate id, both during eviction and in the final order, for any id format.

### Output schema

| Column | Type | Constraint |
|--------|------|-----------|
| `candidate_id` | string | matches `CANDIDATE_ID_PATTERN`, unique, present in the input pool |
| `rank` | int | 1..K, each exactly once |
| `score` | float | six decimals, non-increasing with rank |
| `reasoning` | string | one line, built from the candidate's own data |

### Reasoning

```
first half of the list:   "{title}, {years} yrs — {strengths}. {activity}. Concern: {gap}."
second half:              "{title}, {years} yrs — main gap: {gap}. {strengths}; {activity}."
no gap found:             "{title}, {years} yrs — {strengths}. {activity}. No material gap identified."
```

- **Strengths** lists up to three capability areas, the first with its evidence phrase, plus applied-ML tenure when it is `REASON_ML_TENURE_YEARS` (4) or more.
- **Activity** states the days since the candidate was last active, the recruiter response rate and the open-to-work status.
- **The gap** is chosen in the order given in ARCHITECTURE.md, Stage 7. Anti-signal wording comes from the rubric's `anti_signal_concerns`.
- **Partial evidence** is worded by source: "only self-reported" or "only indirect … in career history".

---

## 8. Configuration Reference

| Source | Contains |
|--------|----------|
| [`shared/config/scoring.py`](../shared/config/scoring.py) | penalties, weights, bands, thresholds, caps, negation cues, availability rules, reasoning thresholds |
| [`shared/config/run_config.py`](../shared/config/run_config.py) | candidate id format |
| [`data/ai_capability_ontology.json`](../data/ai_capability_ontology.json) | capability nodes, phrase lists, importances |
| [`data/jd_rubric.json`](../data/jd_rubric.json) | nice-to-have and ML-relevant nodes, anti-signal vocabulary and wording, consulting firms, logistics (home country, cities, work modes) |

To adapt WorkLens to another role, edit the two JSON files and, if needed, the constants. To use a pool with a different id format, change `CANDIDATE_ID_PATTERN`. No code changes are needed.

---

## 9. Known Limitations

- **Vocabulary coverage.** Phrase matching can miss work described outside the ontology's phrases. Plain-language forms reduce this but do not remove it; there is no semantic (embedding) recall.
- **Negation is a heuristic.** The three-word cue window handles comparisons and stated non-experience; it does not parse sentences.
- **Calibration.** Weights are reasoned from the job description, not fitted to labelled data. `tools/sensitivity.py` measures how much the ranking moves when they are perturbed.
- **Assessment sparsity.** Only 24% of candidates have any `skill_assessment_scores`, so career-text evidence carries most of the anti-gaming weight.
- **Honeypot coverage.** Some impossibility patterns (for example, tenure longer than an employer has existed) cannot be checked from the available fields.
- **Inactive anti-signals.** Five of the seven anti-signal rules do not fire on the provided pool (section 3).
- **Must-haves are weighted, not required.** A candidate with broad production ML but no retrieval or embedding work can still reach the lower part of the top 100 (RANKING_REVIEW.md lists the cases).
