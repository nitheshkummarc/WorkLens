# WorkLens-RedRob — Phase 0 Architecture Package

Domain logic source of truth: **`REDROB_SCORING_DESIGN.md` v1 (trace-corrected)** —
H1/H2-only honeypot, −0.125 soft consulting penalty, description-primary /
assessment-secondary scoring. Constants are **not** re-derived here; they are
referenced as ground truth. Schemas: see `interface_contract.md`.

**Engineering standard:** one responsibility per file; typed functions; no
duplication; all tunables in config; per-module README + tests. **No hard
line ceiling** — files may exceed 300 lines if doing one job well, but length is
never a reason to merge responsibilities (judge-readable in <1 min = the test).

> **STATUS: PHASE 0 — DOCS ONLY.** No implementation code, module files, or
> placeholder classes exist yet. The folder tree below is the *plan*; only
> `docs/` exists at this point.

---

## 1. Proposed folder structure for `worklens_redrob/`

```
worklens_redrob/
├── README.md                         # run instructions + reproduce_command (Phase 1)
├── rank.py                           # ENTRYPOINT/orchestrator: candidates.jsonl + JD -> submission.csv
├── requirements.txt
├── data/
│   ├── ai_capability_ontology.json   # §2: 9 AI nodes (importance + strong/weak phrases) — NEW
│   └── jd_rubric.json                # §1: nice-to-haves, anti-signals, experience bands, logistics targets — NEW
├── shared/
│   ├── config/                       # ALL tunables from REDROB_SCORING_DESIGN.md (no hardcoding in logic)
│   │   ├── paths.py                  # project-root path resolution (pattern reused from WorkLens)
│   │   ├── scoring.py                # §3 behavioral weights/tables, §1 penalties/bands/bonus, §4 thresholds, fit floor
│   │   ├── run_config.py             # RunConfig + AS_OF
│   │   └── __init__.py               # re-export
│   ├── models/                       # all Pydantic schemas (interface_contract.md)
│   │   ├── candidate.py              # Candidate + nested (input model)
│   │   ├── ontology.py               # OntologyNode
│   │   ├── jd_profile.py             # JDProfile + rubric models
│   │   ├── capability.py            # CapabilityProfile, NodeEvidence
│   │   ├── capability_fit.py         # CapabilityFit
│   │   ├── behavioral.py             # BehavioralProfile
│   │   ├── honeypot.py               # HoneypotAnalysis
│   │   ├── ranking.py                # CandidateScore, RankedCandidate
│   │   ├── submission.py             # SubmissionRow
│   │   └── __init__.py
│   ├── utils/
│   │   ├── jsonl_reader.py           # stream-read + validate candidates.jsonl (NEW)
│   │   ├── ontology_loader.py        # load ai_capability_ontology.json (adapted from WorkLens signal_loader)
│   │   ├── phrase_matcher.py         # generic strong/weak phrase detection (copied from WorkLens, generic)
│   │   ├── date_utils.py             # months-between, recency vs AS_OF (NEW)
│   │   ├── text_fields.py            # assemble candidate text blobs (career desc / skills / summary) (NEW)
│   │   └── __init__.py
│   └── __init__.py
├── modules/
│   ├── module1_jd_rubric/            # §1 — build JDProfile from ontology + jd_rubric.json
│   ├── module2_capability/           # §2 — node strengths + base_capability
│   ├── module3_capability_fit/       # §1 adjustments + §0 capability_fit
│   ├── module4_behavioral/           # §3 — behavioral_multiplier
│   ├── module5_honeypot/             # §4 — H1/H2
│   ├── module6_ranking/              # §0 final + §5 — final_score, rank, top-100
│   ├── module7_reasoning/            # §6 — reasoning string
│   └── module8_submission/           # §6 — CSV writer + SubmissionValidator (HARD GATE)
├── tests/                            # unit + integration + trace-replay (pytest layout reused)
├── docs/
│   ├── interface_contract.md
│   └── PHASE0_ARCHITECTURE.md        # this file
└── outputs/                          # generated submission.csv (git-ignored)
```
Each `moduleN_*/` will follow the WorkLens internal shape (single-responsibility
files: e.g. `extractor.py`/`scorer.py`/`validator.py` as the job requires, plus
`config.py` surfacing shared tunables, `README.md`, `tests/`). No module files are
created in Phase 0.

