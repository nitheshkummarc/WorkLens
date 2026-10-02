# Ranking Review: Top 100 vs. the Job Description

An independent check of `outputs/submission.csv` against the Senior AI Engineer job description (`job_description.docx`). Each ranked candidate was judged from their raw profile, not from WorkLens's scores. The review was run on the original output, the scoring was fixed, and the review was run again with the same grading.

## Summary

| | Top 10 | Top 100 | Strong matches captured |
|---|---|---|---|
| Before the fixes | 8 Strong, 1 Good, 1 Weak | 34 Strong, 20 Good, **46 Weak** | 34 of 92 |
| **After the fixes** | **10 Strong** | **66 Strong, 28 Good, 2 Partial, 4 Weak** | **66 of 92** |

- **The output file is correct.** It passes the official validator, is byte-identical across runs, and has 0 honeypots. Every reasoning line's title, years, response rate and open-to-work status matches the raw profile (100 of 100).
- **The plain-language profiles the JD hints at (line 073)** moved from ranks 249–9,958 to ranks 68, 70, 85, 109 and 110; one, at 2,455, has little evidence.
- **The remaining differences** are boundary cases near the bottom of the list (section 4).

**Caveat.** The verdicts are a reading of the JD, not the hidden ground truth. The grading and thresholds are below so they can be challenged. The fixes were chosen from the JD's wording and checked against this review; they were not tuned to maximise it.

---

## 1. Output verification

| Check | Result |
|---|---|
| Official `validate_submission.py` | Submission is valid |
| Rerun, byte for byte | Identical |
| Honeypots in top 100 | 0 (43 in pool) |
| Reasoning facts (title, years, response rate, open to work) match the profile | 100 / 100 |

---

## 2. Method

### 2.1 What the JD asks for

- **Must-haves (lines 033–036):**
  - production embeddings-based retrieval;
  - vector database or hybrid search in production;
  - strong Python;
  - rigorous ranking evaluation (NDCG, MRR, MAP, offline-to-online correlation, A/B).
- **Ideal profile (063–067):**
  - 6–8 years, with 4–5 in applied ML at product companies;
  - has shipped a ranking, search or recommendation system;
  - Noida/Pune or willing to relocate;
  - active on the platform.
- **Disqualifiers (026–028, 045–049):**
  - research-only;
  - recent LangChain-only work;
  - non-coding seniors;
  - title-chasers;
  - consulting-only careers;
  - vision/speech/robotics without NLP/IR;
  - closed-source with no external validation.
- **Logistics (052–053):** office cities; no visa sponsorship; notice ideally 30 days or less.
- **Hackathon note (072–074):**
  - skills-list keyword matching is a trap;
  - plain-language careers count;
  - unavailable candidates should be down-weighted.

### 2.2 Grading the role descriptions

The pool contains only **44 distinct role descriptions**; each was read and graded once against the JD:

| Grade | Meaning | Descriptions (summarised) |
|---|---|---|
| **A** | Shipped embedding/vector or hybrid search, retrieval or recommendation with evaluation | semantic search (sentence-transformers, FAISS); recommender for 10M users; hybrid retrieval and ranking at 50M queries/month; marketplace recommender; end-to-end ranking (BGE, Pinecone, LTR); hybrid semantic search over 35M items; embedding-based search migration |
| **A-plain** | The same work in plain language (JD line 073) | matching-layer overhaul; personalization infrastructure; flagship ranking layer; search and discovery; relevance-infrastructure team lead |
| **B** | Part of the must-haves | learning-to-rank for e-commerce search; discovery-feed ranking; RAG support chatbot; LLM fine-tuning for matching |
| **R-light** | Light recommendation features, deployed by another team | "lighter weight than ranking systems at FAANG …" |
| **C** | Applied ML outside search and ranking | fraud-model serving; forecasting; churn/LTV; sentiment classification; MLOps for a churn model |
| **CV** | Vision-focused | image moderation, "interested in transitioning toward NLP" |
| **D** | Not ML | data engineering, backend, frontend, DevOps, QA, sales, marketing and so on |

### 2.3 Verdict rules

- **Strong:** all of the following:
  - at least 12 months in A or A-plain roles;
  - at least 36 months in A, A-plain or B roles;
  - 4–10 years of experience;
  - based in India;
  - no hard disqualifier;
  - available (active within 180 days, response rate 0.10 or more).
- **Good:** at least 24 months in A, A-plain or B roles, no hard disqualifier, available.
- **Partial:** 12–23 months in those roles.
- **Weak:** everything else.

---

## 3. What was wrong and what changed

| Step | Problem found by the review | Fix | Top 10 | Top 100 (Strong / Good / Partial / Weak) |
|---|---|---|---|---|
| Start | — | — | 8 / 1 / 0 / 1 | 34 / 20 / 0 / 46 |
| 1 | "lighter weight **than** ranking systems", "transitioning **toward** NLP" counted as evidence (42 and 27 of the 46 weak entries) | ignore matches after a negation or comparison cue in the same clause | 8 / 1 / 0 / 1 | 49 / 28 / 1 / 22 |
| 2 | Core credit from assessed skills with no work behind them (25 of the 46) | an assessed skill needs career support for full credit | 9 / 1 / 0 / 0 | 59 / 30 / 2 / 9 |
| 3 | `langchain_only` hit 12 candidates, all with production retrieval work | exempt candidates with retrieval/ranking career evidence | 9 / 1 / 0 / 0 | 59 / 31 / 2 / 8 |
| 4 | Plain-language profiles had only half credit | plain-language phrases for the JD's core concepts | 9 / 1 / 0 / 0 | 61 / 35 / 1 / 3 |
| 5 | 8 of the top 10 clamped to the same capability score | divide by the maximum instead of clamping | 9 / 1 / 0 / 0 | 61 / 35 / 1 / 3 |
| 6 | Unavailable candidates (JD line 074) and candidates abroad (no visa sponsorship) barely penalised | unavailable gets the floor multiplier; outside the home country × 0.8 | **10 / 0 / 0 / 0** | **66 / 28 / 2 / 4** |

---

## 4. What still differs

