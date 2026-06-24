# WorkLens-RedRob — Interface Contract (Phase 0, frozen before implementation)

Source of truth for all domain logic: **`REDROB_SCORING_DESIGN.md` v1 (trace-corrected)**.
This contract defines every schema and module boundary. Once approved it is frozen;
a later-discovered need to change a schema → stop, explain, get approval (same
discipline as the original WorkLens Phase 0).

**Determinism / constraints:** CPU-only, network-off at ranking time, ≤5 min / ≤16 GB.
No LLM in the ranking path (embedding node N10 is specified but **off in v1**).

**Single-producer rule (one metric → one module):** see §"Metric ownership" in
`PHASE0_ARCHITECTURE.md`. Every field below names its producing module.

All models are Pydantic v2 (validated at boundaries). Types are exact.

---

## 1. Candidate input model — mirrors `candidate_schema.json` exactly
Produced by: **`shared/utils/jsonl_reader`** (parse) → validated into these models. Owned by shared (infra), consumed by Modules 2–5.

```python
CompanySize = Literal["1-10","11-50","51-200","201-500","501-1000","1001-5000","5001-10000","10001+"]

class Profile(BaseModel):
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float = Field(ge=0, le=50)
    current_title: str
    current_company: str
    current_company_size: CompanySize
    current_industry: str

class CareerEntry(BaseModel):
    company: str
    title: str
    start_date: str                 # ISO date "YYYY-MM-DD"
    end_date: Optional[str]         # null when current
    duration_months: int = Field(ge=0)
    is_current: bool
    industry: str
    company_size: CompanySize
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: Literal["tier_1","tier_2","tier_3","tier_4","unknown"]   # institution prestige (NOT relevance tier)

class Skill(BaseModel):
    name: str
    proficiency: Literal["beginner","intermediate","advanced","expert"]
    endorsements: int = Field(ge=0)
    duration_months: Optional[int] = Field(default=None, ge=0)

class Certification(BaseModel):
    name: str; issuer: str; year: int

class Language(BaseModel):
    language: str
    proficiency: Literal["basic","conversational","professional","native"]

class RedrobSignals(BaseModel):           # all 23 signals
    profile_completeness_score: float = Field(ge=0, le=100)
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool
    profile_views_received_30d: int = Field(ge=0)
    applications_submitted_30d: int = Field(ge=0)
    recruiter_response_rate: float = Field(ge=0, le=1)
    avg_response_time_hours: float = Field(ge=0)
    skill_assessment_scores: dict[str, float] = Field(default_factory=dict)  # skill -> 0..100
    connection_count: int = Field(ge=0)
    endorsements_received: int = Field(ge=0)
    notice_period_days: int = Field(ge=0, le=180)
    expected_salary_range_inr_lpa: dict[str, float]                          # {"min":..,"max":..}
    preferred_work_mode: Literal["remote","hybrid","onsite","flexible"]
    willing_to_relocate: bool
    github_activity_score: float = Field(ge=-1, le=100)                      # -1 = no github
    search_appearance_30d: int = Field(ge=0)
    saved_by_recruiters_30d: int = Field(ge=0)
    interview_completion_rate: float = Field(ge=0, le=1)
    offer_acceptance_rate: float = Field(ge=-1, le=1)                        # -1 = no history
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool

class Candidate(BaseModel):
    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    profile: Profile
    career_history: list[CareerEntry] = Field(min_length=1, max_length=10)
    education: list[Education] = Field(default_factory=list, max_length=5)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    redrob_signals: RedrobSignals
```

### 1a. `jsonl_reader` behavior (robustness + pool-id accumulation)
`shared/utils/jsonl_reader` streams `candidates.jsonl` one line at a time and yields validated
`Candidate` objects. Required behavior (frozen):
- **Malformed-line handling (never abort on one bad line):** if a line is truncated/invalid JSON
  or fails `Candidate` validation (missing required fields, bad types), **skip it, log a warning,
  increment a `skipped_records` counter, and continue.** The run only aborts on catastrophic I/O
  (file unreadable), never on a single bad record. `skipped_records` is reported at end of run.
- **Pool-ID accumulation:** while streaming, accumulate a `set[str]` of **all valid
  `candidate_id`s seen** (~5–8 MB for 100K ids). This set is returned/exposed alongside the
  stream and **threaded through `rank.py` into `module8_submission`**, so module8's "every
  top-100 id exists in the pool" check (§9) is a **real membership test, not an assumption**.

---