---

## 2. Interface contract
See **`interface_contract.md`** (every schema + boundary). Not duplicated here.

---

## 3. Module plan (responsibility · inputs · outputs · metric ownership)

| Module | Single responsibility | Inputs | Outputs | Owns (metrics) |
|---|---|---|---|---|
| **shared/utils/jsonl_reader** | stream + validate records; skip malformed lines (warn + `skipped_records`); accumulate pool-id `set[str]` (see interface_contract §1a) | `candidates.jsonl` | `Iterable[Candidate]` + pool-id set | — (infra) |
| **module1_jd_rubric** | build the JD rubric (§1) | `ai_capability_ontology.json`, `jd_rubric.json` | `JDProfile` | required_capabilities + importances, nice-to-have set, anti-signal config, experience bands, logistics targets |
| **module2_capability** | extract demonstrated capability (§2) | `Candidate`, ontology, `JDProfile` | `CapabilityProfile` | `node_strengths`, `base_capability`, `ml_relevant_months` |
| **module3_capability_fit** | apply rubric adjustments (§1) + assemble fit (§0) | `Candidate`, `CapabilityProfile`, `JDProfile` | `CapabilityFit` | `anti_penalty`, `hard_dq`, `experience_factor`, `ml_depth_factor`, `nice_bonus`, `capability_fit` |
| **module4_behavioral** | behavioral multiplier (§3) | `Candidate.redrob_signals`, AS_OF | `BehavioralProfile` | 8 sub-scores, `behavioral_raw`, `behavioral_multiplier` |
| **module5_honeypot** | impossibility detection (§4) | `Candidate` | `HoneypotAnalysis` | `is_honeypot`, `rule_fired` |
| **module6_ranking** | final score + rank (§0 final, §5) — **streaming Top-K** | per-candidate `CapabilityFit` + `BehavioralProfile` + `HoneypotAnalysis` (streamed) | `RankedCandidate[100]` | `final_score`, `rank`, top-100 selection, sort/tie-break |
| **module7_reasoning** | per-candidate justification (§6) | `Candidate` + its 4 profile objects | `reasoning: str` | `reasoning` |
| **module8_submission** | CSV serialization + **final-output validation** (§6) | `RankedCandidate[100]` + reasoning + pool ids | `submission.csv` (+ pass/fail) | CSV schema conformance, **validation gate** |
| **rank.py** | orchestration only (wire modules, I/O) | CLI args | runs pipeline | — (no domain metric) |

No module owns a metric owned by another. `base_capability` (M2) and
`capability_fit` (M3) are distinct and separately owned. `final_score` is M6 only.

### 3a. module6_ranking — streaming Top-K (hard constraint, not a suggestion)
module6_ranking **MUST** select the top 100 with a **bounded min-heap** (`heapq`, size K=100)
over the 100K stream — **O(N log K)** time, **O(K)** memory — and **MUST NOT** materialize all
100K scores and full-sort (O(N log N), O(N) memory). Per candidate: compute `final`, push, and
when the heap exceeds 100, pop the smallest.

**Heap element (explicit payload):**
`(final_score, -candidate_num, Candidate, CapabilityProfile, CapabilityFit, BehavioralProfile, HoneypotAnalysis)`
where `candidate_num = int(candidate_id[5:])`.
- **Comparison safety:** the leading pair `(final_score, -candidate_num)` is already unique
  (candidate_num is unique), so `heapq` never needs to compare the trailing objects — including
  them in the tuple is safe and won't raise on non-orderable Pydantic models.
- **Why carry the objects:** the retained 100 elements already hold every per-candidate object
  module7_reasoning needs, so reasoning runs with **no second pass** and without violating the
  single-streaming-pass constraint.
- **Memory:** ≈ 1–2 MB for 100 full payloads — well within the O(K) budget.
- **Tie-breaker rationale:** *Because it's a min-heap, negating the candidate id ensures that on
  a score tie the highest id is treated as "smallest" and is evicted, preserving the lower id —
  matching the candidate_id-ascending tie rule.*

