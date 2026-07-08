# Scoring Architecture — Frozen Design v1

*Design only — no code. Deterministic, CPU-only, network-off at ranking time.
Inputs: `candidate_schema.json`, `sample_candidates.json`, `job_description` (Senior
AI Engineer), the 23 `redrob_signals`. Embeddings are an optional, gated add-on
(disabled in v1, see §3.6) — the frozen system is complete and shippable without them.*

---

## 0. FROZEN FORMULA BLOCK (locked first)

```
FINAL_SCORE(c):
    if honeypot(c):            final = 0.0
    else:                      final = capability_fit(c) * behavioral_multiplier(c)

capability_fit(c) = clamp01( base_capability(c) * experience_factor(c) * ml_depth_factor(c)
                             - anti_penalty(c) + nice_bonus(c) )
    # hard disqualifier: if hard_dq(c): base_capability := min(base_capability, 0.30)
    # ml_depth_factor ∈ [0.85, 1.10] — relevant-ML-tenure depth (§1.5); multiplicative, so it
    #   only re-orders already-capable candidates and cannot lift a weak base. Set to 1.0 → v1.

base_capability(c) = Σ_n ( importance[n] * node_strength[n](c) ) / Σ_n importance[n]
    node_strength ∈ {0.0, 0.5, 1.0}

behavioral_multiplier(c) = 0.50 + 0.50 * behavioral_raw(c)        # ∈ [0.50, 1.00]
behavioral_raw(c) = Σ_k W[k] * sub_k(c)                           # ∈ [0, 1],  Σ W = 1.0

RANK: sort all candidates by (final DESC, candidate_id ASC); take top 100;
      rank = 1..100; score = round(final, 6)  (non-increasing by construction)
```

**Locked constants**

| Group | Constant | Value |
|---|---|---|
| Node importance | **node-specific weights, not fixed tiers** (per §2) | six distinct values: 1.0 · 0.9 · 0.7 · 0.5 · 0.4 · 0.3 |
| node_strength | none / weak / strong | 0.0 / 0.5 / 1.0 |
| Assessment gates | STRONG_ASSESS / STUFF_ASSESS | ≥50 → strong · <30 → drop skill |
| Experience factor E | <3 / 3–5 / 5–9 / 9–12 / >12 yrs | 0.70 / 0.90 / 1.00 / 0.95 / 0.85 |
| ML-depth factor D | ml_years ≥4 / 2–4 / 1–2 / <1 w/ AI signal / no ML role | 1.10 / 1.00 / 0.95 / 0.85 / 1.00 |
| Anti-penalty | per-signal, total cap | see §1.3 · cap 0.50 |
| Hard DQ cap | base_capability ceiling | 0.30 |
| Nice bonus | per-item / cap | +0.03 / +0.10 |
| Behavioral multiplier floor | B_min | 0.50 |
| Honeypot | result | final = 0.0 (sinks to bottom) |
| Output | rows / tie-break | exactly 100 · candidate_id ascending |

`clamp01(x) = max(0, min(1, x))`. AS_OF date for recency = the dataset's stated
current/most-recent `last_active_date` (deterministic; no wall clock).

---

## 1. AI Engineer competency rubric (from the JD)

Three buckets, taken verbatim from the JD's "absolutely need / like to have / explicitly do NOT want".

> **Importance is modeled as node-specific weights, not fixed tiers.** Each of the 9
> ontology nodes carries its own weight in §2 (six distinct values: 1.0, 0.9, 0.7, 0.5,
> 0.4, 0.3), chosen from the JD's own emphasis — not bucketed into a small fixed tier set.
> The bucket words below ("must-have / nice-to-have") describe the JD's framing, not a
> rounding of the weights. Per-node rationale (incl. why N4 = 0.9 and N9 = 0.4) is in §2.

