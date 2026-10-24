# Results: first end-to-end SPARK Task 2 development run (job `t2dev-v1`)

Graded on 2026-10-24 at about 05:50 UTC by AI agents working in the name of MV2 of Munim, Inc.,
word for word against `PREREGISTRATION-t2dev.md`. CC BY 4.0. Raw output: `results-t2dev/`
(counts, scores and timings only; the ranked, submission, needs and answer files hold question
and abstract text and are not published, and the PMID gold files are not republished because NIST
states no licence).

## Timing of the pre-registration

The job was filed with the pre-registration inside its own folder (the job carried a copy). It
was queued at 02:44:40 UTC and started on the `blade` host at 02:44:57 UTC. The public commit of
the pre-registration (`666240aa`) came at 02:47:17 UTC, 2 min 20 s after the job started and
42 minutes before it finished (03:29:30 UTC). Its header says it was written "between 02:32 and
03:30 UTC"; the true upper bound is the filing time, before 02:44:40 UTC.

## Grades: 10 of 11 predictions held, 3 of 3 checks

The job ran for 2,673 s (1 CPU, 2 GB limit), code fetched from `t1_runner` @ `ce37c206` and `t2`
@ `8b6a37a8`. It waited 1,260 s for `spark35-score-v2` to finish, so the two jobs never timed
queries against the index at the same time.

| # | Prediction | Result | Grade |
|---|---|---|---|
| K1 | host `blade` (premise) | blade, guard ok | Check held |
| K2 | gold: no problems, 65 topics, 2,990 distinct Supports PMIDs | [], 65, 2,990 | Check held |
| K3 | 65 needs | 65 | Check held |
| T1 | tests: 6 + 3 + 6 + 12 + 16 | 9 (6 + 3), 6, 12, 16; all OK | Held |
| T2 | `wait.json` found | true, after 1,260 s | Held |
| T3 | at most 1% of relevant PMIDs missing from the index | 3 of 3,236 (0.09%) | Held |
| T4 | Supports: recall@100 >= 0.60; recall@20 in 0.30-0.95 | 0.9077; 0.8462 | Held |
| T5 | Supports: `top:5` MRR in 0.15-0.70 | 0.3174 | Held |
| T6 | BM25: no_candidates 0, no problems, median 3,000-60,000 ms | 0, [], 15,833 ms | Held |
| T7 | compose: 0 empty, valid, median 150-250 words, median under 1,000 ms | 0, [], 247 words, 48.3 ms | Held |
| T8 | mean unjudged share >= 0.40 | 0.7285 | Held |
| T9 | judged precision >= 0.50 | (0.1691 + 0.0365) / (1 - 0.7285) = 0.757 | Held |
| T10 | topics with a mixed paper found >= 1 | 10 | Held |
| T11 | every step exit 0, within 240 minutes, peak memory under 1.5 GB | all 0, 45 minutes, **1.87 GB** | **Missed** (memory) |

The memory miss repeats `spark35-score-v2`'s (1.84 GB). Working explanation, not yet tested:
the container's memory count includes the file cache of the 92.5 GB index (`../t1_runner/
RESULTS-spark35.md`).

## What the numbers say

This is MV2's Task 2 floor: BM25 over all 39,167,523 PubMed records, then extractive answers of
whole abstract sentences with no language model.

- **Retrieval is decent.** A paper judged Supports is in BM25's top 5 for 32 of 65 questions, in
  the top 20 for 55 and in the top 100 for 59. The top 20 feed the answers, so a better ordering
  inside them (a reranker) can raise both measures below.
- **Most cited papers were never judged.** 72.9% of the answers' citations (about 11 per answer)
  are papers no 2024 BioGen run cited, so their stance is unknown. 16 of 65 answers have no judged
  citation at all. T8 held well above 0.60, so by the rule written in advance, the judged pool is
  too sparse to rank systems on its own: every later dev result reports judged precision and how
  many citations were judged.
- **What is judged is mostly right.** 75.7% of the judged citations are papers judged Supports
  (17%) or mixed (Supports and Contradicts in the topic, 3.7%); 0.3% are Contradicts-only and 6.3%
  Neutral or Not relevant (shares of all citations).
- **Coverage of the evidence is tiny.** Mean Supports recall is 3.7%: an answer of at most 250
  words cites about 11 papers, against dozens judged Supports per topic in the pool.
- **The cue-word conflict flag found nothing.** No answer was flagged as conflicting, although
  10 answers cite a mixed paper and 1 cites a Contradicts-only paper (not graded, as stated in
  advance; consistent with arXiv 2603.17580 on how contradiction is expressed). Conflict
  detection needs a model.
- **Composition is cheap.** 48 ms median per answer, against 15.8 s for the BM25 query.

## Next (written before any result of these jobs exists)

- `spark37-speed-v1` (`../speed/PREREGISTRATION.md`): drop words found in very many records from
  the BM25 query, then re-run these 65 questions and the Task 1 dev sets.
- `spark36-rerank-v1` (`../rerank/PREREGISTRATION-spark36.md`): rerank the first 50 of these
  candidates with the MedCPT cross-encoder, compose again and score the same way.

Limits: BioGen judgments come from 2024 runs over a 2023 PubMed snapshot, so an unjudged paper is
unknown, not wrong. BioGen questions are not SPARK's questions, and Task 2's metric ("T2QS") is
not yet defined. No human has checked any of this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
