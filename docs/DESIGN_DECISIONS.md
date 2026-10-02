# Design Decisions

Why the system is built the way it is: the choice made in each module, the alternatives considered, and why they were rejected. Every number below comes from `shared/config/scoring.py`, the `data/` files, or a measurement on the provided 100K pool.

---

## 0. The central idea

A recruiting pool contains **keyword stuffers**, such as an HR Manager listing a dozen AI skills, and **plain-language strong fits**, such as a Recommendation Systems Engineer who never writes "RAG". A system that scores the skills list ranks the stuffers first. The provided `sample_submission.csv` shows this: its rank 1 is a Project Manager, and 98 of its 100 candidates have non-AI current titles.

WorkLens instead **scores what a candidate demonstrably did in their career history.** A capability area reaches full strength only from career titles and descriptions, or from an assessment-verified skill backed by the career history; self-reported evidence is capped at half credit. On the provided pool, none of the sample submission's 100 candidates appear in WorkLens's top 100, and the 98 with non-AI titles average a final score of 0.10 (the top-100 cutoff is about 0.58).

---

## Ranking approach

WorkLens is a hand-built scoring function plus a streaming top-K selector. It uses no ML model, no embeddings and no external search engine.

- **Not TF-IDF or BM25.** Those rank by corpus term statistics. WorkLens scores each candidate against a curated capability ontology, with weights taken from the job description's emphasis.
- **Not embeddings or cosine similarity.** No vectors are computed at ranking time; the run is CPU-only and offline.
- **What it is:**
  1. **Phrase matching against an ontology.** For each of the 9 capability areas a `PhraseGroup` is built once at startup. Each candidate's text is lower-cased once and scanned with `str.find`, plus word-boundary checks.
  2. **A linear and multiplicative scoring function.** An importance-weighted sum of node strengths gives `base_capability`. Experience and ML-depth factors and anti-signal penalties adjust it, and a bounded behavioral multiplier rescales it.
  3. **Streaming top-K.** A min-heap of size 100 keeps the best candidates in O(N log K) time, instead of the O(N log N) time and O(N) memory of a full sort. It breaks ties by ascending candidate id.

These choices fit the constraints (5 minutes, 16 GB, CPU only, no network) and keep every ranking decision traceable to a rule.

---

## Per-module rationale

### `shared/config`: all numbers in one file
**Choice:** every numeric constant in `scoring.py`; role vocabulary in `data/jd_rubric.json`.
**Alternative:** constants inline in each module.
**Why not:** the constants are the model. Keeping them together makes the scoring policy reviewable in one place and tunable without touching logic. It also makes `tools/sensitivity.py` straightforward.

### `shared/models`: Pydantic between stages
**Choice:** validate each candidate on read, and pass typed models between stages, including the rubric vocabulary inside `JDProfile`.
**Alternative:** pass raw dicts.
**Why not:** a 100K synthetic pool can contain malformed rows. Validating at the boundary turns a silently wrong score into a skipped, logged record. The typed models also served as the contract between the two people building the stages in parallel.

### `shared/utils/phrase_matcher`: `str.find` instead of regex
**Choice:** ordered `str.find` with explicit word-boundary checks, grouped per node.
**Alternatives:** one `re.search` per phrase; one union regex per node.
**Why not:** profiling during development showed most of the runtime in regex search. A union regex reports the leftmost match in the text, not the first phrase in list order, so it would change which evidence phrase is reported. `str.find` keeps the semantics exactly. `tests/test_phrase_matcher.py` checks it against a regex reference implementation.

**Caching per text part.** The pool's 300,171 career entries contain only 340 distinct role texts. module2 therefore matches each distinct part once through an LRU-cached `PhraseIndex` and scores by set lookups. This is exact because no phrase spans a newline. module2 went from about 40 s to about 5 s, and the full run is about 2.8× faster. `tools/bench_matcher.py` confirms identical profiles against a regex reference with the same rules (612.7 s → 5.7 s on 100K). Details are in PERFORMANCE.md.

**Matching rule:** a phrase must start at a word boundary, so "search" does not match inside "research" and "serving" does not match inside "observing". Short phrases (four characters or fewer) must also end at one.

### `module1_jd_rubric`: build the rubric once
**Choice:** node-specific importances (1.0, 0.9, 0.7, 0.5, 0.4, 0.3), built into one `JDProfile` at startup. The builder validates the rubric against the ontology and the constants.
**Alternative:** flat tiers (every must-have = 1.0), or recomputing per candidate.
**Why not flat tiers:** the job description is not flat. It calls rigorous evaluation (NDCG/MRR) non-negotiable but supporting, so N4 = 0.9, between the 1.0 build core and NLP foundations at 0.7.

