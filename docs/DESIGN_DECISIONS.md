# Defense Notes

Why the system is built the way it is — per module, with the alternatives we
considered and why we rejected them. Written for the Stage-5 "defend your work"
interview. Every number cited lives in `shared/config/scoring.py` or the `data/`
files; nothing here is hand-waving.

---

## 0. The one idea everything hangs on

A real recruiting pool is full of **keyword stuffers** (an HR Manager who lists
"9 AI core skills") and **plain-language strong fits** (a "Recommendation Systems
Engineer" who never writes the buzzword "RAG"). A system that scores the *skills
list* ranks the stuffers first — which is exactly what the provided
`sample_submission.csv` does (HR Manager at rank 1).

Our answer: **score what a candidate demonstrably did in their career history, not
what they claim in a skill list.** A node reaches full strength only from career
descriptions/titles (or an assessment-verified skill); unvalidated skill lists are
capped at half credit. We verified this on the real data: of the 100 candidates the
sample submission ranks, **0** appear in our top-100; the 71 non-AI stuffers in it
average a final score of 0.12.

Everything below serves that idea.

---

## Ranking approach — the algorithmic story ("how did you achieve the ranking?")

**Short answer: a custom, from-scratch scoring engine with a streaming Top-K
selector — no ML, no embeddings, no external search engine.** Concretely:

- **Not TF-IDF / BM25.** Those rank by corpus term-frequency statistics. We score
  each candidate against a *curated capability ontology* with deterministic phrase
  matching; the weights come from the JD's emphasis, not corpus statistics.
- **Not cosine / embeddings.** No vectors at ranking time (the N10 embedding node is
  specified but off in v1) — it's CPU-only and network-off.
- **Not a graph algorithm.** No PageRank/traversal; candidates are scored
  independently.
- **It is a custom feature-scoring model + an efficient selection algorithm:**
  1. **Phrase/ontology matching (hand-rolled).** For each of 9 capability areas we
     precompile a `PhraseGroup` and scan the candidate text once with `str.find` +
     a manual word-boundary check — a tiny inverted-vocabulary scan. O(#phrases ×
     text) per candidate, compiled once at startup; it replaced a per-phrase regex
     approach for a measured **6.7× speedup** (Phase 1B).
  2. **Feature scoring (linear + multiplicative).** An importance-weighted linear
     sum over node strengths gives `base_capability`; experience/ML-depth factors
     and anti-signal penalties adjust it; a bounded behavioral multiplier rescales.
  3. **Streaming Top-K (the centerpiece).** A bounded min-heap of size 100 over the
     stream keeps the best 100 in **O(N log K)** time and **O(K)** memory — vs
     O(N log N)/O(N) for a full sort — with an id-ascending tie-break in eviction.

So the "technical story" is the good one: an **efficient ranking engine built from
scratch** — a curated matcher + a linear/multiplicative scoring function + a
streaming bounded-heap Top-K — chosen over BM25/cosine/graph because the 5-min /
16-GB / CPU-only / no-network constraints reward algorithmic efficiency and
explainability, and every ranking decision is defensible line by line.

---

## Per-module rationale

### `shared/config` — all constants in one file
**Choice:** every numeric constant (importances, bands, penalties, weights,
thresholds) in `scoring.py`; JD vocabulary in `data/jd_rubric.json`.
**Alternative:** constants inline in each module.
**Why not:** the constants *are* the model. Centralising them makes the whole scoring
policy auditable on one screen and tunable without touching logic — and it made the
sensitivity study a 5-line change.

### `shared/models` — Pydantic at every boundary
**Choice:** validate the candidate against the schema on read; validate every
inter-module object.
**Alternative:** parse raw dicts, trust the data.
**Why not:** 100K synthetic records will contain malformed/edge rows. Validating at
the boundary turns "silent wrong score" into "skipped + logged", and the typed models
are the contract between the two of us building in parallel.

### `shared/utils/phrase_matcher` — pure-Python `PhraseGroup`
**Choice:** ordered `str.find` with a manual word-boundary check, grouped per node.
**Alternatives benchmarked:** per-phrase `re.search`; a single union regex per node.
**Why not:** profiling (Phase 1B) showed ~87% of runtime in `re.Pattern.search`. The
union regex is faster but its match-ordering differs from "first phrase in tuple
order", so it would *change scores*. The pure-Python group preserves exact semantics
(405,440 comparisons, 0 mismatch) and is **6.7× faster** — module2 dropped from
~292s to ~44s per 100K. We kept the legacy regex functions for equivalence testing.

### `module1_jd_rubric` — build the rubric once
**Choice:** importances are **node-specific weights** (1.0/0.9/0.7/0.5/0.4/0.3), from
the JD's emphasis, built into one immutable `JDProfile` at startup.
**Alternative:** flat tiers (every "must-have" = 1.0); or re-deriving per candidate.
**Why not flat tiers:** the JD is not flat — it calls rigorous evaluation (NDCG/MRR)
"non-negotiable" but a *supporting* discipline, so N4 = 0.9, between the 1.0
build-core and the 0.7 of NLP foundations.
**Why once:** re-deriving per candidate would blow the runtime budget.

### `module2_capability` — the precision lever
**Choice:** node strength ∈ {0, 0.5, 1.0}. **1.0** needs a *strong* phrase in
demonstrated text (career history) or an assessment-verified skill (≥50); **0.5** for
a strong phrase only claimed, or a weak/ambiguous phrase in demonstrated text; **0.0**
otherwise. `base_capability` = importance-weighted mean.
**Alternatives:** (a) count skills; (b) any phrase anywhere = full credit; (c)
embeddings.
**Why not (a):** that is the sample-submission stuffer trap.
**Why not (b):** "production" in a *manufacturing* description, or "search" in a SQL
one, would fake AI capability — requiring a *strong* phrase in descriptions stops that
(a Mechanical Engineer lands at 0.17, not the top).
**Why not (c) here:** embeddings need a model + offline precompute; out of scope for
v1. Assessment-gating is *secondary* — only 24% of candidates have any assessment
scores, so description content carries the defense.

### `module3_capability_fit` — adjustments, multiplicative
**Choice:** `clamp01(base · experience_factor · ml_depth_factor − anti_penalty +
nice_bonus)`. Experience peaks at the JD's 5–9yr band; `ml_depth_factor` (0.85–1.10)
rewards *years actually in ML* vs total seniority; anti-signals subtract.
**Alternative:** additive capability + experience + behaviour in one weighted sum.
**Why not additive:** a candidate could buy back a missing must-have with seniority
and engagement. Multiplicative keeps capability primary — you cannot be a top fit
without the core.
**`ml_depth_factor`, why:** two people with identical strong retrieval evidence — one
with 5 ML years, one with a 6-month pivot — get the same `base_capability`; the JD
wants "4–5 years *in applied ML*", so this axis separates them. It only multiplies
(can't lift a weak base), and setting it to 1.0 reproduces the prior version — a clean
disableable surface.

### `module4_behavioral` — a bounded multiplier, not a score
**Choice:** 8 sub-scores → `behavioral_raw` → `multiplier = 0.5 + 0.5·raw ∈
[0.5, 1.0]`. Uses 14 of the 23 signals; `skill_assessment_scores` feeds capability
(module2) instead. The other **8 are deliberately unused**: profile_completeness,
signup_date, profile_views, applications, connections, endorsements, salary, and
`github_activity_score`.
**Alternative:** use all 23 signals; or make behaviour additive/decisive.
**Why omit 8:** connections/endorsements are gameable vanity; completeness/views/
applications are weak quality signals; salary is a negotiation/fit field, not quality;
and `github_activity_score` is `-1` for most of the pool (no GitHub), so it's sparse
and noisy. Feeding more signals into a multiplier only adds variance, not signal — so
the 14 predictive ones are used and the rest are left out.
**Why a bounded multiplier:** the signals doc says treat behaviour as "a multiplier or
modifier on top of skill-match." The 0.5 floor means a stale-but-strong candidate is
*halved, not deleted* — and a "behavioural twin" with better availability can beat its
twin by up to 2×. That matches the JD's "down-weight the unavailable".

### `module5_honeypot` — two rules, on purpose
**Choice:** H1 (≥3 advanced/expert skills with `duration_months == 0`) and H2
(Σ tenure > yoe·12·1.5 + 12). Honeypot ⇒ final 0.
**Alternative:** the earlier six-rule draft (reversed dates, education-before-work,
skill-duration mismatch, …).
**Why not six:** measured on the full 100K, the extra rules fired on **16.9%** of the
pool — a false-positive machine on independently-sampled synthetic data. H1+H2 fire on
**0.043%** (43/100K), matching the spec's stated ~80, and every trigger is genuinely
impossible. We *under*-flag on purpose: safe side of the >10%-in-top-100 DQ, and any
honeypot we miss still scores low on capability anyway. A keyword stuffer is **not** a
honeypot — it is sunk by module2, not floored here.

### `module6_ranking` — streaming bounded heap
**Choice:** a size-100 min-heap over the stream; `final = honeypot?0:fit·mult`; sort
the retained 100 by `(round(score,6) desc, candidate_id asc)`.
**Alternative:** score all 100K into a list and full-sort.
**Why not:** that is O(N) memory and O(N log N) time for 99.9% wasted work — we only
need the top 100. The heap is O(K) memory / O(N log K). The heap also carries each
candidate's full profile objects, so reasoning runs on the retained 100 with **no
second pass**. Tie-break by id-ascending is baked into both the heap eviction and the
final sort, so the CSV satisfies the validator by construction.

### `module7_reasoning` — deterministic template, not an LLM
**Choice:** a fact-grounded template — title, years, top demonstrated strengths (with
a real evidence phrase), one behavioural note, one honest concern; tone leads with
strengths for high ranks and with the concern for low ranks.
**Alternative:** generate reasoning with an LLM.
**Why not:** an LLM at rank time breaks the no-network/5-min constraint and risks
hallucination — the explicit Stage-4 failure mode. Every clause here is pulled from
the candidate's own fields (verified: 100/100 rows, 0 hallucinations), it varies per
candidate (100/100 distinct), and the tone tracks the rank.

### `module8_submission` — validate, then write
**Choice:** a hard gate that re-checks all official-validator rules + pool membership
+ "scores not all identical" + non-empty reasoning, and aborts the run on any failure
before writing.
**Alternative:** trust module6's construction and just write.
**Why not:** "valid by construction" is an assumption; the gate is a *test*. It costs
microseconds and removes the single worst outcome — a silently malformed CSV that
auto-rejects at Stage 1 and burns one of only three submissions.

---

## Calibration robustness (addressing the obvious objection)

The constants are reasoned from the JD, not tuned on a gold set (none exists). So:
**how much does the ranking depend on the exact numbers?** We perturbed importances by
±15% and the experience/ML-depth factors by ±0.05, 8 trials over an 8,000 sample:

| | mean overlap with baseline |
|---|---|
| top-10 | **97.5%** |
| top-50 | **97.5%** |
| top-100 | **95.4%** |
| rank correlation (shared top-100) | **~0.96–0.99** |

The top-10 — which drives 50% of the composite via NDCG@10 — is essentially stable
under realistic mis-calibration. The exact weights are not load-bearing; the
*structure* (description-primary, capability-primary, honeypot floor) is.

---

## Known limitations (honest)

1. **Calibration is reasoned, not ground-truth-tuned.** Mitigated, not eliminated, by
   the robustness above. If a local gold set ever exists, the constants in `scoring.py`
   are the single tuning surface.
2. **No semantic recall.** Embeddings are off (the design's gated N10 node). A strong
   candidate phrasing their work entirely outside our vocabulary can be under-scored.
   Softened by weak/plain-language phrases, but it's the main recall gap and most
   affects NDCG@50 / MAP. The intended fix is the N10 node: offline-precomputed
   embeddings (precompute is allowed by spec §107) loaded as a millisecond lookup at
   rank time, added only as a recall booster that never bypasses honeypot/anti-signal
   logic.
3. **Behavioural cliffs.** The recency band has a hard edge at 90 days; a candidate one
   day over can drop a tier. Bounded by the 0.5 multiplier floor; intended per the JD's
   down-weighting language.
4. **Honeypot generalisation.** 0.043% is validated on the public pool, not the hidden
   ground truth, which may contain patterns H1/H2 don't cover. We under-flag
   deliberately so we cannot trip the DQ.

---

## Questions we expect in the interview

- *Why does an HR Manager with 9 AI skills score 0?* → module2: no AI in the career
  descriptions; skill list capped at 0.5 and gated by assessments.
- *Why is consulting only a −0.125 soft penalty, not a DQ?* → in this dataset the
  employer is decorrelated from the work content (descriptions are templated), so the
  company name alone must not zero a candidate; real consultants with only generic
  skills are already sunk by low base capability.
- *Why 0.9 for evaluation and not 1.0?* → the JD treats rigorous ranking evaluation as
  non-negotiable but supporting, not a primary build deliverable.
- *What if your weights are wrong?* → the sensitivity table: top-10 is 97.5% stable
  under ±15%.
- *The JD lists a "closed-source 5+ years without external validation" disqualifier
  (line 049) — why don't you enforce it?* → it keys on the absence of a public signal
  (papers/talks/GitHub), and 64.6% of the pool has no GitHub at all, so the rule fires
  on a majority and is a false-positive machine on this synthetic data. We deliberately
  omit it; genuinely weak closed-source profiles are already sunk by low demonstrated
  capability. (Python-as-a-skill and HR-tech/OSS domain are omitted for the same
  "low discrimination / not a capability axis" reason.)