**Six non-matches in the top 100, all at ranks 58–97:**
- **Two "Partial" profiles** with solid ranking and RAG work but several short completed stints. This review treats that as job-hopping; WorkLens applies the smaller title-chasing penalty.
- **Three "Weak" profiles** with broad production ML (feature store, NLP pipelines, gradient-boosted re-ranking) but no retrieval or embedding role. WorkLens weights the must-have areas; it does not require them.
- **One "Weak" profile** credited for retrieval through the job title "Recommendation Systems Engineer" while the description is MLOps work.

**26 Strong matches below the cut (section 6).** Most have role descriptions that do not state production deployment or evaluation (for example the internal-knowledge-base semantic search role), or slightly lower availability. The JD's must-have says "deployed to real users", so WorkLens scoring them a little lower is defensible on the text. Going further would mean tuning the scorer to this review, which this review deliberately avoids.

---

## 5. Every ranked candidate

Career evidence lists each role's graded description and its duration in months.

| Rank | Candidate | Title, yrs | Score | JD verdict | Career evidence (months) | Concerns | Assessment |
|---|---|---|---|---|---|---|---|
| 1 | CAND_0081846 | Lead AI Engineer, 6.7 | 0.857971 | **Strong** | hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (27m); hybrid semantic search, 35M items (NDCG, drift) (52m) | none | Shipped search/ranking/embedding systems for 79 months; fits the JD's must-haves. |
| 2 | CAND_0077337 | Staff Machine Learning Engineer, 7 | 0.841257 | **Strong** | marketplace recommender (embeddings, A/B) (19m); hybrid semantic search, 35M items (NDCG, drift) (14m); embedding-based search migration (A/B) (44m); embedding-based search migration (A/B) (6m) | notice 60d | Shipped search/ranking/embedding systems for 83 months; fits the JD's must-haves. |
| 3 | CAND_0008425 | Senior NLP Engineer, 7.8 | 0.812762 | **Strong** | hybrid semantic search, 35M items (NDCG, drift) (25m); LLM fine-tuning for candidate-JD matching (46m); end-to-end ranking: BGE, Pinecone, LTR, eval (21m) | notice 90d, location: india | Shipped search/ranking/embedding systems for 46 months; fits the JD's must-haves. |
| 4 | CAND_0046525 | Senior Machine Learning Engineer, 6.1 | 0.784965 | **Strong** | embedding-based search migration (A/B) (48m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (25m) | notice 60d | Shipped search/ranking/embedding systems for 73 months; fits the JD's must-haves. |
| 5 | CAND_0080766 | Staff Machine Learning Engineer, 8.8 | 0.773297 | **Strong** | personalization infra, A/B (plain-language) (38m); search and discovery, offline-online eval (plain-language) (12m); flagship ranking layer (plain-language) (43m); hybrid semantic search, 35M items (NDCG, drift) (12m) | none | Shipped search/ranking/embedding systems for 105 months; fits the JD's must-haves. |
| 6 | CAND_0079387 | AI Engineer, 6.9 | 0.769949 | **Strong** | recommender for 10M users (embeddings, A/B) (22m); RAG support chatbot (Pinecone) (22m); MLOps pipelines (churn model) (18m); semantic search (sentence-transformers, FAISS) (19m) | location: india | Shipped search/ranking/embedding systems for 41 months; fits the JD's must-haves. |
| 7 | CAND_0046064 | Senior NLP Engineer, 8.9 | 0.769628 | **Strong** | LLM fine-tuning for candidate-JD matching (36m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (34m); end-to-end ranking: BGE, Pinecone, LTR, eval (36m) | location: india | Shipped search/ranking/embedding systems for 70 months; fits the JD's must-haves. |
| 8 | CAND_0005260 | Senior NLP Engineer, 5.2 | 0.769376 | **Strong** | LLM fine-tuning for candidate-JD matching (34m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (27m) | no external validation (no GitHub), notice 60d | Shipped search/ranking/embedding systems for 27 months; fits the JD's must-haves. |
| 9 | CAND_0030031 | AI Engineer, 5.7 | 0.762047 | **Strong** | recommender for 10M users (embeddings, A/B) (13m); MLOps pipelines (churn model) (27m); discovery-feed ranking models (offline-online correlation) (27m) | location: india | Shipped search/ranking/embedding systems for 13 months; fits the JD's must-haves. |
| 10 | CAND_0002025 | Senior AI Engineer, 5.9 | 0.747498 | **Strong** | marketplace recommender (embeddings, A/B) (42m); LLM fine-tuning for candidate-JD matching (28m) | location: india | Shipped search/ranking/embedding systems for 42 months; fits the JD's must-haves. |
| 11 | CAND_0041610 | Recommendation Systems Engineer, 6.7 | 0.739832 | **Good** | learning-to-rank for e-commerce search (31m); MLOps pipelines (churn model) (26m); RAG support chatbot (Pinecone) (15m); learning-to-rank for e-commerce search (7m) | none | Relevant work (53 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 12 | CAND_0039754 | Senior Applied Scientist, 16.2 | 0.739793 | **Good** | end-to-end ranking: BGE, Pinecone, LTR, eval (37m); hybrid semantic search, 35M items (NDCG, drift) (40m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (21m) | 16.2 yrs outside 5-9 | Relevant work (98 months of search/ranking); not Strong because: 16.2 years of experience. |
| 13 | CAND_0018499 | Senior Machine Learning Engineer, 7.2 | 0.729026 | **Strong** | hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (26m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (18m); LLM fine-tuning for candidate-JD matching (42m) | none | Shipped search/ranking/embedding systems for 44 months; fits the JD's must-haves. |
| 14 | CAND_0005538 | Senior AI Engineer, 5.9 | 0.721234 | **Strong** | relevance infra team lead (plain-language) (15m); matching-layer overhaul (plain-language) (30m); matching-layer overhaul (plain-language) (14m); marketplace recommender (embeddings, A/B) (10m) | notice 90d, location: india | Shipped search/ranking/embedding systems for 69 months; fits the JD's must-haves. |
| 15 | CAND_0071974 | Senior AI Engineer, 7.8 | 0.720932 | **Strong** | end-to-end ranking: BGE, Pinecone, LTR, eval (50m); LLM fine-tuning for candidate-JD matching (28m); marketplace recommender (embeddings, A/B) (14m) | notice 45d, location: india | Shipped search/ranking/embedding systems for 64 months; fits the JD's must-haves. |
| 16 | CAND_0041669 | Recommendation Systems Engineer, 8 | 0.719452 | **Good** | learning-to-rank for e-commerce search (37m); RAG support chatbot (Pinecone) (52m); recommender for 10M users (embeddings, A/B) (6m) | notice 60d | Relevant work (95 months of search/ranking); not Strong because: only 6 months of embedding-based search/ranking. |
| 17 | CAND_0006557 | NLP Engineer, 7.9 | 0.714327 | **Strong** | learning-to-rank for e-commerce search (54m); recommender for 10M users (embeddings, A/B) (40m) | no external validation (no GitHub), notice 120d | Shipped search/ranking/embedding systems for 40 months; fits the JD's must-haves. |
| 18 | CAND_0098846 | AI Engineer, 7.6 | 0.713355 | **Good** | learning-to-rank for e-commerce search (25m); MLOps pipelines (churn model) (20m); RAG support chatbot (Pinecone) (19m); MLOps pipelines (churn model) (26m) | notice 45d | Relevant work (44 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 19 | CAND_0074735 | Applied ML Engineer, 5.5 | 0.709241 | **Good** | RAG support chatbot (Pinecone) (24m); RAG support chatbot (Pinecone) (19m); MLOps pipelines (churn model) (22m) | notice 90d, location: india | Relevant work (43 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 20 | CAND_0077285 | Recommendation Systems Engineer, 5.5 | 0.708082 | **Good** | discovery-feed ranking models (offline-online correlation) (42m); MLOps pipelines (churn model) (15m); RAG support chatbot (Pinecone) (8m) | notice 60d, location: india | Relevant work (50 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 21 | CAND_0081053 | NLP Engineer, 5.4 | 0.708016 | **Strong** | MLOps pipelines (churn model) (22m); recommender for 10M users (embeddings, A/B) (42m) | notice 90d | Shipped search/ranking/embedding systems for 42 months; fits the JD's must-haves. |
| 22 | CAND_0027691 | NLP Engineer, 6.5 | 0.705504 | **Strong** | MLOps pipelines (churn model) (27m); semantic search (sentence-transformers, FAISS) (33m); learning-to-rank for e-commerce search (16m) | none | Shipped search/ranking/embedding systems for 33 months; fits the JD's must-haves. |
| 23 | CAND_0017960 | Recommendation Systems Engineer, 7.7 | 0.703703 | **Good** | discovery-feed ranking models (offline-online correlation) (54m); discovery-feed ranking models (offline-online correlation) (21m); RAG support chatbot (Pinecone) (16m) | notice 60d | Relevant work (91 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 24 | CAND_0005649 | Senior Data Scientist, 7.4 | 0.703619 | **Strong** | semantic search (sentence-transformers, FAISS) (18m); RAG support chatbot (Pinecone) (12m); MLOps pipelines (churn model) (42m); discovery-feed ranking models (offline-online correlation) (16m) | notice 90d | Shipped search/ranking/embedding systems for 18 months; fits the JD's must-haves. |
| 25 | CAND_0068811 | Applied ML Engineer, 8 | 0.700603 | **Strong** | recommender for 10M users (embeddings, A/B) (19m); RAG support chatbot (Pinecone) (26m); learning-to-rank for e-commerce search (25m); MLOps pipelines (churn model) (25m) | none | Shipped search/ranking/embedding systems for 19 months; fits the JD's must-haves. |
| 26 | CAND_0010685 | NLP Engineer, 6.7 | 0.697914 | **Strong** | learning-to-rank for e-commerce search (18m); MLOps pipelines (churn model) (28m); semantic search (sentence-transformers, FAISS) (12m); discovery-feed ranking models (offline-online correlation) (21m) | no external validation (no GitHub), location: india | Shipped search/ranking/embedding systems for 12 months; fits the JD's must-haves. |
| 27 | CAND_0075574 | Machine Learning Engineer, 5.7 | 0.697380 | **Good** | learning-to-rank for e-commerce search (24m); discovery-feed ranking models (offline-online correlation) (36m); RAG support chatbot (Pinecone) (8m) | notice 60d | Relevant work (68 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 28 | CAND_0064326 | Search Engineer, 7.6 | 0.693467 | **Good** | learning-to-rank for e-commerce search (31m); discovery-feed ranking models (offline-online correlation) (24m); RAG support chatbot (Pinecone) (24m); learning-to-rank for e-commerce search (12m) | notice 45d | Relevant work (91 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 29 | CAND_0010257 | Senior Data Scientist, 6.5 | 0.689893 | **Strong** | MLOps pipelines (churn model) (37m); discovery-feed ranking models (offline-online correlation) (14m); recommender for 10M users (embeddings, A/B) (26m) | notice 120d | Shipped search/ranking/embedding systems for 26 months; fits the JD's must-haves. |
| 30 | CAND_0028793 | Search Engineer, 7.2 | 0.687672 | **Strong** | semantic search (sentence-transformers, FAISS) (32m); RAG support chatbot (Pinecone) (40m); discovery-feed ranking models (offline-online correlation) (13m) | notice 120d | Shipped search/ranking/embedding systems for 32 months; fits the JD's must-haves. |
| 31 | CAND_0086022 | Senior Applied Scientist, 5.3 | 0.687622 | **Strong** | hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (25m); embedding-based search migration (A/B) (38m) | none | Shipped search/ranking/embedding systems for 63 months; fits the JD's must-haves. |
| 32 | CAND_0057563 | NLP Engineer, 6.8 | 0.685788 | **Strong** | learning-to-rank for e-commerce search (20m); recommender for 10M users (embeddings, A/B) (34m); semantic search (sentence-transformers, FAISS) (26m) | notice 60d | Shipped search/ranking/embedding systems for 60 months; fits the JD's must-haves. |
| 33 | CAND_0052328 | Recommendation Systems Engineer, 6.5 | 0.683909 | **Good** | RAG support chatbot (Pinecone) (52m); MLOps pipelines (churn model) (25m) | none | Relevant work (52 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 34 | CAND_0033861 | Senior NLP Engineer, 8 | 0.681543 | **Strong** | LLM fine-tuning for candidate-JD matching (30m); hybrid semantic search, 35M items (NDCG, drift) (39m); marketplace recommender (embeddings, A/B) (26m) | availability risk, location: india | Shipped search/ranking/embedding systems for 65 months; fits the JD's must-haves. |
| 35 | CAND_0042029 | Senior Data Scientist, 6.5 | 0.679819 | **Good** | discovery-feed ranking models (offline-online correlation) (36m); RAG support chatbot (Pinecone) (42m) | notice 45d | Relevant work (78 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 36 | CAND_0011432 | Senior Data Scientist, 7.6 | 0.678898 | **Good** | discovery-feed ranking models (offline-online correlation) (28m); RAG support chatbot (Pinecone) (36m); discovery-feed ranking models (offline-online correlation) (26m) | notice 60d, location: india | Relevant work (90 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 37 | CAND_0065195 | Search Engineer, 5.1 | 0.678305 | **Good** | RAG support chatbot (Pinecone) (48m); MLOps pipelines (churn model) (13m) | notice 45d, location: india | Relevant work (48 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 38 | CAND_0052682 | NLP Engineer, 6.6 | 0.676471 | **Strong** | recommender for 10M users (embeddings, A/B) (46m); RAG support chatbot (Pinecone) (32m) | location: india | Shipped search/ranking/embedding systems for 46 months; fits the JD's must-haves. |
| 39 | CAND_0009691 | Applied ML Engineer, 6.2 | 0.675598 | **Strong** | recommender for 10M users (embeddings, A/B) (28m); recommender for 10M users (embeddings, A/B) (15m); recommender for 10M users (embeddings, A/B) (30m) | notice 120d | Shipped search/ranking/embedding systems for 73 months; fits the JD's must-haves. |
| 40 | CAND_0031593 | Search Engineer, 7.8 | 0.674602 | **Strong** | learning-to-rank for e-commerce search (38m); RAG support chatbot (Pinecone) (21m); recommender for 10M users (embeddings, A/B) (33m) | notice 90d | Shipped search/ranking/embedding systems for 33 months; fits the JD's must-haves. |
| 41 | CAND_0011687 | Senior NLP Engineer, 7.8 | 0.673285 | **Strong** | end-to-end ranking: BGE, Pinecone, LTR, eval (52m); LLM fine-tuning for candidate-JD matching (40m) | location: india | Shipped search/ranking/embedding systems for 52 months; fits the JD's must-haves. |
| 42 | CAND_0070202 | Machine Learning Engineer, 5.1 | 0.672564 | **Strong** | learning-to-rank for e-commerce search (49m); recommender for 10M users (embeddings, A/B) (12m) | no external validation (no GitHub), notice 90d, location: india | Shipped search/ranking/embedding systems for 12 months; fits the JD's must-haves. |
| 43 | CAND_0096142 | Applied ML Engineer, 5 | 0.672435 | **Strong** | discovery-feed ranking models (offline-online correlation) (42m); recommender for 10M users (embeddings, A/B) (18m) | notice 120d | Shipped search/ranking/embedding systems for 18 months; fits the JD's must-haves. |
| 44 | CAND_0083307 | Search Engineer, 7.8 | 0.671276 | **Strong** | RAG support chatbot (Pinecone) (20m); learning-to-rank for e-commerce search (51m); semantic search (sentence-transformers, FAISS) (14m); learning-to-rank for e-commerce search (7m) | notice 120d, location: india | Shipped search/ranking/embedding systems for 14 months; fits the JD's must-haves. |
| 45 | CAND_0099401 | NLP Engineer, 7.7 | 0.669427 | **Strong** | recommender for 10M users (embeddings, A/B) (14m); MLOps pipelines (churn model) (33m); learning-to-rank for e-commerce search (27m); MLOps pipelines (churn model) (16m) | notice 90d | Shipped search/ranking/embedding systems for 14 months; fits the JD's must-haves. |
| 46 | CAND_0091909 | Machine Learning Engineer, 6.9 | 0.663923 | **Strong** | recommender for 10M users (embeddings, A/B) (51m); discovery-feed ranking models (offline-online correlation) (31m) | notice 45d | Shipped search/ranking/embedding systems for 51 months; fits the JD's must-haves. |
| 47 | CAND_0018549 | Recommendation Systems Engineer, 6.8 | 0.662675 | **Strong** | learning-to-rank for e-commerce search (37m); recommender for 10M users (embeddings, A/B) (44m) | notice 60d | Shipped search/ranking/embedding systems for 44 months; fits the JD's must-haves. |
| 48 | CAND_0011162 | Recommendation Systems Engineer, 5.8 | 0.661955 | **Good** | discovery-feed ranking models (offline-online correlation) (25m); MLOps pipelines (churn model) (28m); learning-to-rank for e-commerce search (15m) | notice 90d | Relevant work (40 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 49 | CAND_0078002 | Machine Learning Engineer, 6.3 | 0.660156 | **Strong** | discovery-feed ranking models (offline-online correlation) (34m); recommender for 10M users (embeddings, A/B) (30m); discovery-feed ranking models (offline-online correlation) (10m) | notice 60d, location: india | Shipped search/ranking/embedding systems for 30 months; fits the JD's must-haves. |
| 50 | CAND_0065878 | Senior Data Scientist, 7.8 | 0.652676 | **Strong** | learning-to-rank for e-commerce search (24m); recommender for 10M users (embeddings, A/B) (20m); learning-to-rank for e-commerce search (33m); learning-to-rank for e-commerce search (15m) | no external validation (no GitHub), location: india | Shipped search/ranking/embedding systems for 20 months; fits the JD's must-haves. |
| 51 | CAND_0061265 | Recommendation Systems Engineer, 6.6 | 0.652128 | **Strong** | semantic search (sentence-transformers, FAISS) (20m); MLOps pipelines (churn model) (36m); learning-to-rank for e-commerce search (22m) | notice 120d | Shipped search/ranking/embedding systems for 20 months; fits the JD's must-haves. |
| 52 | CAND_0014440 | Recommendation Systems Engineer, 6.4 | 0.651887 | **Good** | learning-to-rank for e-commerce search (31m); learning-to-rank for e-commerce search (31m); MLOps pipelines (churn model) (14m) | notice 60d, location: india | Relevant work (62 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 53 | CAND_0050876 | Applied ML Engineer, 6 | 0.650294 | **Strong** | learning-to-rank for e-commerce search (38m); recommender for 10M users (embeddings, A/B) (24m); recommender for 10M users (embeddings, A/B) (9m) | notice 90d, location: india | Shipped search/ranking/embedding systems for 33 months; fits the JD's must-haves. |
| 54 | CAND_0055905 | Senior Machine Learning Engineer, 8.1 | 0.649833 | **Good** | hybrid semantic search, 35M items (NDCG, drift) (14m); LLM fine-tuning for candidate-JD matching (37m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (45m) | no external validation (no GitHub), location: abroad | Relevant work (96 months of search/ranking); not Strong because: based outside India (no visa sponsorship). |
| 55 | CAND_0095528 | Senior Data Scientist, 5.3 | 0.642375 | **Good** | recommender for 10M users (embeddings, A/B) (33m); MLOps pipelines (churn model) (30m) | no external validation (no GitHub), notice 45d, location: india | Relevant work (33 months of search/ranking); not Strong because: 33 months of search/ranking work (under 3 years). |
| 56 | CAND_0066376 | Applied ML Engineer, 5.7 | 0.638920 | **Strong** | recommender for 10M users (embeddings, A/B) (45m); semantic search (sentence-transformers, FAISS) (22m) | no external validation (no GitHub), notice 90d | Shipped search/ranking/embedding systems for 67 months; fits the JD's must-haves. |
| 57 | CAND_0094759 | Lead AI Engineer, 8.6 | 0.635323 | **Strong** | embedding-based search migration (A/B) (32m); hybrid retrieval + ranking, 50M queries/month (NDCG, MRR) (28m); embedding-based search migration (A/B) (41m) | availability risk | Shipped search/ranking/embedding systems for 101 months; fits the JD's must-haves. |
| 58 | CAND_0039838 | Recommendation Systems Engineer, 4.9 | 0.634532 | **Weak** | MLOps pipelines (churn model) (49m); discovery-feed ranking models (offline-online correlation) (9m) | notice 90d, location: india, 4.9 yrs outside 5-9 | No search, ranking or embedding role; scored on broad ML evidence (Retrieval & Search, Ranking & Recommendation / LTR, Evaluation & Experimentation, ML Production & Deployment (MLOps), NLP / IR foundations). |
| 59 | CAND_0070398 | Machine Learning Engineer, 7.2 | 0.632844 | **Strong** | semantic search (sentence-transformers, FAISS) (37m); semantic search (sentence-transformers, FAISS) (22m); discovery-feed ranking models (offline-online correlation) (26m) | notice 120d | Shipped search/ranking/embedding systems for 59 months; fits the JD's must-haves. |
| 60 | CAND_0027801 | NLP Engineer, 7.4 | 0.630861 | **Strong** | MLOps pipelines (churn model) (34m); semantic search (sentence-transformers, FAISS) (22m); semantic search (sentence-transformers, FAISS) (31m) | notice 120d | Shipped search/ranking/embedding systems for 53 months; fits the JD's must-haves. |
| 61 | CAND_0051292 | Applied ML Engineer, 5.2 | 0.630318 | **Strong** | learning-to-rank for e-commerce search (16m); semantic search (sentence-transformers, FAISS) (28m); RAG support chatbot (Pinecone) (16m) | location: india | Shipped search/ranking/embedding systems for 28 months; fits the JD's must-haves. |
| 62 | CAND_0044855 | Senior Data Scientist, 6.6 | 0.627837 | **Strong** | RAG support chatbot (Pinecone) (31m); recommender for 10M users (embeddings, A/B) (22m); semantic search (sentence-transformers, FAISS) (25m) | notice 60d | Shipped search/ranking/embedding systems for 47 months; fits the JD's must-haves. |
| 63 | CAND_0007412 | Applied ML Engineer, 7.4 | 0.624912 | **Partial** | RAG support chatbot (Pinecone) (33m); discovery-feed ranking models (offline-online correlation) (19m); RAG support chatbot (Pinecone) (14m); RAG support chatbot (Pinecone) (13m); learning-to-rank for e-commerce search (8m) | job-hopping (3+ completed stints <18m), notice 120d | Some ranking or retrieval exposure, but too little to meet the must-haves. |
| 64 | CAND_0094056 | NLP Engineer, 5.9 | 0.620011 | **Strong** | semantic search (sentence-transformers, FAISS) (36m); MLOps pipelines (churn model) (34m) | notice 120d | Shipped search/ranking/embedding systems for 36 months; fits the JD's must-haves. |
| 65 | CAND_0069905 | Applied ML Engineer, 6.6 | 0.619662 | **Strong** | semantic search (sentence-transformers, FAISS) (26m); RAG support chatbot (Pinecone) (13m); semantic search (sentence-transformers, FAISS) (39m) | notice 90d | Shipped search/ranking/embedding systems for 65 months; fits the JD's must-haves. |
| 66 | CAND_0039383 | Applied ML Engineer, 7.1 | 0.618105 | **Strong** | discovery-feed ranking models (offline-online correlation) (34m); semantic search (sentence-transformers, FAISS) (13m); discovery-feed ranking models (offline-online correlation) (37m) | notice 90d | Shipped search/ranking/embedding systems for 13 months; fits the JD's must-haves. |
| 67 | CAND_0075439 | Machine Learning Engineer, 4.3 | 0.617687 | **Strong** | RAG support chatbot (Pinecone) (26m); recommender for 10M users (embeddings, A/B) (25m) | location: india, 4.3 yrs outside 5-9 | Shipped search/ranking/embedding systems for 25 months; fits the JD's must-haves. |
| 68 | CAND_0030468 | Senior Applied Scientist, 5.4 | 0.617330 | **Strong** | relevance infra team lead (plain-language) (14m); personalization infra, A/B (plain-language) (18m); personalization infra, A/B (plain-language) (32m) | notice 45d | Shipped search/ranking/embedding systems for 64 months; fits the JD's must-haves. |
| 69 | CAND_0012957 | Search Engineer, 4.9 | 0.617081 | **Strong** | learning-to-rank for e-commerce search (18m); recommender for 10M users (embeddings, A/B) (40m) | notice 120d, 4.9 yrs outside 5-9 | Shipped search/ranking/embedding systems for 40 months; fits the JD's must-haves. |
| 70 | CAND_0068351 | Lead AI Engineer, 6.4 | 0.616471 | **Strong** | search and discovery, offline-online eval (plain-language) (25m); matching-layer overhaul (plain-language) (45m); flagship ranking layer (plain-language) (6m) | no external validation (no GitHub) | Shipped search/ranking/embedding systems for 76 months; fits the JD's must-haves. |
| 71 | CAND_0064904 | AI Engineer, 4.9 | 0.615840 | **Good** | MLOps pipelines (churn model) (27m); recommender for 10M users (embeddings, A/B) (31m) | notice 90d, 4.9 yrs outside 5-9 | Relevant work (31 months of search/ranking); not Strong because: 31 months of search/ranking work (under 3 years). |
| 72 | CAND_0040117 | Recommendation Systems Engineer, 6.5 | 0.614698 | **Strong** | recommender for 10M users (embeddings, A/B) (51m); RAG support chatbot (Pinecone) (26m) | no external validation (no GitHub), location: india | Shipped search/ranking/embedding systems for 51 months; fits the JD's must-haves. |
| 73 | CAND_0049538 | Applied ML Engineer, 5.8 | 0.613879 | **Good** | learning-to-rank for e-commerce search (40m); MLOps pipelines (churn model) (19m); MLOps pipelines (churn model) (9m) | location: india | Relevant work (40 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 74 | CAND_0074225 | Machine Learning Engineer, 4.3 | 0.612371 | **Good** | discovery-feed ranking models (offline-online correlation) (26m); RAG support chatbot (Pinecone) (25m) | notice 120d, 4.3 yrs outside 5-9 | Relevant work (51 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 75 | CAND_0047721 | Senior Data Scientist, 7 | 0.610779 | **Strong** | recommender for 10M users (embeddings, A/B) (48m); learning-to-rank for e-commerce search (36m) | notice 90d | Shipped search/ranking/embedding systems for 48 months; fits the JD's must-haves. |
| 76 | CAND_0015528 | Applied ML Engineer, 7.4 | 0.609084 | **Strong** | recommender for 10M users (embeddings, A/B) (52m); MLOps pipelines (churn model) (20m); recommender for 10M users (embeddings, A/B) (15m) | location: india | Shipped search/ranking/embedding systems for 67 months; fits the JD's must-haves. |
| 77 | CAND_0086151 | Recommendation Systems Engineer, 7.7 | 0.605485 | **Strong** | learning-to-rank for e-commerce search (26m); recommender for 10M users (embeddings, A/B) (28m); semantic search (sentence-transformers, FAISS) (37m) | notice 120d | Shipped search/ranking/embedding systems for 65 months; fits the JD's must-haves. |
| 78 | CAND_0096172 | NLP Engineer, 5.2 | 0.599636 | **Strong** | semantic search (sentence-transformers, FAISS) (40m); recommender for 10M users (embeddings, A/B) (21m) | notice 45d, location: india | Shipped search/ranking/embedding systems for 61 months; fits the JD's must-haves. |
| 79 | CAND_0084819 | Search Engineer, 4.5 | 0.599455 | **Good** | RAG support chatbot (Pinecone) (33m); learning-to-rank for e-commerce search (20m) | notice 120d, location: india, 4.5 yrs outside 5-9 | Relevant work (53 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 80 | CAND_0079064 | Senior Data Scientist, 5.2 | 0.598157 | **Strong** | semantic search (sentence-transformers, FAISS) (44m); RAG support chatbot (Pinecone) (18m) | notice 120d | Shipped search/ranking/embedding systems for 44 months; fits the JD's must-haves. |
| 81 | CAND_0062247 | AI Engineer, 7.3 | 0.597996 | **Strong** | semantic search (sentence-transformers, FAISS) (37m); learning-to-rank for e-commerce search (50m) | none | Shipped search/ranking/embedding systems for 37 months; fits the JD's must-haves. |
| 82 | CAND_0091534 | AI Engineer, 16.6 | 0.597059 | **Good** | learning-to-rank for e-commerce search (52m); semantic search (sentence-transformers, FAISS) (13m); RAG support chatbot (Pinecone) (20m) | 16.6 yrs outside 5-9 | Relevant work (85 months of search/ranking); not Strong because: 16.6 years of experience. |
| 83 | CAND_0053695 | Recommendation Systems Engineer, 5.8 | 0.596507 | **Strong** | discovery-feed ranking models (offline-online correlation) (20m); learning-to-rank for e-commerce search (34m); semantic search (sentence-transformers, FAISS) (14m) | location: india | Shipped search/ranking/embedding systems for 14 months; fits the JD's must-haves. |
| 84 | CAND_0000031 | Recommendation Systems Engineer, 6 | 0.596484 | **Good** | discovery-feed ranking models (offline-online correlation) (14m); discovery-feed ranking models (offline-online correlation) (16m); discovery-feed ranking models (offline-online correlation) (27m); learning-to-rank for e-commerce search (13m) | notice 60d | Relevant work (70 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 85 | CAND_0037980 | Senior Applied Scientist, 9 | 0.596152 | **Strong** | flagship ranking layer (plain-language) (38m); flagship ranking layer (plain-language) (38m); personalization infra, A/B (plain-language) (31m) | none | Shipped search/ranking/embedding systems for 107 months; fits the JD's must-haves. |
| 86 | CAND_0061655 | Machine Learning Engineer, 4.6 | 0.595537 | **Good** | learning-to-rank for e-commerce search (43m); recommender for 10M users (embeddings, A/B) (11m) | location: india, 4.6 yrs outside 5-9 | Relevant work (54 months of search/ranking); not Strong because: only 11 months of embedding-based search/ranking. |
| 87 | CAND_0036863 | Senior Data Scientist, 4.3 | 0.594978 | **Good** | learning-to-rank for e-commerce search (12m); learning-to-rank for e-commerce search (33m); RAG support chatbot (Pinecone) (6m) | notice 60d, 4.3 yrs outside 5-9 | Relevant work (51 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 88 | CAND_0073883 | AI Specialist, 5.3 | 0.593039 | **Weak** | demand forecasting (13m); fraud-model serving API (26m); light recommendation features (deployed by platform team) (23m) | notice 90d | No search, ranking or embedding role; scored on broad ML evidence (Ranking & Recommendation / LTR, ML Production & Deployment (MLOps), Data & Feature pipelines). |
| 89 | CAND_0075249 | Applied ML Engineer, 6.2 | 0.592946 | **Strong** | recommender for 10M users (embeddings, A/B) (36m); semantic search (sentence-transformers, FAISS) (38m) | notice 45d, location: india | Shipped search/ranking/embedding systems for 74 months; fits the JD's must-haves. |
| 90 | CAND_0044222 | AI Engineer, 7.7 | 0.592304 | **Strong** | semantic search (sentence-transformers, FAISS) (49m); discovery-feed ranking models (offline-online correlation) (43m) | notice 60d, location: india | Shipped search/ranking/embedding systems for 49 months; fits the JD's must-haves. |
| 91 | CAND_0011327 | AI Research Engineer, 6.3 | 0.591615 | **Weak** | fraud-model serving API (44m); light recommendation features (deployed by platform team) (14m); sentiment classification (16m) | no external validation (no GitHub), notice 60d | No search, ranking or embedding role; scored on broad ML evidence (Ranking & Recommendation / LTR, ML Production & Deployment (MLOps), NLP / IR foundations, LLM & Fine-tuning, Data & Feature pipelines). |
| 92 | CAND_0067866 | Senior Software Engineer (ML), 6.4 | 0.591191 | **Weak** | light recommendation features (deployed by platform team) (38m); fraud-model serving API (19m); sentiment classification (19m) | notice 45d | No search, ranking or embedding role; scored on broad ML evidence (Ranking & Recommendation / LTR, ML Production & Deployment (MLOps), NLP / IR foundations, LLM & Fine-tuning, Data & Feature pipelines). |
| 93 | CAND_0054394 | Recommendation Systems Engineer, 4.1 | 0.590919 | **Strong** | semantic search (sentence-transformers, FAISS) (14m); learning-to-rank for e-commerce search (34m) | 4.1 yrs outside 5-9 | Shipped search/ranking/embedding systems for 14 months; fits the JD's must-haves. |
| 94 | CAND_0060054 | AI Engineer, 6.4 | 0.590691 | **Strong** | semantic search (sentence-transformers, FAISS) (31m); recommender for 10M users (embeddings, A/B) (24m); discovery-feed ranking models (offline-online correlation) (21m) | no external validation (no GitHub) | Shipped search/ranking/embedding systems for 55 months; fits the JD's must-haves. |
| 95 | CAND_0061339 | Search Engineer, 4.2 | 0.590546 | **Strong** | recommender for 10M users (embeddings, A/B) (28m); discovery-feed ranking models (offline-online correlation) (13m); discovery-feed ranking models (offline-online correlation) (8m) | notice 90d, 4.2 yrs outside 5-9 | Shipped search/ranking/embedding systems for 28 months; fits the JD's must-haves. |
| 96 | CAND_0043228 | Applied ML Engineer, 6.8 | 0.590448 | **Good** | learning-to-rank for e-commerce search (25m); MLOps pipelines (churn model) (44m); semantic search (sentence-transformers, FAISS) (11m) | location: india | Relevant work (36 months of search/ranking); not Strong because: only 11 months of embedding-based search/ranking. |
| 97 | CAND_0030953 | Search Engineer, 7.8 | 0.588569 | **Partial** | discovery-feed ranking models (offline-online correlation) (30m); recommender for 10M users (embeddings, A/B) (16m); semantic search (sentence-transformers, FAISS) (24m); discovery-feed ranking models (offline-online correlation) (15m); RAG support chatbot (Pinecone) (7m) | job-hopping (3+ completed stints <18m), notice 45d, location: india | Some ranking or retrieval exposure, but too little to meet the must-haves. |
| 98 | CAND_0083879 | Machine Learning Engineer, 7.1 | 0.587062 | **Good** | MLOps pipelines (churn model) (19m); discovery-feed ranking models (offline-online correlation) (46m); discovery-feed ranking models (offline-online correlation) (19m) | no external validation (no GitHub) | Relevant work (65 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |
| 99 | CAND_0058575 | AI Engineer, 5.8 | 0.585405 | **Strong** | semantic search (sentence-transformers, FAISS) (24m); RAG support chatbot (Pinecone) (15m); MLOps pipelines (churn model) (30m) | notice 90d | Shipped search/ranking/embedding systems for 24 months; fits the JD's must-haves. |
| 100 | CAND_0045250 | Applied ML Engineer, 6.6 | 0.583558 | **Good** | discovery-feed ranking models (offline-online correlation) (46m); MLOps pipelines (churn model) (32m) | no external validation (no GitHub) | Relevant work (46 months of search/ranking); not Strong because: no role combining embedding retrieval with search/ranking. |

---

## 6. Strong matches outside the top 100

The 26 candidates graded Strong that WorkLens ranks below 100, in WorkLens order, with the reason from their scores.

| WorkLens rank | Candidate | Title, yrs | Score | Behaviour multiplier | Why below the cut | Career evidence (months) |
|---|---|---|---|---|---|---|
| 101 | CAND_0049896 | Search Engineer, 7.3 | 0.580353 | 0.890 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial | RAG support chatbot (Pinecone) (45m); recommender for 10M users (embeddings, A/B) (42m) |
| 103 | CAND_0016163 | Applied ML Engineer, 6.7 | 0.579258 | 0.907 | career text: Ranking & Recommendation / LTR missing, Evaluation & Experimentation partial | MLOps pipelines (churn model) (27m); semantic search (sentence-transformers, FAISS) (40m); MLOps pipelines (churn model) (12m) |
| 106 | CAND_0079284 | Machine Learning Engineer, 4.9 | 0.578016 | 0.890 | career text: ML Production & Deployment (MLOps) partial | discovery-feed ranking models (offline-online correlation) (36m); recommender for 10M users (embeddings, A/B) (22m) |
| 107 | CAND_0087630 | AI Engineer, 7.2 | 0.577930 | 0.843 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.84) | recommender for 10M users (embeddings, A/B) (15m); recommender for 10M users (embeddings, A/B) (27m); recommender for 10M users (embeddings, A/B) (43m) |
| 109 | CAND_0006567 | Senior AI Engineer, 7.9 | 0.577374 | 0.952 | career text: Embeddings & Vector missing | matching-layer overhaul (plain-language) (26m); search and discovery, offline-online eval (plain-language) (49m); personalization infra, A/B (plain-language) (19m) |
| 110 | CAND_0061257 | Staff Machine Learning Engineer, 8 | 0.575019 | 0.930 | career text: Embeddings & Vector missing, ML Production & Deployment (MLOps) partial | flagship ranking layer (plain-language) (43m); search and discovery, offline-online eval (plain-language) (52m) |
| 112 | CAND_0009024 | Search Engineer, 5.2 | 0.571196 | 0.876 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.88) | recommender for 10M users (embeddings, A/B) (33m); recommender for 10M users (embeddings, A/B) (28m) |
| 114 | CAND_0007009 | Recommendation Systems Engineer, 7.9 | 0.567620 | 0.871 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.87) | RAG support chatbot (Pinecone) (14m); RAG support chatbot (Pinecone) (48m); semantic search (sentence-transformers, FAISS) (32m) |
| 121 | CAND_0089552 | Machine Learning Engineer, 6 | 0.557160 | 0.855 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.85) | RAG support chatbot (Pinecone) (50m); recommender for 10M users (embeddings, A/B) (21m) |
| 123 | CAND_0050454 | AI Engineer, 6.8 | 0.553466 | 0.926 | career text: Evaluation & Experimentation missing, ML Production & Deployment (MLOps) partial | semantic search (sentence-transformers, FAISS) (30m); learning-to-rank for e-commerce search (20m); semantic search (sentence-transformers, FAISS) (31m) |
| 124 | CAND_0088025 | Staff Machine Learning Engineer, 8.6 | 0.553419 | 0.947 | career text: Retrieval & Search partial, Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial | end-to-end ranking: BGE, Pinecone, LTR, eval (45m); end-to-end ranking: BGE, Pinecone, LTR, eval (44m); embedding-based search migration (A/B) (13m) |
| 127 | CAND_0029367 | Senior Data Scientist, 5.7 | 0.550411 | 0.910 | career text: Ranking & Recommendation / LTR missing, ML Production & Deployment (MLOps) partial | semantic search (sentence-transformers, FAISS) (44m); semantic search (sentence-transformers, FAISS) (15m); RAG support chatbot (Pinecone) (8m) |
| 136 | CAND_0042506 | Search Engineer, 4.2 | 0.539798 | 0.889 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial | RAG support chatbot (Pinecone) (18m); recommender for 10M users (embeddings, A/B) (32m) |
| 140 | CAND_0060072 | Staff Machine Learning Engineer, 5.7 | 0.537489 | 0.747 | career text: ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.75) | marketplace recommender (embeddings, A/B) (37m); marketplace recommender (embeddings, A/B) (31m) |
| 150 | CAND_0020877 | Applied ML Engineer, 5.1 | 0.530971 | 0.878 | career text: Ranking & Recommendation / LTR missing, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.88) | semantic search (sentence-transformers, FAISS) (38m); RAG support chatbot (Pinecone) (22m) |
| 151 | CAND_0054123 | Applied ML Engineer, 4.7 | 0.530691 | 0.901 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial | recommender for 10M users (embeddings, A/B) (45m); semantic search (sentence-transformers, FAISS) (10m) |
| 167 | CAND_0070485 | Search Engineer, 6.4 | 0.518767 | 0.868 | career text: Evaluation & Experimentation missing, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.87) | semantic search (sentence-transformers, FAISS) (26m); learning-to-rank for e-commerce search (50m) |
| 168 | CAND_0026532 | Recommendation Systems Engineer, 4.8 | 0.518667 | 0.880 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial | semantic search (sentence-transformers, FAISS) (34m); recommender for 10M users (embeddings, A/B) (22m) |
| 171 | CAND_0093912 | Senior Data Scientist, 5.3 | 0.512487 | 0.927 | career text: Evaluation & Experimentation missing, ML Production & Deployment (MLOps) partial | learning-to-rank for e-commerce search (27m); semantic search (sentence-transformers, FAISS) (19m); learning-to-rank for e-commerce search (16m) |
| 204 | CAND_0051630 | Machine Learning Engineer, 6 | 0.494710 | 0.827 | career text: Evaluation & Experimentation missing, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.83) | learning-to-rank for e-commerce search (44m); semantic search (sentence-transformers, FAISS) (27m) |
| 208 | CAND_0007411 | Senior Machine Learning Engineer, 8 | 0.493263 | 0.751 | career text: Retrieval & Search partial, Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial; lower availability (multiplier 0.75) | end-to-end ranking: BGE, Pinecone, LTR, eval (38m); LLM fine-tuning for candidate-JD matching (57m) |
| 212 | CAND_0030348 | Machine Learning Engineer, 4.5 | 0.491820 | 0.901 | career text: Ranking & Recommendation / LTR partial, ML Production & Deployment (MLOps) partial | semantic search (sentence-transformers, FAISS) (28m); recommender for 10M users (embeddings, A/B) (25m) |
| 360 | CAND_0036184 | Recommendation Systems Engineer, 6 | 0.434052 | 0.937 | career text: Ranking & Recommendation / LTR partial, Evaluation & Experimentation missing, ML Production & Deployment (MLOps) missing | semantic search (sentence-transformers, FAISS) (52m); semantic search (sentence-transformers, FAISS) (19m) |
| 549 | CAND_0003977 | Recommendation Systems Engineer, 4.6 | 0.396761 | 0.828 | career text: Evaluation & Experimentation missing, ML Production & Deployment (MLOps) missing; lower availability (multiplier 0.83) | semantic search (sentence-transformers, FAISS) (49m); semantic search (sentence-transformers, FAISS) (6m) |
| 708 | CAND_0020708 | Search Engineer, 4.2 | 0.372579 | 0.889 | career text: Ranking & Recommendation / LTR partial, Evaluation & Experimentation missing, ML Production & Deployment (MLOps) missing | semantic search (sentence-transformers, FAISS) (50m) |
| 2455 | CAND_0093193 | Senior Machine Learning Engineer, 7.9 | 0.281189 | 0.907 | career text: Embeddings & Vector partial, Ranking & Recommendation / LTR missing, Evaluation & Experimentation partial, ML Production & Deployment (MLOps) missing | matching-layer overhaul (plain-language) (44m); matching-layer overhaul (plain-language) (50m) |