### `module2_capability`: graded evidence
**Choice:** node strength in {0, 0.5, 1.0}.
- **1.0** needs a strong phrase in career history, or an advanced/expert skill with an assessment ≥ 50 that the career history at least loosely supports.
- **0.5** is for a strong phrase only in self-reported text, an assessed skill with no career support, or only a weak phrase in career history.
- **0.0** otherwise.

Each result records its source (`career`, `skill_verified`, `claimed`, `career_weak`, `none`) so the reasoning can describe it accurately.

**Context.** A phrase inside a comparison or a statement of non-experience is not evidence: "lighter weight than ranking systems at FAANG", "interested in transitioning toward NLP". A match is ignored when a cue word (than, toward, not, no, never, without) appears among the three words before it in the same clause. This is a heuristic, not a parser; on the provided pool it suppresses four patterns, all correctly (SCORING_DESIGN.md, section 1.2).

**Why assessed skills need career support.** The job asks for work "deployed to real users". An assessment shows knowledge, not delivery, so on its own it counts as a claim.
**Alternatives:** (a) count skills; (b) any phrase anywhere earns full credit; (c) embeddings.
**Why not (a):** that is the sample submission's failure mode.
**Why not (b):** "production" in a manufacturing description, or "search" in a SQL role, would fake AI capability. Across 5,791 Mechanical Engineers the mean final score is 0.09.
**Why not (c):** embeddings need a model and offline pre-computation; they are out of scope for v1. Assessment gating is secondary because only 24% of candidates have any assessment scores.

### `module3_capability_fit`: multiplicative adjustments
**Choice:** `clamp01((base × experience_factor × ml_depth_factor − anti_penalty + nice_bonus) / 1.2)`, where 1.2 is the largest value the numerator can reach. Dividing instead of clamping keeps the strongest profiles distinct; with a plain clamp, 8 of the top 10 tied at 1.0 and behaviour alone ordered them.
**Alternative:** one additive sum of capability, experience and behaviour.
**Why not additive:** a candidate could make up for a missing core capability with seniority and engagement. Multiplying keeps capability primary.

**`ml_depth_factor`:** two candidates with identical retrieval evidence, one with five ML years and one with a six-month pivot, have the same `base_capability`. The job asks for 4-5 years of applied ML, so this factor separates them. It only multiplies, so it cannot lift a weak base. ML tenure is capped at stated experience so that overlapping roles cannot inflate it.

**Anti-signals:** seven rules from the job description's "do not want" list. Only `research_only` is a hard disqualifier. `consulting_only` is a soft penalty (−0.125), because in this data the employer name is not correlated with the work described. `title_chasing` counts only completed roles: a candidate who recently started a new job is not job-hopping. `langchain_only` does not fire when the career shows retrieval or ranking work, which is the job description's own exemption; without that check all 12 of its firings hit candidates with production retrieval experience. On the provided pool, five of the seven rules never fire (SCORING_DESIGN.md, section 3). They are kept because they encode real requirements and are covered by tests.

### `module4_behavioral`: a bounded multiplier
**Choice:** eight sub-scores → `behavioral_raw` → `multiplier = 0.5 + 0.5 × raw`, in [0.5, 1.0]. It uses 14 of the 23 signals; `skill_assessment_scores` feeds capability instead.
**Not used:** `profile_completeness_score`, `signup_date`, `profile_views_received_30d`, `applications_submitted_30d`, `connection_count`, `endorsements_received`, `expected_salary_range_inr_lpa`, `github_activity_score`.
**Why:**
- Connections and endorsements are easy to inflate.
- Completeness, views and applications say little about quality.
- Salary is a negotiation field, not a quality signal.
- `github_activity_score` is −1 (no GitHub) for 64.6% of the pool.

**Why a bounded multiplier:** the signals documentation describes behaviour as a modifier on top of skill match, so capability stays the primary axis.

**Two explicit availability rules.** The job description says a candidate inactive for six months with a 5% response rate "is, for hiring purposes, not actually available", and that the company does not sponsor work visas. A weighted sum understated both: an unresponsive candidate kept about 0.73 of their score, and being abroad cost 1-2%. So a candidate inactive for more than 180 days or with a response rate below 0.10 gets the floor multiplier (0.5), and a candidate outside the home country has the multiplier scaled by 0.8. Both thresholds and the factor are in `scoring.py`; the home country is in the rubric.

### `module5_honeypot`: two rules
**Choice:** H1 (≥ 3 advanced/expert skills with `duration_months == 0`) and H2 (total tenure > `yoe × 12 × 1.5 + 12`). A honeypot scores 0.
**Alternative:** an earlier draft with six rules (reversed dates, education after work, skill-duration mismatch and others; not in the repository).
**Why not:** on the 100K pool the extra rules flagged about 17% of candidates, mostly false positives on independently sampled synthetic data. H1 and H2 flag 43 (0.043%), close to the roughly 80 the specification mentions, and each is genuinely impossible. Under-flagging is the safe side of the "more than 10% honeypots in the top 100" disqualification. A missed honeypot usually scores low on capability anyway.

