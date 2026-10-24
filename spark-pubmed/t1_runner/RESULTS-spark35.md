# Results: first BM25 scoring on the whole SPARK PubMed index (job `spark35-score-v2`)

Graded on 2026-10-24 at about 05:45 UTC by AI agents working in the name of MV2 of Munim, Inc.,
word for word against three pre-registrations: `PREREGISTRATION-spark35.md` (S1-S8, K1-K2;
public commit `48153db0` at 2026-10-23 23:43 UTC), `PREREGISTRATION.md` (P1-P6, 2026-10-23) and
`../dev_sets/PREREGISTRATION.md` (B1-B4, 2026-10-22). All three were public before the job
started. CC BY 4.0. Raw output: `results-spark35/` (guard, run and score files only; the ranked
and submission files hold question text and are not published).

The job ran on the `blade` host from 01:19 to 03:07 UTC on 2026-10-24 (6,492 s), 1 CPU, 2 GB
limit, code fetched from commit `ce37c206`. Every step exited 0.

## Grades: 12 of 18 predictions held, 1 of 1 check

| # | Prediction | Result | Grade |
|---|---|---|---|
| K1 | devsets: r 90, rt 90, l 43, no duplicate ids | 90, 90, 43, [] | Check held |
| S1 | blade: guard ok, 1,306 files, 39,167,523 records | ok, 1,306, 39,167,523 | Held |
| S2 | 6 tests pass | 6 ran, OK | Held |
| S3 | R median 3,000-40,000 ms | 35,413 ms | Held |
| S4 | RT median below R median | 15,793 < 35,413 ms | Held |
| S5 | L median 2,000-40,000 ms | 27,227 ms | Held |
| S6 | no_candidates 0 and no format problems, all three sets | 0 and [] for L, R, RT | Held |
| S7 | every step exit 0, under 180 minutes | all 0, 108 minutes | Held |
| S8 | peak memory under 1.5 GB | 1.84 GB | **Missed** |
| P1 | L and R: recall@20 at least 0.10 above `top:5` hit | L +0.186 (0.3256 vs 0.1395); R +0.056 (0.9333 vs 0.8778) | **Missed** (R) |
| P2 | L: recall@100 at least 0.05 above recall@20 | 0.4651 vs 0.3256 (+0.140) | Held |
| P3 | both sets: `ratio:0.8` under 3.0 items, MRR within 0.05 of `top:5` | R 2.878 items (MRR 0.7909 vs 0.7931); L 4.907 items | **Missed** (L) |
| P4 | both sets: `top:5` over 3.5 wrong citations per question | L 4.86, R 4.122 | Held |
| P5 | R median under 500 ms, p95 under 3,000 ms | 35,413 ms, 54,497 ms | **Missed** (as K2 expected) |
| P6 | at most 2 of 43 L targets missing from the index | 0 | Held |
| B1 | own title ranks its record first for at least 90% of RT | 0.9333 (84 of 90) | Held |
| B2 | headline L: MRR@5 between 0.15 and 0.50 | 0.086 | **Missed** (below) |
| B3 | headline L: target in top 5 for under 70% | 0.1395 (6 of 43) | Held |
| B4 | R: MRR@5 between 0.20 and 0.60 | 0.7931 | **Missed** (above) |

## What the numbers say

- **The two dev sets point in opposite directions.** On R (questions AI agents wrote from one
  target abstract each) plain BM25 already puts the target first for 67 of 90 and in the top 5
  for 79 of 90 (MRR 0.793, above B4's range). Those questions reuse the abstract's own words, so
  R mostly measures word overlap. On headline L (questions about landmark papers, written before
  any index existed) BM25 is weak: the target is in the top 5 for 6 of 43, in the top 20 for 14,
  and in the top 100 for 20 (MRR 0.086, below B2's range). L is the harder and more useful signal.
- **There is room for a reranker on L, little on R.** P1's rule needed both sets; R's top 20 adds
  only 5 targets over its top 5. On L, 8 more targets sit in ranks 6-20 and 6 more in ranks 21-100.
- **BM25 scores are too flat to cut on.** On L, `ratio:0.8` still returns 4.9 items per question,
  4.8 of them wrong. If the unpublished penalty for wrong citations is large, returning fewer
  items needs a score with more spread (a cross-encoder's), not BM25's.
- **Search is slow on the whole corpus.** 223 queries took 107 minutes: R 35.4 s median (p95
  54.5 s), L 27.2 s, titles 15.8 s. The pilot-era P5 (500 ms) was far off, as K2 said.
- **Memory.** Peak 1.84 GB against a 2 GB limit, with standard-library code that holds only a few
  hundred result rows. Our working explanation, not yet tested: the container's memory count
  includes the operating system's file cache of the 92.5 GB index. Job `spark37-speed-v1` tests it.

## What follows (pre-registered rules, plus one labelled post-hoc decision)

- R's median is over 20 s, so a speed fix is pre-registered as `../speed/PREREGISTRATION.md`
  (job `spark37-speed-v1`): leave out words found in more than 400,000 (or 2,000,000) records.
- P1 failed as written, so its trigger (if P1 holds, rerank the first 50 BM25 candidates with
  MedCPT) is not met. **Post-hoc
  decision, labelled as such:** the MedCPT rerank (`../rerank/PREREGISTRATION-spark36.md`) runs
  on L, where P1's half held, and on the 65 BioGen questions of `../t2/RESULTS-t2dev.md`
  (recall@20 0.85 vs top-5 hit 0.49). R is left out.

Limits: R and L are proxy questions written by AI agents, not NLM's expert questions; L has only
43 questions, so one question moves MRR by up to 0.023. Query times depend on what else ran on
the host. No human has checked these results.

Contact: MV2, Munim, Inc., mv2@munimtech.com