## 2. Ontology node model (§2 data) — `data/ai_capability_ontology.json`
Produced/loaded by: **`shared/utils/ontology_loader`**. Consumed by Module 1 (importances) & Module 2 (phrase matching).

```python
class OntologyNode(BaseModel):
    name: str                       # e.g. "Retrieval & Search"
    importance: float = Field(ge=0, le=1)     # node-specific weight (six distinct values; see design §2) — the scoring driver
    strong_phrases: tuple[str, ...]
    weak_phrases: tuple[str, ...]
```
The 9 nodes (N1–N9) and their importances/phrases are fixed per `REDROB_SCORING_DESIGN.md` §2. **N10 (semantic_recall / embeddings) is NOT present in v1.**

---

## 3. JD profile model (§1 rubric) — output of Module 1
Produced by: **`module1_jd_rubric`**. Built from `data/ai_capability_ontology.json` + `data/jd_rubric.json` (the §1.2/§1.3/§1.4/§3-logistics-targets config encoded from the JD). Consumed by Modules 2, 3.

```python
class CapabilityRequirement(BaseModel):
    name: str
    importance: float               # node-specific weight from the ontology — the scoring value
    tier: Literal["Critical","High","Medium","Nice"]   # DISPLAY-ONLY coarse bucket of `importance`; never the scoring input (importance is). Weights are node-specific, not tiered.

class AntiSignalRule(BaseModel):
    key: str                        # "research_only" | "consulting_only" | "langchain_only" | ...
    penalty: float                  # e.g. 0.25, 0.125, 0.20, 0.15, 0.10
    is_hard_dq: bool                # True ONLY for "research_only"

class ExperienceBand(BaseModel):
    lo: float; hi: float; factor: float    # e.g. (5,9,1.00)

class JDProfile(BaseModel):
    role: str                                   # "Senior AI Engineer"
    required_capabilities: list[CapabilityRequirement]   # all 9 nodes w/ importance+tier
    critical_nodes: list[str]
    nice_to_have_nodes: list[str]               # §1.2
    nice_bonus_per_item: float                  # +0.03
    nice_bonus_cap: float                       # +0.10
    anti_signals: list[AntiSignalRule]          # §1.3 (consulting_only.penalty=0.125, is_hard_dq=False)
    anti_penalty_cap: float                     # 0.50
    hard_dq_base_ceiling: float                 # 0.30
    experience_bands: list[ExperienceBand]      # §1.4
    consulting_companies: tuple[str, ...]       # employer list for consulting soft-penalty
    logistics_target_cities: tuple[str, ...]    # §3.2 location_factor
```

---

## 4. Capability profile model (§2) — output of Module 2
Produced by: **`module2_capability`**. Owns `node_strengths` + `base_capability` + `ml_relevant_months`. Consumed by Modules 3, 7.

```python
class NodeEvidence(BaseModel):
    node: str
    strength: Literal[0.0, 0.5, 1.0]
    source: Literal["career_description","skill_verified","skill_unverified","none"]
    evidence_phrase: Optional[str]      # the matched phrase / skill name (for reasoning)

class CapabilityProfile(BaseModel):
    candidate_id: str
    node_strengths: list[NodeEvidence]  # one per ontology node (all 9 present)
    base_capability: float = Field(ge=0, le=1)   # Σ(importance·strength)/Σ importance
    ml_relevant_months: int = Field(ge=0)        # §1.5 — Σ duration_months of career roles
                                                 #   whose title/desc matches nodes N1–N7
                                                 #   (same ontology scan; no extra pass)
```

---

## 5. Capability-fit model (§1 adjustments + §0 capability_fit) — output of Module 3
Produced by: **`module3_capability_fit`**. Owns `anti_penalty`, `experience_factor`, `ml_depth_factor`, `nice_bonus`, `hard_dq`, and the combined `capability_fit`. Consumed by Module 6 (ranking) and Module 7 (reasoning).

```python
class CapabilityFit(BaseModel):
    candidate_id: str
    base_capability: float              # carried from Module 2 (input)
    anti_signals_fired: list[str]       # keys that fired
    anti_penalty: float = Field(ge=0, le=0.50)
    hard_dq: bool                       # research_only only
    experience_factor: float = Field(ge=0, le=1)
    ml_depth_factor: float = Field(ge=0.85, le=1.10)  # §1.5 — from ml_relevant_months (Module 2)
    nice_items: list[str]
    nice_bonus: float = Field(ge=0, le=0.10)
    capability_fit: float = Field(ge=0, le=1)   # clamp01(min(base,0.30 if hard_dq)·E·D − anti + nice)
```

---