After the pass, sort only the retained 100 by `(round(final,6) DESC, candidate_id ASC)` to
assign ranks. (Mirrors `REDROB_SCORING_DESIGN.md` §5.)

### 3b. Runtime budget (target ≤5 min; single CPU core; estimates, confirmed in Phase 1b)
Budgeted for the streaming-heap path — **no full sort**.

| Stage | Work | Est. time |
|---|---|---|
| M1 JD rubric extraction | one-time at startup (build `JDProfile` from ontology + rubric) | one-time, negligible, <1 s |
| JSONL read + parse + validate | 100K lines (~465 MB) streamed via `jsonl_reader` | ~45 s |
| Per-candidate scoring M2–M6 (×100K) + heap push | precompiled phrase match (M2), capability_fit (M3), behavioral (M4), honeypot (M5), final + heap (M6) | ~150 s |
| Reasoning M7 (×100 only) | template render for the final 100 | <1 s |
| CSV write + validation M8 | 100 rows + `SubmissionValidator` | <1 s |
| **Total** | | **~196 s (~3.3 min)** — ≥1.6 min margin under the 5-min cap |

If Phase-1b measurement exceeds budget, optimize per-candidate scoring (precompile regex,
token-set matching, skip empty fields) — **do not** revert to a full sort.

### 3c. One-time initialization (required for the §3b budget to hold)
The per-candidate budget assumes **all setup happens once at startup, outside the 100K loop**:
- `data/ai_capability_ontology.json` and `data/jd_rubric.json` are **loaded once** at startup
  (via `ontology_loader` / module1) and passed as **immutable references** into the
  per-candidate scoring path — **never re-read or re-parsed per candidate**.
- `shared/utils/phrase_matcher` **compiles its regex / matching structures once at
  initialization** (e.g. precompiled patterns or token sets per node) and reuses them across
  all 100K candidates — **no compilation inside the per-candidate loop**.
- `module1_jd_rubric` runs **once** producing a single `JDProfile`, reused for every candidate.
A regression here (re-loading/re-compiling per candidate) would blow the ~150 s scoring budget;
treat one-time init as a hard performance contract, asserted in the Phase-1b timing test.

---

## 4. Data-flow diagram (candidates.jsonl + job_description → submission.csv)

```
                         data/ai_capability_ontology.json   data/jd_rubric.json
                                         │                          │
                                         └──────────┬───────────────┘
job_description (context) ──────────────────────────▼
                                            module1_jd_rubric → JDProfile ──────────────┐
                                                                                        │ (importances, anti/nice/exp/logistics)
candidates.jsonl (100,000)                                                              │
   │  shared/utils/jsonl_reader (stream + validate)                                     │
   ▼                                                                                    │
 Candidate ──┬─────────────► module2_capability ──► CapabilityProfile ──┐               │
             │                    (uses ontology + JDProfile)            │               │
             ├─────────────► module3_capability_fit ◄────────────────────┴───────────────┘
             │                    → CapabilityFit (capability_fit)        │
             ├─────────────► module4_behavioral  → BehavioralProfile (multiplier)
             ├─────────────► module5_honeypot    → HoneypotAnalysis (is_honeypot)
             │                                                            │
             │     (per-candidate: capability_fit, multiplier, honeypot) │
             ▼                                                            ▼
      module6_ranking:  final = honeypot ? 0 : capability_fit·multiplier
                        sort (round(final,6) DESC, candidate_id ASC) → take top 100 → ranks 1..100
             │
             ▼
   for each of top 100:  module7_reasoning (Candidate + 4 profiles) → reasoning string
             │
             ▼
   module8_submission:  build SubmissionRow[100] → SubmissionValidator (HARD GATE)
                        → write submission.csv   (abort on any validation failure)
             │
             ▼
        submission.csv      [orchestrated end-to-end by rank.py]
```
Streaming note: the pipeline scores candidates in a single streaming pass (M2–M5
per candidate), keeping only a running top-K by `final_score` to satisfy the 5-min
/ 16-GB budget on 100K records; reasoning (M7) runs only for the final 100.

---

## 5. Design-section → module ownership (every § owned by exactly one module)

