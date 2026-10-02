# Performance

How the ranking run was made about 2.8× faster, with the measurements behind it.

## Result

| | Before | After |
|---|---|---|
| Full run, 100K candidates (wall time) | about 45-50 s | about 17-30 s |
| CPU time, old and new code alternated on the same machine (3 rounds) | 75.0-76.9 s | 26.6-27.3 s (about 2.8×) |
| module2 (capability extraction), timed inside a full run | 39.9 s | 4.5-6.3 s |
| module2 vs. a per-phrase regex reference with the same rules, all 100K candidates | 612.7 s | 5.7 s (108×) |
| Output of the speed-up itself | — | byte-identical CSV |

The current figures include the negation, corroboration and availability rules added after the speed-up (RANKING_REVIEW.md); those changed the ranking on purpose, so "byte-identical" refers to the caching change measured on its own. Absolute times on this laptop vary by up to 2× with thermal state, so the paired CPU-time ratio is the reliable figure. Reproduce the module2 comparison with:

```bash
python tools/bench_matcher.py --candidates ./candidates.jsonl --sample 100000
```

---

## 1. Measure first

Per-stage timing over the full pool showed where the time went:

| Stage | Share of run time |
|---|---|
| module2: capability phrase matching | 65% |
| module3: anti-signal phrase matching | 16% |
| JSON parsing | 7% |
| Pydantic validation | 6% |
| module4-6 and file reading | 6% |

About 80% of the run was phrase matching: roughly 120 ontology phrases checked against each candidate's text, about 4 million Python-level checks per run.

## 2. Find the redundancy in the data

The candidate texts are heavily repeated:

- 300,171 career entries contain only **340 distinct role texts** (title plus description).
- Across all text parts that module2 reads (titles, descriptions, summaries, headlines, skill names) there are only **5,935 distinct strings**.

The old code still rescanned every phrase against every candidate's full text.

## 3. The change

### Match each text part once, cache the result

`PhraseIndex` (`shared/utils/phrase_matcher.py`) returns the set of vocabulary phrases found in one text part. It is wrapped in `functools.lru_cache` (65,536 entries), so each distinct part is scanned once per run.

module2 (`modules/module2_capability/extractor.py`) now:

1. looks up the cached phrase set for each part: current title, every role title and description, summary, headline and each skill name;
2. unions those sets into one set for career evidence and one for self-reported evidence;
3. scores each node with ordered set lookups ("first strong phrase of this node that is in the set") instead of rescanning text;
4. decides ML relevance per role from the same cached sets.

On the full pool the cache served 2,472,119 lookups and missed 5,935 times (99.8% hits).

### Why the result is exactly the same

The old code matched phrases against the parts joined with newlines. No phrase contains a newline (enforced in `PhraseIndex`), so a match can never span two parts. A match at a part's edge sees either a newline or the start/end of the string next to it, and the word-boundary rule treats both the same way. So the phrases found in the joined text are exactly the union of the phrases found in each part.

This was verified three ways:
- the full-pool CSV is byte-identical before and after;
- `tools/bench_matcher.py` compares every `CapabilityProfile` against the regex reference;
- the test suite passes unchanged.

### Skip absent phrases cheaply

In `PhraseGroup`, each phrase is first checked with `core in text` (a C-level substring test). The Python word-boundary check runs only when the substring is present. Most phrases are absent from most texts, so this removes most Python function calls. It also speeds up module3, which uses `PhraseGroup` directly. Measured alone, it cut module2+module3 time by about 22%.

## 4. What was tried and rejected

| Idea | Result |
|---|---|
| One combined regex per phrase list | about 6× slower: Python's regex engine cannot optimise a large alternation with lookbehinds |
| `Candidate.model_validate_json(line)` instead of `json.loads` + `model_validate` | no measurable gain |
| Pre-filter ML-tenure phrases against the whole career text | slower: the per-role check already stops at the first match |
| Multiprocessing across cores | not adopted; the submission describes a single-core run |

## 5. Trade-offs and limits

- The large gain depends on repeated text, which this pool has. On a pool where every description is unique, the cache would mostly miss and the gain would shrink to the prefilter's (about 20%).
- The cache is bounded (65,536 entries), so memory stays capped regardless of input size.
- After the change, module3 (anti-signals, about 33%), JSON parsing (15%), Pydantic validation (13%) and module2 (25%) make up most of the run. The same per-part caching could be applied to module3.

---

## How to explain it in an interview

> "I profiled the run per stage and found 80% of the time was phrase matching, mostly in module2. Then I looked at the data: 300,000 career entries contained only 340 distinct role texts, and only about 6,000 distinct text parts overall. But we were rescanning about 120 phrases against every candidate's full text.
>
> Because no phrase can contain a newline, matching the joined text gives exactly the union of matching each part separately. So I match each distinct part once, cache the set of phrases it contains with an LRU cache, and score each candidate by set lookups. The cache hit rate is 99.8%.
>
> module2 went from about 40 seconds to about 5, and the whole run is about 2.8× faster in alternating runs on the same machine. The CSV is byte-identical, and a benchmark script checks every profile against a straightforward regex implementation. The trade-off is that the gain depends on repeated text; on fully unique text it falls back to a cheap substring prefilter, which still gives about 20%."

**Likely follow-ups**

- *How do you know it's correct?* Byte-identical CSV on the full pool, a profile-by-profile comparison against the regex reference (`tools/bench_matcher.py`), and the test suite.
- *Why not multiprocessing?* It would give more, but the submission is documented as single-core, and this was an algorithmic fix that needs no extra hardware.
- *Why an LRU cache and not a plain dict?* It bounds memory; on unusual input the cache cannot grow without limit.
- *What would you optimise next?* module3 with the same per-part caching, then JSON parsing (for example `orjson`).