### `module6_ranking`: streaming bounded heap
**Choice:** a size-K min-heap over the stream (K = 100 by default, `--top-k`); `final = 0 if honeypot else round(fit × multiplier, 6)`; the retained entries are sorted by score descending, then id ascending.
**Alternative:** score all 100K into a list and sort.
**Why not:** that keeps every record in memory and sorts 100K entries to use 100. The heap also carries each retained candidate's scoring objects, so reasoning needs no second pass. Scores are rounded before they enter the heap, so eviction and final ordering compare exactly the value written to the CSV. The tie-break compares candidate ids as strings (reversed inside the heap), so it works for any id format.

### `module7_reasoning`: a template, not an LLM
**Choice:** a deterministic template with title, years, strongest capability areas (with an evidence phrase), recent activity and the most significant gap.
**Alternative:** generate the text with an LLM.
**Why not:** an LLM call at ranking time breaks the no-network and time constraints, and risks invented claims. Each clause here comes from the candidate's fields or a matched phrase. Partial evidence is worded by its source ("only self-reported" or "only indirect … in career history"), and behavioural gaps are named when they are the reason. When there is no gap the line says so, rather than filling a "Concern" slot. `tests/test_reasoning.py` covers these cases.

### `module8_submission`: validate, then write
**Choice:** check every official validator rule, plus pool membership, non-identical scores and non-empty reasoning, before writing; abort with exit code 1 on failure. The writer also guards against spreadsheet formula injection.
**Alternative:** trust module 6's construction.
**Why not:** "valid by construction" is an assumption, and the check costs microseconds. It prevents a malformed CSV from being submitted.

---

## Calibration robustness

The constants are reasoned from the job description, not fitted to labelled data (none exists). To measure how much the ranking depends on their exact values, `tools/sensitivity.py` re-ranks the first 8,000 candidates under 8 random perturbations (seed 0). Node importances are scaled by ±15%, and the experience and ML-depth factors are shifted by ±0.05:

| | mean overlap with the unperturbed ranking | worst trial |
|---|---|---|
| top 10 | 96.3% | 90% |
| top 50 | 95.2% | 92% |
| top 100 | 96.5% | 94% |
| Spearman correlation on the shared top 100 | 0.93-0.99 | |

The top 10, which carries the most weight in NDCG@10, is stable under realistic mis-calibration. The structure (career-first evidence, capability-first scoring, honeypot floor) matters more than the exact weights.

---

## Known limitations

1. **Calibration is reasoned, not fitted.** The sensitivity check bounds the risk but does not remove it. If labelled data becomes available, `scoring.py` is the single place to tune.
2. **No semantic recall.** Embeddings are not used. A strong candidate who describes their work entirely outside the ontology's vocabulary can be under-scored. The planned fix is an offline-precomputed embedding lookup (pre-computation is allowed by the specification), used only to add recall, never to bypass honeypot or anti-signal logic.
3. **Behavioural cliffs.** Recency bands have hard edges; one day past 90 days drops a band. The 0.5 multiplier floor limits the effect.
4. **Honeypot coverage.** H1 and H2 were checked on the public pool only; the hidden evaluation may contain other patterns. The rules under-flag deliberately.
5. **Must-haves are weighted, not required.** RANKING_REVIEW.md checks every top-100 candidate against the job description. After the post-review fixes the top 10 are all strong matches, but a few candidates with broad production ML and no retrieval or embedding work remain in the lower part of the top 100.
6. **Inactive anti-signals.** Five rules do not fire on the provided pool. Their vocabulary was not tuned to this data, to avoid fitting rules to one synthetic sample.

---

## Questions to expect

- *Why doesn't an HR Manager with nine AI skills rank?* Their career text has no AI content, so those skills count only as self-reported (0.5). They score about 0.22, against a top-100 cutoff of about 0.58.
- *Why is consulting only a −0.125 soft penalty?* In this dataset the employer is not correlated with the work described, so the company name alone must not sink a candidate. Consultants with only generic experience already score low.
- *Why 0.9 for evaluation rather than 1.0?* The job treats rigorous evaluation as non-negotiable but supporting, not a primary deliverable.
- *What if the weights are wrong?* See the sensitivity table: the top 10 is about 96% stable under ±15% perturbation.
- *Why isn't the "closed-source for 5+ years without external validation" disqualifier enforced?* It depends on the absence of public signals such as GitHub, and 64.6% of the pool has no GitHub, so it would flag the majority. Weak closed-source profiles already score low on demonstrated capability.
