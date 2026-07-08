# WorkLens

**Deterministic Candidate Ranking Engine**

A deterministic candidate ranking engine that evaluates 100,000 candidate profiles against a structured job specification in under 2 minutes on a single CPU core. Designed for explainability, reproducibility, and configuration-driven evaluation with no runtime network dependencies.

<<<<<<< HEAD
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
=======

[🚀 Live Demo](https://huggingface.co/spaces/nitheshkummar/redrob)

![WorkLens Demo](assets/Worklens.png)
>>>>>>> b061914 (Refined README.md and documenation)

---

## ⚡ Engineering Highlights

- ✅ **Configuration-driven evaluation pipeline** — adapt to any role by editing JSON, zero code changes
- ✅ **O(N log K) streaming top-K ranking** — bounded min-heap, constant memory over any input size
- ✅ **Deterministic and explainable scoring** — same input → byte-identical output, every rank justified
- ✅ **CPU-only execution** — no GPU, no network, no pre-computation
- ✅ **Constant-memory processing** — streams 465 MB input without loading it into memory
- ✅ **Strong interface contracts with Pydantic schemas** — typed schemas at every module boundary, malformed data fails fast

---

## 📊 Performance

| | |
|---|---|
| 📦 **100K Candidates** | Processed in a single streaming pass |
| ⏱️ **< 2 min** | Wall time on a single CPU core |
| 💾 **O(K) Memory** | Only top-100 held in memory, not the full pool |
| 📐 **O(N log K)** | Heap insert per candidate — no full sort |
| 🔁 **Deterministic** | Byte-identical output across runs — no wall-clock dependency |
| 📦 **1 Dependency** | `pydantic` — stdlib `csv`, `json`, `heapq` handle the rest |

---

## 🏗️ System Architecture

![System Architecture](assets/System%20architecture.png)

An 8-stage streaming pipeline. Each candidate is scored through modules 2–5, inserted into the bounded top-K heap (module 6), and discarded — the full pool is never held in memory. Only the retained top-K receive reasoning (module 7) and validation (module 8) before output.

> [📖 Read the full architecture deep-dive →](docs/ARCHITECTURE.md)

---

## Quick Start

### Local

```bash
python -m venv .venv && .venv\Scripts\activate    # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python rank.py --candidates ./candidates.jsonl --out ./output.csv
```

<<<<<<< HEAD
`candidates.jsonl` isn't in the repo  — point `--candidates` at your copy
(a plain `.jsonl` or a gzipped `.jsonl.gz` both work). Check the result with the official
validator:
=======
### Docker
>>>>>>> b061914 (Refined README.md and documenation)

```bash
docker build -t worklens .
docker run --rm -v "$PWD:/data" worklens \
    --candidates /data/candidates.jsonl --out /data/output.csv
```

> Both `.jsonl` and `.jsonl.gz` inputs are supported transparently.

<<<<<<< HEAD
- **One command**, shown above, turns the candidate file into the CSV — no hidden steps or
  manual edits. Name the output : `--out ./submission.csv`.
- **No pre-computation** — no embeddings, indexes, or model weights; the only inputs are the
  two committed files under `data/`, so there's nothing to build first.
- **Dependencies:** `requirements.txt` (only `pydantic` at ranking time; `pytest` for tests).
- **Compute:** ~2 minutes on a single CPU core — inside the 5 min / 16 GB / CPU-only /
  no-network limits.
- **Metadata:** `submission_metadata.yaml` at the repo root mirrors the portal fields.
- **Docker:** a `Dockerfile` is included for a clean-room run (`docker build` + `docker run`).
=======
---
>>>>>>> b061914 (Refined README.md and documenation)

## Repository Structure

```
rank.py              → Pipeline entrypoint
data/                → Capability ontology + job rubric (configuration)
shared/
  ├── config/        → All scoring constants, paths, runtime config
  ├── models/        → Pydantic schemas (interface contracts)
  └── utils/         → Phrase matching, JSONL streaming, date math
modules/             → 8 single-responsibility pipeline stages
tests/               → pytest suite (32 tests)
docs/                → Architecture, methodology, design rationale
```

---

## Testing

```bash
pytest -v    # 32 tests — scoring, ranking, honeypot, phrase matching, output validation
```

<<<<<<< HEAD
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
=======
All tests use synthetic candidates built in-process — no dependency on the full dataset.
>>>>>>> b061914 (Refined README.md and documenation)