## 6. Behavioral profile model (§3) — output of Module 4
Produced by: **`module4_behavioral`**. Owns all 8 sub-scores, `behavioral_raw`, `behavioral_multiplier`. Consumed by Module 6 and Module 7.

```python
class BehavioralProfile(BaseModel):
    candidate_id: str
    recency: float; responsiveness: float; open: float; interview: float
    offer: float; logistics: float; demand: float; trust: float   # each ∈ [0,1]
    behavioral_raw: float = Field(ge=0, le=1)
    behavioral_multiplier: float = Field(ge=0.50, le=1.0)
```
AS_OF (recency reference date) is a `RunConfig` value (validated dataset max `last_active_date` = 2026-05-27), passed in — never `datetime.now()`.

---

## 7. Honeypot analysis model (§4) — output of Module 5
Produced by: **`module5_honeypot`**. Sole owner of `is_honeypot`. Consumed by Module 6 (floor) and Module 7 (reasoning).

```python
class HoneypotAnalysis(BaseModel):
    candidate_id: str
    is_honeypot: bool
    rule_fired: Optional[Literal["H1","H2"]]    # H1 expert-0-duration · H2 tenure>life
    evidence: Optional[str]                      # e.g. "expert in MLflow/Photoshop/Content Writing with 0 months"
```

---

## 8. Ranking result model (§0 final + §5) — output of Module 6
Produced by: **`module6_ranking`**. Sole owner of `final_score` and `rank`.

```python
class CandidateScore(BaseModel):                # internal, all candidates
    candidate_id: str
    capability_fit: float
    behavioral_multiplier: float
    is_honeypot: bool
    final_score: float                          # 0.0 if honeypot else capability_fit·multiplier

class RankedCandidate(BaseModel):               # top-100 only
    candidate_id: str
    rank: int = Field(ge=1, le=100)
    score: float                                # round(final_score, 6) — the emitted CSV score
```
**Sort key (frozen):** `(score DESC, candidate_id ASC)` where `score = round(final_score,6)`.
Sorting on the *rounded* score (not raw final) guarantees the validator's tie rule —
equal emitted scores ⇒ candidate_id ascending — holds exactly.

---

## 9. CSV output model (§6) — output of Module 8
Produced by: **`module8_submission`**. Owns CSV serialization **and** final-output validation.

```python
class SubmissionRow(BaseModel):
    candidate_id: str = Field(pattern=r"^CAND_[0-9]{7}$")
    rank: int = Field(ge=1, le=100)
    score: float
    reasoning: str                              # from Module 7
```
CSV header (exact order): `candidate_id,rank,score,reasoning`. UTF-8. Header + exactly 100 data rows.

---

## 10. Reasoning (§6) — output of Module 7
Produced by: **`module7_reasoning`**. Owns the `reasoning` string. Input: `Candidate` + its `CapabilityProfile`, `CapabilityFit`, `BehavioralProfile`, `HoneypotAnalysis`. Output: `str` (1–2 sentences, fact-grounded, varied, concern-aware) per `REDROB_SCORING_DESIGN.md` §6 template. No hallucination: every claim drawn from the candidate's own fields / matched nodes.

---

## 11. Run configuration — `shared/config`
```python
class RunConfig(BaseModel):
    candidates_path: Path
    job_description_path: Path
    ontology_path: Path
    jd_rubric_path: Path
    output_path: Path
    as_of_date: str = "2026-05-27"      # dataset max last_active_date (deterministic)
```
All numeric constants (behavioral weights/tables §3, anti penalties §1.3, experience bands §1.4, nice bonus §1.2, honeypot thresholds §4, fit floor §3.4, assessment gates §2) live in `shared/config/*` — never hardcoded in logic. Values are taken verbatim from `REDROB_SCORING_DESIGN.md`.

---

## Boundary summary (who hands what to whom)
```
jsonl_reader → Candidate
Module1(JDProfile)  ─┐
Candidate ──────────┼→ Module2 → CapabilityProfile ─┐
Candidate, JDProfile ┘                               ├→ Module3 → CapabilityFit ┐
Candidate ──────────────────────→ Module4 → BehavioralProfile ─────────────────┤
Candidate ──────────────────────→ Module5 → HoneypotAnalysis ──────────────────┤
                                                                                ├→ Module6 → RankedCandidate[100]
Candidate + (CapabilityProfile,CapabilityFit,BehavioralProfile,HoneypotAnalysis)→ Module7 → reasoning
RankedCandidate[100] + reasoning → Module8 → submission.csv  (+ SubmissionValidator hard gate)
```
