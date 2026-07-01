# WorkLens-RedRob

Ranks the top 100 candidates for the Senior AI Engineer role out of the 100k-row
`candidates.jsonl` and writes `submission.csv` (`candidate_id,rank,score,reasoning`).

There's no ML model, no embeddings and no network calls. It's a deterministic
rule-based ranker: read each profile, score how well it matches the JD, then nudge
that score by the candidate's engagement signals. Runs on CPU in a couple of
minutes. The only runtime dependency is `pydantic`, used to validate the input.

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/mac: source .venv/bin/activate
pip install -r requirements.txt

python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

`candidates.jsonl` isn't in the repo (it's ~465 MB) — point `--candidates` at your
copy. The files under `data/` are committed, so there's nothing to precompute.

Check the result with the official validator:

```bash
python validate_submission.py submission.csv
```

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
the top without needing an LLM. Penalties cover JD red flags (research-only, consulting-
only, LangChain-only, etc.). Honeypots — impossible profiles like "expert in 5 skills
with 0 months used" — are forced to 0 so they can't reach the top 100.

Recency is measured against a fixed date (2026-05-27, the latest `last_active_date` in
the data), not the clock, so the same input always gives the same output.

## Layout

```
rank.py        entrypoint
data/          capability ontology + JD rubric (committed)
shared/        config (all the constants), pydantic models, utils
modules/       module1..8, one job each
docs/          design notes + interface contract
```

Module order: 1 JD rubric → 2 capability → 3 capability fit → 4 behavioural →
5 honeypot → 6 ranking (streaming top-100 heap) → 7 reasoning → 8 CSV + validation.

## Notes

- Streams the file and keeps only the top 100 in memory, so it stays well inside the
  16 GB / 5 min / CPU-only limits. Output is byte-for-byte reproducible.
- Verified against the full 100k pool: the official validator passes, two runs match
  exactly, and every reasoning line is checked against the candidate's own fields.
- `pytest` covers the scoring, ranking tie-breaks, honeypot rules, phrase-matcher
  equivalence and the submission validator (`pytest` from the repo root).
- AI tools were used for code review and discussion while building this. No candidate
  data was sent to any LLM, and the ranker itself makes no API calls.
```
