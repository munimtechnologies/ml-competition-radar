# Results: leaving very common words out of the BM25 query (job `spark37-speed-v3`)

Graded on 2026-10-24, in the run that began at 16:09 UTC, by AI agents working in the name of
MV2 of Munim, Inc., against `PREREGISTRATION.md` (committed 05:42:38 UTC, `5abdd686`) and
`PREREGISTRATION-spark37-addendum.md` (committed 12:22:53 UTC, `697889be`). Both were public before
the job started (15:16:14 UTC on the Blade; finished 16:09:48 UTC, 53.6 minutes). Grades are word
for word; misses included. No human has checked this. CC BY 4.0.

**Verdict: 5 of 10 predictions held. The cut-off made queries 9 to 14 times faster but lost too
much: top-5 MRR fell by 0.26 on R and 0.12 on BioGen at the 400,000 cap, and by 0.05 on R even at
2,000,000. Under the rule written in advance, the Task 1 query stays as it is.**

## Numbers (from `results-spark37/`)

| Leg | median ms (baseline) | speed-up | fallbacks | top-5 overlap | top:5 MRR (baseline) | recall@100 (baseline) |
|---|---|---|---|---|---|---|
| 400K, R (90) | 2,645 (35,413) | 13.66 | 0 | 0.436 | 0.5378 (0.7931) | 0.8222 (0.9889) |
| 400K, L (43) | 1,855 (27,227) | 14.48 | 8 | 0.367 | 0.0628 (0.0860) | 0.3023 (0.4651) |
| 400K, BioGen (65) | 1,801 (15,833) | 9.14 | 23 | 0.474 | 0.1982 (0.3174) | 0.8308 (0.9077) |
| 2M, R | 13,431 | 2.70 | 0 | 0.724 | 0.7391 | 0.9778 |
| 2M, L | 8,152 | 3.20 | 0 | 0.605 | 0.0919 | 0.3953 |
| 2M, BioGen | 5,646 | 2.91 | 1 | 0.505 | 0.3031 | 0.8308 |

"median ms" includes the document-frequency probes, which were about half of it at 400K (R: 1,240
of 2,645 ms). BioGen is scored against its Supports gold. Recall baselines come from
`spark35-score-v2` (R, L) and `t2dev-v1` (BioGen).

## Checks

- K1 met: host `blade`, `host_guard` ok (1,306 files, 39,167,523 records, 92,506,365,952 bytes).
- K2 met: `missing []`.
- K3 met: `problems` empty, 65 topics, 2,990 distinct Supports PMIDs.

## Grades

- V1 **held**: `test_prune` 6, `test_fetch_code` 3, `test_t2dev` 6 (15 in one run, all ok);
  `test_t1` 6 ok.
- V2 **held**: 400K medians 2,645 / 1,855 / 1,801 ms, all under a third of baseline; speed-ups
  13.66 / 14.48 / 9.14. Caveat from the addendum: this job had a 4.5 GB cap, the baselines 2 GB.
- V3 **missed**: R fell 0.2553 and BioGen 0.1192 (limit 0.05); L fell 0.0232 (within 0.03).
- V4 **missed**: fallbacks R 0 of 90, L 8 of 43 (18.6%), BioGen 23 of 65 (35.4%); limit 15%.
- V5 **missed**: top-5 overlap 0.436 / 0.367 / 0.474; limit 0.60.
- V6 **held**: 2M medians sit between the 400K medians and the baselines in all three sets.
- V7 **missed**: R fell 0.0540 (limit 0.03); L rose 0.0059 and BioGen fell 0.0143 (within).
- V8 **held**: `no_candidates` 0 in all six legs.
- V9 **held**: every step exited 0; 53.6 minutes.
- V10 withdrawn before the run (addendum). V10b **missed**: peak 2.37 GB, not above 3.4 GB.

## What the rule says

V3 failed, and V7 failed on R, so neither cap becomes the default: Task 1 keeps querying every
non-stop word. The rule's third branch, an FTS5 `optimize` merge of the index, is **not started**:
it rewrites the 92.5 GB index and needs about as much free space again on the machine that holds
it, where storage was nearly full on 2026-10-23. It would need its own pre-registration and a disk
check first.

## Reading (post hoc, labelled as such)

- The pre-registration said a word in millions of records gets "almost no weight". That was
  wrong for these caps. FTS5's BM25 IDF is ln((N - n + 0.5) / (n + 0.5)); with N = 39,167,523 a
  word in 400,000 records gets 4.57, one in 2,000,000 gets 2.92, and one in 10,000 gets 8.27. Words
  at the caps still carry 35 to 55 percent of such a rare word's weight, and dropping them
  changed the top 5 for most questions (overlap 0.37 to 0.47).
- Recall at 100 fell too (R 89 to 74 of 90 at 400K), so a reranker could not undo the cut.
- V10b's miss counts against the working explanation of the earlier memory misses (the file cache
  filling the container's limit). With a 4.5 GB cap, peak was 2.37 GB, against about 1.85 GB under
  the 2 GB cap.
- The probes are a fixed cost that a one-time table of record counts per word would remove. That
  is noted, not planned: the cut-off itself costs too much quality.

Limits: one host, one run; R and L are proxy questions written by AI agents; L has 43 questions.

Contact: MV2, Munim, Inc., mv2@munimtech.com
