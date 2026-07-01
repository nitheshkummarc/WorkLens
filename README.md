# WorkLens-RedRob

Ranks the top 100 candidates for the Senior AI Engineer role out of the 100k-row
`candidates.jsonl` and writes `submission.csv` (`candidate_id,rank,score,reasoning`).
It's a deterministic, CPU-only rule-based ranker — no ML model, no embeddings, no
network calls — and its only runtime dependency is `pydantic`.

**Live demo:** https://huggingface.co/spaces/nitheshkummar/redrob — rank a small
candidate sample in the browser.

## Overview

**Challenge Overview:** RedRob's *Intelligent Candidate Discovery & Ranking* task: from a pool
of 100,000 profiles, return the 100 best fits for a fixed **Senior AI Engineer** job
description — in under 5 minutes, on 16 GB CPU, with no GPU and no network. The dataset is
seeded with traps: keyword-stuffers (e.g. an HR Manager listing 9 AI skills), plain-language
strong fits, and ~80 "honeypot" profiles that are subtly impossible.

**The approach:** An LLM or embedding search can't scale to 100K within the time budget and
tends to reward keyword overlap, so this is a transparent scoring engine instead. The core design principle is simple: **score what a candidate demonstrably did in their career history, not what they list as skills.** A capability score is built from that, rescaled by a behavioral multiplier
(recency, responsiveness, availability), and provably-impossible profiles are forced to zero.
Every ranking comes with a one-sentence, fact-based reason.

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/mac: source .venv/bin/activate
pip install -r requirements.txt

python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

`candidates.jsonl` isn't in the repo  — point `--candidates` at your copy
(a plain `.jsonl` or a gzipped `.jsonl.gz` both work). Check the result with the official
validator:

```bash
python validate_submission.py submission.csv
```

## Reproducing the submission (Stage 3)

- **One command**, shown above, turns the candidate file into the CSV — no hidden steps or
  manual edits. Name the output : `--out ./<team-name>.csv`.
- **No pre-computation** — no embeddings, indexes, or model weights; the only inputs are the
  two committed files under `data/`, so there's nothing to build first.
- **Dependencies:** `requirements.txt` (only `pydantic` at ranking time; `pytest` for tests).
- **Compute:** ~2 minutes on a single CPU core — inside the 5 min / 16 GB / CPU-only /
  no-network limits.
- **Metadata:** `submission_metadata.yaml` at the repo root mirrors the portal fields.
- **Docker:** a `Dockerfile` is included for a clean-room run (`docker build` + `docker run`).

## How the score works

For each candidate:

```
final = 0                                  if the profile is a honeypot
final = capability_fit * behavioral_mult   otherwise
```

`capability_fit` is how well the person matches the JD. `behavioral_mult` (0.5–1.0)
moves that up or down by how active, available and responsive they are. Capability
is the driver; behaviour only rescales it.

```
capability_fit = clamp( base * experience_factor * ml_depth_factor - penalties + bonus )
base           = importance-weighted match across 9 areas
                 (retrieval, embeddings, ranking, evaluation, ML production,
                  NLP, LLM, data pipelines, scale)
```

The important part: credit comes from what someone actually describes doing in their
career history, not from their skills list. That's what keeps keyword-stuffers out of
the top. Penalties cover JD red flags (research-only, consulting-only, LangChain-only,
etc.). Honeypots — impossible profiles like "expert in 5 skills with 0 months used" —
are forced to 0 so they can't reach the top 100.

Recency is measured against a fixed date (2026-05-27, the latest `last_active_date` in
the data), not the clock, so the same input always gives the same output.

## Layout

```
rank.py        entrypoint
data/          capability ontology + JD rubric (committed)
shared/        config (all the constants), pydantic models, utils
modules/       module1..8, one job each
docs/          methodology write-up
```

Module order: 1 JD rubric → 2 capability → 3 capability fit → 4 behavioural →
5 honeypot → 6 ranking (streaming top-100 heap) → 7 reasoning → 8 CSV + validation.


## Verification

- `pytest` (from the repo root) covers the scoring, ranking tie-breaks, honeypot rules,
  phrase-matcher equivalence, and the submission validator.
- Checked against the full 100k pool: the official validator passes, two runs produce a
  byte-identical CSV, and every reasoning line is verified against the candidate's own fields.
- AI tools were used for code review and discussion; no candidate data was sent to any LLM,
  and the ranker itself makes no API calls.
