# Methodology

## The short version

We rank 100,000 candidates against one fixed "Senior AI Engineer" job description and
return the best 100 — in about two minutes, on a normal laptop CPU, with no GPU, no
internet, and no machine-learning model. It's a plain, rule-based scoring engine you
can read end to end.

Everything rests on one idea: **judge people on what they actually did at work, not on
the keywords in their skills list.** Someone who describes building a recommendation
system gets full credit for it; someone who just lists "RAG" as a skill gets half. That
single choice is what stops keyword-stuffers from winning — and it's why none of the 100
profiles the sample submission ranks make it into our top 100.

## How a candidate is scored

`final = 0` if the profile is impossible (a "honeypot"); otherwise
`final = capability_fit × behavioral_multiplier`.

**1. Turn the job description into a checklist.** We break the JD into nine skill areas
(search, embeddings, ranking, evaluation, production ML, NLP, LLMs, data pipelines,
scale) and weight each by how much the role really needs it. The things the JD says it
does *not* want — pure research, consulting-only, LangChain-only, and so on — become
penalties. All of this lives as data, not hard-coded in the logic.

**2. Score capability from evidence.** For each skill area we look in two places: the
person's career history (what they *did*) and their summary and skills list (what they
*claim*). Work shown in the career history earns full marks; a bare claim earns half;
nothing earns zero. We then take an importance-weighted average.

**3. Adjust for fit.** We nudge that score by how much experience they have (the JD
likes 5–9 years), how much of that was actually in ML, and the JD penalties — plus a
small bonus for nice-to-have skills.

**4. Factor in availability.** The platform gives 23 engagement signals — how recently
someone logged in, how fast they reply to recruiters, whether they're open to work,
notice period, location, and so on. We turn the useful ones into a 0.5–1.0 multiplier.
It only rescales the capability score: a strong-but-inactive candidate is dialled down,
never dropped.

**5. Remove the impossible.** A few profiles are physically impossible — "expert in
five skills with zero months of use," or more career history than their total years of
experience. Two simple checks catch these and set their score to zero.

**6. Pick the top 100 and explain each one.** As we read the file we keep only the best
100 so far in memory (a small heap), so we never sort all 100,000. Each of the 100 gets
a one-sentence reason built only from that person's own profile — no invented facts —
and a final check confirms the CSV is valid before it's written.

## Why it holds up

- **Fast and light:** one pass over the file and a fixed-size heap — about two minutes
  for 100,000 profiles on a single CPU core, well inside the limits.
- **Repeatable:** the same input always produces the exact same file.
- **Honest:** every ranking can be explained, and the reasons never mention anything
  that isn't in the candidate's profile.
- **Not fragile:** nudging the weights by ±15% barely moves the top of the list — the
  top 10 stay about 97% the same — so the result doesn't hinge on any one number.
