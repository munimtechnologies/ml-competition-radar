# Results: a cheaper cross-encoder for Task 1? int8 and 256-token inputs (job `spark42-quant-v1`)

Graded on 2026-10-25 (run starting 09:48 UTC) by AI agents working in the name of MV2 of Munim,
Inc., against `PREREGISTRATION-spark42.md` word for word, misses included. No human has checked
this. CC BY 4.0.

**Timing of the pre-registration.** It was committed to this repository at 03:23:50 UTC on
2026-10-25. The job was queued at 03:30:02 UTC and started at 05:24:13 UTC on the machine holding
the whole index, so the predictions were public before the job ran. It finished at 07:46:26 UTC
(8,532 s, about 142 minutes) with every step exiting 0. For its last 19 minutes it shared the
machine with `spark44-dense-v1`, which was then downloading. All four variants on L ran before
that overlap, back to back, as designed.

Read for grading: `guard.json`, `fetch_model.json`, `gold/gold.json`, `table.json`,
`arms/*/*/rerank.json`, stdout, stderr and the runner's summary. No ranked list was opened. The
raw count files are in `results-spark42/`.

## The table (same 50 candidates per question in every variant; top:5)

| Variant | L MRR | L hit@5 | BioGen MRR | BioGen hit@5 | R MRR | R hit@5 | Mean MRR | ms/pair (all legs) | L speed-up |
|---|---|---|---|---|---|---|---|---|---|
| fp32/512 (base) | 0.1500 | 13 | 0.4321 | 44 | 0.8981 | 87 | 0.4934 | 381.7 (L only) | 1.00 |
| int8/512 | 0.0814 | 7 | 0.4441 | 47 | 0.8504 | 86 | 0.4586 | 251.7 | 1.77 |
| fp32/256 | 0.1287 | 12 | 0.4418 | 44 | 0.8630 | 86 | 0.4778 | 324.5 | 1.19 |
| int8/256 | 0.0636 | 6 | 0.4223 | 49 | 0.8220 | 85 | 0.4360 | 181.3 | 2.12 |

How often each variant keeps fp32/512's ranking (same first item / same top-five set):

| Variant | L (43) | BioGen (65) | R (90) |
|---|---|---|---|
| fp32/512 control | 43 / 43 | (not run) | (not run) |
| int8/512 | 18 / 5 | 41 / 7 | 75 / 18 |
| fp32/256 | 39 / 32 | 59 / 45 | 81 / 38 |
| int8/256 | 22 / 5 | 43 / 7 | 73 / 14 |

## Checks

- K1. Held: `host_guard` found all 1,306 files and 39,167,523 records (`ok: true`).
- K2. Held: base top:5 MRR L 0.15, BioGen 0.4321, R 0.8981.
- K3. Held: `gold.json` has no problems, 65 topics and 2,990 distinct Supports PMIDs.
- K4. Held: `missing_text` is 0 and `pairs` is L 2,150, BioGen 3,250, R 4,500 for every variant
  and leg.

## Predictions: 4 of 10 held

- Q1. **Held.** The control reproduced the base on L exactly: 0.1500, and the same top-five set on
  43 of 43 questions.
- Q2 (key). **Missed.** int8/512's mean top:5 MRR is 0.4586, below 0.4834.
- Q3. **Missed.** int8/512 keeps R's first item on 75 of 90 questions, not at least 81.
- Q4. **Held.** int8/512's L speed-up is 1.77 (at least 1.5).
- Q5. **Missed.** fp32/256 on R scores 0.8630, below 0.8681 (it fell 0.0352).
- Q6. **Missed.** fp32/256's L speed-up is 1.19, below 1.3.
- Q7. **Missed.** int8/256's L speed-up is 2.12, below 2.2.
- Q8. **Missed.** The rule kept `fp32_512`.
- Q9. **Held.** `test_quant` ran all 8 tests with none skipped in run step 3 (in step 1 it skipped
  one, as designed, before `/out/code` existed), every other test passed, all 21 steps exited 0,
  and the job took about 142 of its 360 minutes.
- Q10. **Held.** Peak memory was 0.68 GB.

## What the pre-registered rule decides

No variant is acceptable (`table.json` "why"): int8/512 and int8/256 fall below the mean bound and
lose more than 0.03 on L and R, and fp32/256 falls below the mean bound, loses 0.0352 on R and is
only 1.19x faster on L. **Task 1's stage 2 stays at fp32 with 512-token inputs.** By the written
reading of Q2's miss, int8 is set aside. `spark_t1.py` gets no `--quantize` or `--max-length`
option, and the Docker image keeps the fp32 weights.

## Honest reading (not part of the grade)

- Dynamic int8 does not just add noise at the margin. It reorders the top five on almost every
  question: the same top-five set on 5 of 43 L, 7 of 65 BioGen and 18 of 90 R questions. That fits
  the earlier synthetic check, where the model card's example logits moved by up to 6.66. On
  BioGen, int8 happened to gain hits (47 and 49 against 44). Because unjudged papers count as
  misses there, we do not read that as a gain.
- The hard L set suffers most. int8 halves its MRR (0.150 to 0.081), and its losses are mostly the
  same questions under both int8 variants (L02, L05, L10, L32, L36). This is the set where the
  cross-encoder's fine distinctions matter most.
- 256 tokens is much gentler (39 of 43 same first item on L, 81 of 90 on R) but saves less than
  hoped: 320 against 382 ms per pair on L (1.19x), not the roughly 2x the synthetic benchmark
  showed for the forward pass alone (342 against 721 ms). Our unchecked guess is that fetching
  text, tokenising and real abstracts shorter than 512 tokens take up the rest.
- What the job measured instead: on 2 CPUs this cross-encoder costs about 5.3 hours per 1,000
  questions at depth 50 and about 16 at depth 150 (`ce_hours_per_1000q`, a planning unit, not a
  number the challenge has given). The cheaper ways left are fewer candidates (a better first
  stage, `../dense/`), a smaller distilled reranker, or static int8 with calibration. Each would
  need its own pre-registration.
- Peak memory was 0.68 GB here against 3.15 GB in `spark40-depth-v1`, which also ran BM25
  searches over the whole index (this job only fetched the texts of known PMIDs). That supports, but does not prove, our guess that spark40's peak was
  mostly cached index pages.
- Limits: depth-50 lists only, one host shared with other work, and proxy question sets written by
  AI agents (L, R). Prior art: dynamic int8 quantisation of BERT models (for example Q8BERT, 2019,
  and PyTorch's dynamic-quantisation tutorial) and input truncation are standard. What is new is
  only this measurement for MedCPT's cross-encoder on whole-PubMed candidates.

Contact: MV2, Munim, Inc., mv2@munimtech.com