### 1.1 Must-haves → highest-weight nodes (importance 0.9–1.0)
- **Production embeddings-based retrieval** (sentence-transformers / OpenAI / BGE / E5; embedding drift, index refresh, retrieval-quality regression).
- **Vector DB / hybrid search infra** (Pinecone / Weaviate / Qdrant / Milvus / OpenSearch / Elasticsearch / FAISS).
- **Ranking / recommendation / learning-to-rank** systems shipped to users.
- **Evaluation frameworks** for ranking (NDCG / MRR / MAP, offline↔online correlation, A/B).
- **Production deployment** (the JD's central gate: "without any production deployment — we will not move forward").
- **Strong Python / code quality.**

### 1.2 Nice-to-haves → bonus (lowest-weight nodes 0.3–0.4, additive cap +0.10)
LLM fine-tuning (LoRA/QLoRA/PEFT) · learning-to-rank models · HR-tech/recruiting/marketplace domain · distributed systems / large-scale inference optimization · OSS in AI/ML.

### 1.3 Anti-signals → `anti_penalty` (subtractive; total cap 0.50)

| Anti-signal | Detection (deterministic) | Penalty | Hard DQ? |
|---|---|---|---|
| Pure research, no production | titles/desc all research/academic; no `deployed/shipped/production/serving` | −0.25 | **Yes** |
| Consulting-only career | every company ∈ {TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini, …} and no product company | **−0.125** | **No** |
| LangChain-only / <12mo LLM hype, no pre-LLM ML | only recent LLM-wrapper terms, no earlier ML-production evidence | −0.20 | No |
| Framework-tutorial enthusiast | skills/desc dominated by tutorial/demo framework terms, no systems evidence | −0.15 | No |
| Title-chasing | ≥3 roles each `duration_months` < 18 with rising seniority titles | −0.10 | No |
| No recent hands-on (senior) | current title ∈ {architect, tech lead, manager} and no recent IC/production signal | −0.10 | No |
| CV/Speech/Robotics-primary, no NLP/IR | strong vision/speech/robotics, zero retrieval/NLP/IR nodes | −0.15 | No |

Hard DQ caps `base_capability` at **0.30** (sinks them far down without crashing the required 100-row output). **Only "Pure research, no production" remains a hard DQ.** Consulting-only was downgraded to a soft −0.125 penalty (trace evidence: in this dataset employer is decorrelated from work content — descriptions are a reused template bank sampled independently of company — so employer name alone must not zero a candidate; the consultant-with-only-generic-skills case is already handled by low `base_capability` + the unverified-skill 0.5 cap).

**Why "pure research, no production" carries *both* the cap and the −0.25 penalty (intentional, not redundant).** The two act on different parts of the formula and compound: the **0.30 cap** bounds how high a research-only profile's capability can *register* (it can never look "strong" on retrieval/ranking phrasing alone), while the **−0.25 penalty** then pushes it *further down within* that ceiling — `clamp01(min(base,0.30)·E − 0.25 + nice) ≈ 0.05` after experience. Without the penalty it would sit at ~0.30 (mid-pack); with it, ~0.05 (effectively floored). This reflects the JD's strongest non-honeypot disqualifier — *"without any production deployment … we will not move forward … we are explicit about this"* — so research-only must land near the bottom even when its phrasing scores well, short of the honeypot 0.0.

### 1.4 Experience band → `experience_factor` (JD: "range, not a requirement", ideal 6–8)
Per the locked E table. `years_of_experience` drives it; band 5–9 = 1.0, gentle taper outside.

### 1.5 Relevant-ML-tenure → `ml_depth_factor` (JD: ideal is "4–5 years *in applied ML*", not just total)
The JD distinguishes **total seniority** from **domain depth**: *"6-8 years total experience, of
which 4-5 are in applied ML/AI roles at product companies"* (ideal-candidate §) and warns against
*"recent (under 12 months) … LangChain to call OpenAI"* shallowness (disqualifier §). `experience_factor`
(§1.4) already captures total seniority; `ml_depth_factor` captures **how much of that career was
actually ML/AI work** — an axis `base_capability` does **not** measure (it scores the *presence* of ML
capability, not its *duration*). Two candidates with identical strong N1/N5 evidence — one with 5 years
of ML roles, one with a 6-month pivot — get the same `base_capability`; this factor separates them, which
is exactly the top-of-list precision NDCG@10 rewards.

**Computation (deterministic, dense data — reuses module2's ontology scan, no extra pass).**
A `career_history[]` role is **ML-relevant** if its `title` **or** `description` matches any
**strong-or-weak phrase of nodes N1–N7** (retrieval, embeddings, ranking, evaluation, ML-production,
NLP/IR, LLM — the genuine ML/AI nodes; N8 data-eng and N9 scale-infra alone do **not** qualify as
"applied ML"). Then `ml_months = Σ duration_months over ML-relevant roles` (this field is present for
100% of rows, values 6–228 — not a sparse signal), and `ml_years = ml_months / 12`.

| `ml_years` | `ml_depth_factor` | Rationale (JD-anchored) |
|---|---:|---|
| ≥ 4 | **1.10** | meets the ideal "4–5 years in applied ML" — boost genuine domain depth |
| 2 – <4 | **1.00** | solid but below ideal depth — neutral |
| 1 – <2 | **0.95** | real but shallow ML tenure — mild discount |
| < 1, but `base_capability > 0` | **0.85** | AI signal exists yet ≈no ML *career* months → recent pivot / skills-only claim (the JD's "under 12 months" concern) — demote |
| no ML-relevant role (`base_capability ≈ 0` from ML nodes) | **1.00** | neutral — `base_capability` is already ~0; don't double-punish |

**Bounded and safe by construction.** D ∈ [0.85, 1.10], applied as `base · E · D`. Because it
*multiplies* `base_capability`, it only meaningfully re-orders candidates who already have a real base
(a weak base × 1.10 is still weak), so it sharpens the top without promoting noise. The upper 1.10 cannot
break the score invariant — `clamp01` caps the product at 1.0. Setting all D = 1.0 reproduces v1 exactly,
so it is a clean, disableable calibration surface. **Interaction note:** the `< 1 yr → 0.85` case and the
`LangChain-only −0.20` anti-signal (§1.3) can co-fire on a recent-LLM-hype profile; this is intended
(shallow *and* hype is the worst case), and `clamp01` bounds the combined effect.

---

## 2. Capability ontology (the deterministic concept layer)

**Version:** AI Capability Ontology **v1**. The node set + importances + phrase families
below are frozen and live in `data/ai_capability_ontology.json`, which carries a top-level
`"version": "ai-capability-ontology-v1"` field. The exact freeze point is
**commit `b2f4c71`** (the ontology's first commit), so it is answerable via
`git show b2f4c71:data/ai_capability_ontology.json`. (Later JD-audit vocab additions —
OpenSearch, hybrid search, offline-to-online — are recorded in the ontology file's own
`description` field.)

Concept nodes, each with **strong** and **weak** phrase families — **plain-language forms included** so a Tier-5 who says *"built a recommendation system at a product company"* scores full credit without buzzwords. Matched over `profile.summary + headline + current_title + career_history[].title + career_history[].description + skills[].name + certifications`.

| Node | Imp. | Strong phrases (representative) | Weak phrases |
|---|---|---|---|
| N1 Retrieval & Search | 1.0 | recommendation system, recommender, search relevance, ranking system, matching engine, information retrieval, semantic search, RAG, nearest-neighbor, elasticsearch/solr/lucene | search, relevance, personalization, query |
| N2 Embeddings & Vector | 1.0 | embeddings, sentence-transformers, BGE, E5, vector database, faiss, pinecone, weaviate, qdrant, milvus, hnsw, dense retrieval, two-tower | vector, similarity, encoder |
| N3 Ranking & Recommendation / LTR | 1.0 | learning to rank, ltr, xgboost ranker, lambdamart, re-ranking, ranking model, recommendation engine | ranking, scoring, recommend |
| N4 Evaluation & Experimentation | 0.9 | ndcg, mrr, map, precision@k, offline evaluation, a/b test, online experiment, offline-online correlation | evaluation, metrics, benchmark, experiment |
| N5 ML Production & Deployment (MLOps) | 1.0 | deployed to production, model serving, ml pipeline, feature store, productionized, real users, inference service, monitoring/drift | deployed, production, pipeline, serving |
| N6 NLP / IR foundations | 0.7 | nlp, natural language processing, text classification, ner, tokeniz*, language model, information retrieval | text, language, embedding |
| N7 LLM & Fine-tuning | 0.3 | fine-tuning, lora, qlora, peft, instruction tuning, rlhf | llm, prompt, gpt |
| N8 Data & Feature pipelines | 0.5 | data pipeline, spark, airflow, dbt, feature engineering, etl, warehouse, kafka | data, pipeline, batch, stream |
| N9 Distributed / Scale / Inference-opt | 0.4 | distributed training, large-scale inference, latency optimization, quantization, throughput, sharding | scale, latency, optimize |

**Per-node weight rationale (weights are node-specific, set from the JD's emphasis):**
The four 1.0 nodes (N1/N2/N3/N5) are the JD's "absolutely need" build-core (retrieval,
embeddings/vector infra, ranking, production). Two weights are deliberately *between* the
round tiers and must survive "why exactly this number" scrutiny:
- **N4 Evaluation = 0.9 (not 1.0, not 0.8):** the JD lists rigorous ranking evaluation
  (NDCG/MRR/MAP, offline↔online correlation, A/B) as a hard requirement — *"If you've never
  thought about how to evaluate a ranking system rigorously, this role will be very painful"* —
  so it sits just **below** the 1.0 build-core because it is a must-have *supporting discipline*
  rather than a primary build deliverable, but **above** 0.7 because the JD treats it as
  non-negotiable, not merely desirable.
- **N9 Scale / Inference-opt = 0.4 (not 0.3):** the JD files "distributed systems / large-scale
  inference optimization" under *"Things we'd like you to have but won't reject you for,"* so it
  is weighted low like the other nice-to-haves — but **slightly above** the pure 0.3 nice-to-haves
  (e.g. N7 LLM fine-tuning) because the role's stated core mandate is candidate–JD matching
  *"at scale,"* making scale skills more on-point to the actual job than generic LLM tuning.

**node_strength rule (per node, per candidate):**
- **1.0 (strong):** evidence in `career_history[].description`/title (demonstrated work) **OR** a skill at proficiency ≥ advanced with `skill_assessment_scores[skill] ≥ 50`.
- **0.5 (weak):** evidence only in `skills[]`/`summary` without assessment, or assessment 30–49 (claimed but unproven).
- **0.0:** no evidence, or claimed skill with `assessment < 30` (treated as keyword stuffing → skill dropped).

This is the single most important precision lever: **career-history-described work always counts strong** (catches plain-language Tier-5s), while **unvalidated skill lists are discounted** (defangs keyword-stuffers).

> **Assessment-gating is a SECONDARY defense, not the primary one (measured dataset-wide).** Only **24.2%** of the 100K candidates have any `skill_assessment_scores` (avg 0.36 assessed skills vs ~9.6 listed; ~76% have none). So the `STRONG_ASSESS ≥50` / `STUFF_ASSESS <30` gates only have data for a minority. **The primary anti-stuffer mechanism is description-content scoring:** the high-value nodes (N1 Retrieval, N3 Ranking, N5 Production) can only reach strength 1.0 from `career_history[].description` evidence, which keyword-stuffers lack (their descriptions are non-ML). Assessment scores sharpen the few cases where they exist; they are not what carries the defense. *(Trace evidence: candidate C2, a stuffer with empty assessments, was still floored to 0 by N5 production = 0 + the 0.5 unverified-skill cap + anti-penalty.)*

---

## 3. Behavioral scoring formula

Per `redrob_signals_doc`: behavioral signals act as a **multiplier/modifier** on capability — never the driver, never zeroing a strong candidate (floor 0.50). `skill_assessment_scores` and `github_activity_score` are treated as **capability evidence (§2)**, not here.

### 3.1 `behavioral_raw` = Σ W[k]·sub_k  (weights sum to 1.0)

| k | Sub-score | Weight | Definition (→ [0,1]) |
|---|---|---:|---|
| recency | activity recency | 0.30 | from `last_active_date` vs AS_OF: ≤30d→1.0 · ≤60→0.9 · ≤90→0.75 · ≤180→0.5 · else→0.25 |
| responsiveness | reachability | 0.25 | `recruiter_response_rate` × time_factor(`avg_response_time_hours`: ≤24→1.0 · ≤72→0.9 · else→0.8) |
| open | in-market | 0.10 | `open_to_work_flag` ? 1.0 : 0.4 |
| interview | follow-through | 0.10 | `interview_completion_rate` (missing→0.5 neutral) |
| offer | closeability | 0.05 | `offer_acceptance_rate` if ≥0 else 0.5 (−1 = unknown→neutral) |
| logistics | fit to JD logistics | 0.10 | mean( notice_factor, location_factor, workmode_factor ) — see §3.2 |
| demand | recruiter demand | 0.07 | mean( lognorm(`saved_by_recruiters_30d`,cap 20), lognorm(`search_appearance_30d`,cap 500) ) |
| trust | verifiability | 0.03 | fraction of {`verified_email`,`verified_phone`,`linkedin_connected`} true |

### 3.2 Logistics sub-factors
- notice_factor (`notice_period_days`): ≤30→1.0 · ≤60→0.8 · ≤90→0.6 · else→0.4 (JD: sub-30 preferred).
- location_factor — **gradient derived from the JD's actual location language**, not a flat rule. The JD says: *"Location: Pune/Noida-preferred but flexible. We have offices in Noida and Pune"*; *"Candidates in Hyderabad, Pune, Mumbai, Delhi NCR welcome to apply"*; *"Open to relocation candidates from Tier-1 Indian cities"*; *"Outside India: case-by-case, but we don't sponsor work visas."* Mapped to:
  - `location` in **Pune / Noida** (the office cities; *"Located in or willing to relocate to Noida or Pune"*) → **1.0**
  - `location` in **Hyderabad / Mumbai / Delhi NCR** (explicitly *"welcome to apply"*) → **0.85**
  - else, `willing_to_relocate` **and** `country == India` (JD *"open to relocation … from Tier-1 Indian cities"*) → **0.85**
  - else **in India**, not relocating → **0.55**
  - **outside India** (JD *"case-by-case … we don't sponsor work visas"*) → **0.30**
  (City list + values live in `jd_rubric.json`/config; each value traces to a JD line above.)
- workmode_factor (`preferred_work_mode`): hybrid/flexible/onsite → 1.0 · remote → 0.7 (JD is hybrid Pune/Noida).

### 3.3 Missing / sentinel handling (frozen)
`-1` sentinels (`github_activity_score`, `offer_acceptance_rate`) and absent fields map to **neutral** (no penalty), never to 0. Rationale: absence ≠ negative.

### 3.4 Multiplier
`behavioral_multiplier = 0.50 + 0.50 · behavioral_raw ∈ [0.50, 1.00]`.
A fully unavailable candidate (stale, unresponsive) is **halved**, not eliminated — the JD says *down-weight* the unavailable, and we must still produce a full ranked 100. A "behavioral twin" with better signals beats its twin by up to ~2×.

### 3.5 Why a multiplier, not additive
Keeps capability primary (NDCG@10 precision) while letting behavior re-order otherwise-close candidates — satisfies the doc's "multiplier/modifier" framing and the behavioral-twin trap.

### 3.6 Optional embedding term (DISABLED in v1)
If enabled behind the Day-7 gate (see prior decision): add one node `N10 semantic_recall` (importance 0.5) whose `node_strength = clamp01((cosine(candidate, JD_requirements) − 0.35) / 0.45)`, computed from **precomputed** embeddings (offline; ~154 MB cache; ms at rank time). It only **raises** recall of plain-language fits; it never bypasses honeypot/anti-signal logic. v1 ships with this node absent.

---

## 4. Honeypot detection formula

Deterministic, **high-precision** impossibility checks (favor false-negatives over false-positives — burying a real candidate is worse than missing one honeypot, and the gate is only >10% in top-100). `honeypot(c) = (hard_rule_count(c) ≥ 1)`.

**Frozen hard rules (any one ⇒ honeypot):**
1. **Expert-but-unused cluster (H1):** count( proficiency ∈ {advanced, expert} **and** `duration_months == 0` ) ≥ 3. *(Matches the spec's own honeypot example "expert proficiency in skills with 0 years used".)*
2. **Tenure exceeds working life (H2):** `Σ career_history.duration_months > (years_of_experience·12)·1.5 + 12` (generous slack for parallel/overlapping roles; only flags the impossible — every real trigger had a single role longer than the candidate's entire stated experience).

**Why only these two (trace-validated, see `REDROB_TRACE_REPORT.md`).** The earlier draft had six rules; measured across the full 100K they fired wildly inconsistently with the spec's "~80 honeypots (0.08%)":

| Rule | Firing rate | Verdict |
|---|---|---|
| skill-duration > career | 13.45% | **removed** — `skills[].duration_months` is sampled independently of tenure; false-positive machine |
| reversed dates | 0.00% | **removed** — never fires (dates internally consistent) |
| duration mismatch | 0.00% | **removed** — never fires |
| education-before-work | 3.46% | **removed** — education years sampled independently of career; false-positive machine |
| **H1 expert-0-duration** | **0.021% (21)** | **kept** — precise, matches spec example |
| **H2 tenure>life** | **0.022% (22)** | **kept** — precise, disjoint from H1, every trigger genuinely impossible |

**Validated gate firing rate (H1 OR H2): 43 / 100,000 = 0.043%** — close to the spec's ~80 expected, and *under*-flagging (the safe direction; it cannot trip the >10%-in-top-100 DQ, and any honeypot that slips through still scores low on capability). **Caveat: this rate is measured on the public 100K pool; it is not proven on the hidden ground-truth set (see §7).**

**Not checkable from this schema (honest gap):** the JD's "8 years at a company founded 3 years ago" — there are **no company-founding dates** in `candidate_schema.json`, so that specific impossibility can't be verified. Residual honeypot risk.

**Keyword-stuffer ≠ honeypot:** a wrong-title-with-many-AI-skills profile is *not* forced to 0; it is naturally sunk by §2 (non-ML descriptions → N5 production = 0, plus the unverified-skill 0.5 cap) + §1.3 anti-signals. The honeypot floor is reserved for *provably impossible* profiles.

---

## 5. Final ranking formula

```
For each candidate c in candidates.jsonl (100,000):
    base   = base_capability(c)                       # §2, importance-weighted; description-primary, assessment-secondary
    if hard_dq(c): base = min(base, 0.30)             # §1.3 — hard_dq = "pure research, no production" ONLY
    capf   = clamp01( base * experience_factor(c) * ml_depth_factor(c) - anti_penalty(c) + nice_bonus(c) )   # §1 (incl. §1.5 ML-depth)
    M      = 0.50 + 0.50 * behavioral_raw(c)          # §3
    final  = 0.0 if honeypot(c) else capf * M         # §4

Keep the top 100 via a streaming bounded heap (see below); then
Sort the retained 100 by (round(final,6) DESC, candidate_id ASC) → ranks 1..100, score = round(final, 6)
```

**Implementation constraint (not a suggestion) — streaming Top-K heap.** module6_ranking
**MUST** select the top 100 with a **bounded min-heap** (`heapq`, size K=100) over the 100K
stream — **O(N log K)** time, **O(K)** memory — and **MUST NOT** collect all 100K scores
and full-sort (O(N log N), O(N) memory). Per candidate: compute `final`, push, and when the
heap exceeds 100, pop the smallest. **Heap element = `(final_score, -candidate_num, Candidate,
CapabilityProfile, CapabilityFit, BehavioralProfile, HoneypotAnalysis)`** where
`candidate_num = int(candidate_id[5:])`. The leading pair `(final_score, -candidate_num)` is
**already unique** (candidate_num is unique), so `heapq` never compares the trailing objects —
carrying them is safe and gives module7 full per-candidate context for the retained 100 with
**no second pass** (preserving the single streaming pass). Memory ≈ 1–2 MB for 100 full
payloads — within the O(K) budget. Eviction: the smallest element is the lowest score and, on a
score tie, the **highest** candidate id (smaller id kept → tie→candidate_id-ascending). After
the pass, sort the retained 100 by `(round(final,6) DESC, candidate_id ASC)` to assign ranks.

Properties (all satisfy `validate_submission.py`): exactly 100 rows; ranks 1–100 unique; **score non-increasing** (guaranteed by the final sort key); **ties broken by candidate_id ascending** (in both the heap eviction and the final sort); every id from the pool. Honeypots score 0 → cannot reach the top-100 while ≥100 positive candidates exist (they do), keeping honeypot-rate-in-top-100 = 0.

**Capability stays primary** (it's the multiplicand); behavior only rescales within [0.5, 1.0]; anti-signals/honeypots act before the multiplier. This maximizes top precision (NDCG@10 = 0.50 weight) while behavior + plain-language recall serve NDCG@50/MAP.

---

## 6. CSV output schema

Per `submission_spec` §2–3 (auto-validated):

| Column | Type | Rule |
|---|---|---|
| `candidate_id` | string | `CAND_XXXXXXX`; must exist in pool; unique |
| `rank` | int | 1–100, each exactly once |
| `score` | float | `round(final,6)`; non-increasing with rank |
| `reasoning` | string | 1–2 sentences; fact-grounded; varied; concern-aware |

- **File:** `<participant_id>.csv`, UTF-8, header row + **exactly 100** data rows.
- **Reasoning generation (deterministic template, fact-derived — no hallucination):**
  `"{current_title} with {years_of_experience} yrs; strengths: {top 2 matched nodes + 1 evidence snippet from career_history}; {1 behavioral note: recency/response}; concern: {top missing Critical node OR fired anti-signal OR notice_period}."`
  - Every claim is pulled from the candidate's own fields (passes Stage-4 "no hallucination").
  - Content varies because nodes/snippets/concerns differ per candidate (passes "variation").
  - Tone tracks rank: high ranks lead with strengths, low ranks lead with the concern (passes "rank consistency").

**Example (sample candidate CAND_0000001, Ira Vora — illustrative):**
```
CAND_0000001,<rank>,<score>,"Backend Engineer with 6.9 yrs; strong data/feature
pipelines (Kafka/Spark/Airflow) and emerging retrieval (NLP, embeddings via Milvus);
active recently, response rate 0.34; concern: ML production/eval evidence is
self-directed, not yet shipped to users."
```
(Honest: Ira is a data-eng→ML transitioner — partial fit, mid-pack — and the reasoning says so.)

---

## 7. Known Failure Modes / Limitations

Explicit, honest risks in this v1 design (none are silently assumed away):

- **Honeypot generalization (open risk).** H1/H2 were validated against the **public** 100K
  pool (~80 honeypots) achieving **0.043% pool-wide / 0 in top-100**. This is the *expected*
  outcome but is **not proven** to generalize to the hidden ground-truth set — the hidden set
  may contain honeypot patterns H1/H2 don't cover (e.g. company-founding-date impossibilities,
  which this schema can't express). Named risk, not a guarantee.
- **Capability false negatives.** Rule-based ontology matching can miss genuinely skilled
  candidates whose work is phrased outside the ontology's strong/weak lists; such candidates
  may score lower than warranted. Mitigated (not eliminated) by including plain-language phrase
  forms; the optional embedding node N10 would further reduce this but is off in v1.
- **Missing-signal assumption.** The `-1`/missing → **neutral** rule (§3.3) assumes missingness
  is non-informative (missing-at-random). If, in the hidden set, missingness correlates with
  quality (e.g. weaker candidates disproportionately lack GitHub/offer history), behavioral
  scoring would be **systematically biased** for affected candidates. Untested on the hidden set.
- **No hidden-set feedback.** With no leaderboard and a 3-submission cap, all calibration is
  against local evidence; the chosen constants are frozen on that basis and may be suboptimal
  for the hidden NDCG metric.

---

## 8. Winning Hypothesis (supported by local evidence — not proven)

**Hypothesis (not a claim of fact):** this design is *expected* to outperform naive
keyword/keyword-embedding matching on the hidden NDCG-scored set, for three reasons:
1. **Plain-language Tier-5 capture** — capability is scored from `career_history` *content*,
   not buzzword presence, so strong candidates who don't use the jargon still rank.
2. **Behavioral-twin separation** — near-identical-capability candidates are ordered by the
   ×0.5–1.0 behavioral modifier (availability/engagement), which keyword systems ignore.
3. **Honeypot avoidance** — H1/H2 floor provably-impossible profiles that pure embedding
   similarity would rank highly.
4. **Domain-depth separation** — `ml_depth_factor` (§1.5) orders equal-capability candidates by
   *years of actual ML work*, lifting the JD's ideal "4–5 years in applied ML" profile above the
   shallow recent-pivot — a depth axis keyword/embedding similarity does not measure.

**Supporting evidence (local only):** the 5-candidate `REDROB_TRACE_REPORT.md` produced
DevOps/strong-fit (0.585) and consulting+real-ML (0.619) above a plain-language Tier-5 (0.458),
above a keyword-stuffer (0.0) and a honeypot (0.0) — an ordering that matches strong-recruiter
intuition, with the plain-language candidate scored on its description content and the stuffer
sunk despite a buzzword-rich skill list.

**Explicitly unproven:** this has **not** been validated against the hidden ground truth; there
is no leaderboard signal. The hypothesis rests on a 5-candidate trace plus pool-wide
distribution checks — supporting, not conclusive. Outperformance is a *goal and expectation*,
not an established result.

---

## Frozen-design caveats
- All numeric constants are **frozen for v1** but are the calibration surface if a local gold set (see prior decision doc) shows miscalibration — change constants, not the architecture.
- **Validated honeypot firing rate: 0.043% (43 / 100,000)** with the kept rules H1 (expert-0-duration) + H2 (tenure>life), versus the spec's ~80 expected (~0.08%). The earlier six-rule draft fired on **16.94%** of the pool; removing the skill-duration and education-before-work rules (each a false-positive machine on this independently-sampled synthetic data) is what brought it in line. The gate intentionally *under*-flags — safe given the >10%-in-top-100 DQ. **This number is validated on the public pool only — not proven on the hidden ground-truth set (§7); always cite it with that caveat (README, methodology, DEFENSE_NOTES, etc.).**
- **Consulting-only is a soft −0.125 penalty, not a hard DQ** (§1.3). Trace evidence: employer is decorrelated from work content in this dataset; the only hard DQ retained is "pure research, no production".
- **Assessment-gating is secondary** (§2): only 24.2% of candidates carry `skill_assessment_scores`; description-content scoring is the primary anti-stuffer mechanism.
- **C1/C4 behavioral flip accepted as-is** (recency band cliff at 90 days): a slightly-stronger-on-capability but unavailable candidate can rank below an available one. This is intended per the JD's explicit "down-weight the unavailable", and the 0.50 multiplier floor bounds how far it can go. No change.
- Residual honeypot blind spot: company-founding-date impossibilities are unverifiable from the schema.
- Embedding node N10 is specified but **off** in v1; enabling it is the only sanctioned structural change, and it is purely additive to recall.
- **`ml_depth_factor` (§1.5) is a frozen-but-calibratable surface.** Its band edges (1/2/4 yrs) and values [0.85–1.10] are set from the JD's "4–5 years in applied ML" ideal, not from hidden-set tuning; like all constants they are the calibration surface if a local gold set shows miscalibration. Setting all bands to D = 1.0 disables it and reproduces v1 exactly. Like the honeypot rate, its benefit is reasoned/locally-supported, **not proven on the hidden ground-truth set** — cite with that caveat.