| `REDROB_SCORING_DESIGN.md` section | Owning module | Note |
|---|---|---|
| §0 frozen block — `capability_fit` equation | module3_capability_fit | the clamp01(base·E·D − anti + nice) assembly (D = `ml_depth_factor`) |
| §0 frozen block — `final = honeypot?0:cap_fit·M` | module6_ranking | final combination |
| §0 frozen block — RANK sort / top-100 / tie-break | module6_ranking | |
| §0 locked constants | shared/config | values only; logic elsewhere |
| §1.1 must-haves (Critical nodes + importances) | module1_jd_rubric (+ ontology data) | importances live in ontology, selected by rubric |
| §1.2 nice-to-haves (`nice_bonus`) | module3_capability_fit | rule applied; list from JDProfile |
| §1.3 anti-signals (`anti_penalty`, hard_dq, consulting −0.125) | module3_capability_fit | definitions from JDProfile |
| §1.4 experience band (`experience_factor`) | module3_capability_fit | bands from JDProfile |
| §1.5 ML-depth (`ml_depth_factor`) | module3_capability_fit | from `ml_relevant_months` (Module 2); `base·E·D` |
| §1.5 `ml_relevant_months` (N1–N7 role-tenure sum) | module2_capability | same ontology scan as `node_strengths`; no extra pass |
| §2 capability ontology + `node_strength` + `base_capability` | module2_capability | description-primary; assessment-secondary |
| §2 assessment-secondary gating | module2_capability | uses `skill_assessment_scores` where present |
| §3 behavioral sub-scores + multiplier | module4_behavioral | incl. §3.2 logistics, §3.3 sentinels, §3.4 multiplier |
| §4 honeypot H1/H2 | module5_honeypot | |
| §5 final ranking / selection | module6_ranking | |
| §6 CSV output schema | module8_submission | |
| §6 reasoning generation | module7_reasoning | |
| §6 final-output validation (validate_submission rules) | module8_submission / SubmissionValidator | hard gate — see §8 |

No section is unowned; no section is shared by two modules. (Data files
`ai_capability_ontology.json` / `jd_rubric.json` carry §1/§2 *values*; the *logic*
that applies them is owned as above.)

---

## 6. Files reused from WorkLens (copied/adapted) — and why each is safe

Reuse = **generic engineering infrastructure with no embedded Backend-domain
assumptions.** Each is copied into `worklens_redrob/` (the original `worklens/`
stays byte-for-byte unchanged); none imports from `worklens/`.

| WorkLens file | Reuse as | Why safe (no Backend-domain assumption) |
|---|---|---|
| `shared/utils/phrase_matcher.py` | `shared/utils/phrase_matcher.py` | Pure text matching: word-boundary for short terms, substring for stems, span-overlap helper. Operates on arbitrary phrase lists; knows nothing about Backend nodes. Used here to detect AI-ontology phrases in candidate text. |
| `shared/utils/signal_loader.py` | basis for `shared/utils/ontology_loader.py` | Generic "JSON → dataclass" loader (name/strong/weak). Adapted only to add the `importance` field. No Backend vocabulary embedded — vocabulary comes from the (new) data file. |
| `shared/config/paths.py` (pattern) | `shared/config/paths.py` | Project-root resolution via `Path(__file__).parents`. Pure path handling; the *values* are replaced with RedRob paths. |
| `shared/config/__init__.py` (re-export pattern) | `shared/config/__init__.py` | Structural pattern (focused config modules re-exported). No values reused. |
| logging convention (`logging.getLogger(__name__)` per module) | same convention | Standard-library logging idiom; no domain content. |
| pytest layout (`tests/__init__.py`, per-module `tests/`, fixture style) | same layout | Test-infrastructure pattern only; no Backend tests copied. |

Everything above is **infrastructure**; all **domain** content (vocabulary,
weights, formulas) is supplied by new data/config, per the build authorization.

---

## 7. Files rewritten from scratch — and why WorkLens's version doesn't apply

| Concern | WorkLens file (not reused) | Why it doesn't apply |
|---|---|---|
| Capability vocabulary | `ontology/ontology_nodes.json`, `data/ontology/capability_signals.json` | Backend Engineer domain (12 backend nodes). RedRob needs the 9 AI/IR nodes from §2. |
| Co-occurrence activation | `shared/utils/cooccurrence.py`, `shared/utils/windowing.py` | WorkLens activates via "strong≥1 OR distinct-weak≥3 per window". RedRob §2 uses a different rule (source-based: career-description vs skill-list, assessment-gated) — the weak-count engine does not apply. |
| Portal/sidebar noise | `shared/utils/noise_filter.py` | Backend JDs were noisy Naukri HTML. RedRob input is clean structured JSON — no portal noise. |
| Résumé/JD text parsing | `shared/utils/document_parsing.py`, `ontology/jd_parser.py`, `ontology/resume_parser.py`, `ontology/pdf_to_text.py` | RedRob has **no** résumé text / PDFs; input is structured `candidate_schema.json`. |
| Scoring constants | `shared/config/scoring.py`, `shared/config/extraction.py` | Backend importance/strength/coverage/role-extraction constants. RedRob constants come from `REDROB_SCORING_DESIGN.md`. |
| All schemas | `shared/models/*` | Backend profiles (JDCapabilityProfile, CandidateCapabilityProfile, MatchingResult…). RedRob schemas differ entirely (see interface_contract.md). |
| Per-candidate scoring/ranking | `modules/module1..5` (Backend) | Backend importance/strength/coverage/tiebreaker formulas. RedRob derives all of §1–§6 anew. |
| Input reader | — (WorkLens read `.txt` files) | New `jsonl_reader.py` for streaming 100K JSONL with validation. |
| Output writer + validator | — (WorkLens emitted report objects) | New CSV writer + `SubmissionValidator` enforcing the RedRob spec. |
| Recency/date math | (embedded in WorkLens M2 résumé date parsing) | Different inputs (ISO dates, AS_OF recency bands); new `date_utils.py`. |

---

## 8. Enforcement of `validate_submission.py` — named owner of the hard gate

**Owner: `modules/module8_submission/validator.py` → `SubmissionValidator`.**
This is a **mandatory pass/fail gate**, invoked by `rank.py` **after** rows are
built and **before/at** write; if any check fails, the run **aborts with a
non-zero exit** (no partial/invalid CSV is accepted as success). It mirrors the
official `validate_submission.py` exactly:

| Requirement (from `validate_submission.py`) | Enforced by `SubmissionValidator` |
|---|---|
| Header is exactly `candidate_id,rank,score,reasoning` | header assertion |
| Exactly 100 data rows | `len(rows) == 100` |
| `candidate_id` matches `^CAND_[0-9]{7}$` | regex per row |
| Each `candidate_id` unique | set-size check |
| **Every `candidate_id` exists in the pool** | membership against the id-set captured by `jsonl_reader` (passed in) |
| Each rank 1..100 exactly once | `sorted(ranks) == list(range(1,101))` |
| `score` parses as float | type check |
| `score` non-increasing by rank | adjacent-pair check on rank-sorted rows |
| Equal scores ⇒ `candidate_id` ascending | adjacent-pair tie check |
| Not all scores identical (spec §6 "model isn't differentiating" — not auto-checked by the official validator) | guard: assert `len(set(scores)) > 1` |
| File is `.csv`, UTF-8 | extension + encoding on write |

**Two-layer assurance (not "somewhere"):**
1. **By construction (module6_ranking):** sorts on `(round(final,6) DESC, candidate_id ASC)` and assigns ranks 1..100, so non-increasing-score and the equal-score→candidate_id-ascending rule hold *as produced*.
2. **By verification (module8 SubmissionValidator):** independently re-checks all of the above on the final rows — it does not trust construction. The pool id-set is threaded in explicitly so "every id exists in the pool" is a real check, not an assumption.
3. **Belt-and-suspenders (rank.py):** after writing, `rank.py` may shell the **official** `validate_submission.py` on the produced file as a final external confirmation (optional but recommended; documented in README).

The validation gate is therefore a single, named, testable owner — not implicit
in the CSV writer.

---

## Phase 0 exit
This package (folder structure, interface contract, module plan, data flow,
section→module mapping, reuse list, rewrite list, validation ownership) is the
complete pre-implementation architecture. **Awaiting review/approval before any
implementation code is written.** Original `worklens/` untouched; no module code,
no placeholder classes created.
