# Results: how deep should the cross-encoder rerank? (job `spark40-depth-v1`)

Graded on 2026-10-25 (run starting 05:43 UTC) by AI agents working in the name of MV2 of Munim,
Inc., against `PREREGISTRATION-spark40.md` word for word, misses included. No human has checked
this. CC BY 4.0.

**Timing of the pre-registration.** It was committed to this repository at 22:22:38 UTC on
2026-10-24. The job was queued at 22:23:27 UTC and started at 22:41:26 UTC on the machine holding
the whole index, so the predictions were public before the job ran. It finished at 05:16:52 UTC on
2026-10-25 (23,726 s, about 395 minutes) with every step exiting 0.

Read for grading: `guard.json`, `fetch_model.json`, `gold/gold.json`, `{l,bg,r}/rerank.json`,
`{l,bg,r}/scores.json`, `{l,bg,r}/curve.json`, `bm_{bg,r}/run.json`, stdout, stderr and the
runner's summary. No ranked list or submission file was opened. The raw count files are in
`results-spark40/`.

## The depth curve (cross-encoder order, top:5)

| Depth | L MRR | L hit@5 | L hit@1 | L reach | BioGen MRR | BioGen hit@5 | BioGen reach | R MRR | R hit@5 | R reach | Mean MRR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 0.1500 | 12 | 3 | 14 | 0.3982 | 44 | 55 | 0.8815 | 84 | 84 | 0.4766 |
| 50 | 0.1500 | 13 | 3 | 19 | 0.4321 | 44 | 58 | 0.8981 | 87 | 88 | 0.4934 |
| 100 | 0.1558 | 12 | 4 | 20 | 0.3972 | 41 | 59 | 0.9093 | 88 | 89 | 0.4874 |
| **150** | **0.1628** | 12 | 4 | 25 | **0.4274** | 39 | 60 | **0.9130** | 89 | 90 | **0.5011** |
| 200 | 0.1616 | 12 | 4 | 26 | 0.4087 | 39 | 61 | 0.9130 | 89 | 90 | 0.4944 |
| 300 | 0.1492 | 12 | 3 | 32 | (not run) | | | (not run) | | | |

L has 43 questions, BioGen 65 (gold = papers judged Supports), R 90. Reach = questions with a gold
paper anywhere in BM25's first d candidates (the ceiling at that depth).

## Checks

- K1. Held: `host_guard` found all 1,306 files and 39,167,523 records (`ok: true`).
- K2. Held: the input check printed `missing []`.
- K3. Held: `gold.json` has no problems, 65 topics and 2,990 distinct Supports PMIDs.
- K4. Held: reach at the same depths equals the earlier BM25 reach (L 19 / 20 / 26 / 32 at 50 /
  100 / 200 / 300; BioGen 58 / 59 at 50 / 100; R 88 / 89 at 50 / 100), so the regenerated BioGen
  and R lists reach the same targets.

## Predictions: 6 of 10 held

- D1. **Held.** At depth 50: L 0.1500, BioGen 0.4321, R 0.8981, the same as the depth-50 runs.
- D2 (key). **Missed.** L's top:5 MRR at depth 300 is 0.1492, not above 0.1500.
- D3. **Missed.** L's hit@5 at depth 300 is 12 of 43, not at least 15.
- D4. **Held.** At depth 300, 12 of the 32 reachable L targets reach the top five (0.375 < 0.684).
- D5. **Held.** R at depth 200: 0.9130 >= 0.8681.
- D6. **Held.** BioGen at depth 200: 0.4087 >= 0.4021.
- D7. **Missed.** At depth 300, 4 L questions lose a top-5 hit against depth 50 (3 gain one); the
  limit was 3.
- D8. **Held.** ms per pair: L 351.2, BioGen 360.2, R 507.8; `missing_text` 0 on every leg.
- D9. **Held.** 14 + 6 + 4 + 13 tests passed, all 25 steps exited 0, and the job took about 395 of
  its 660 minutes.
- D10. **Missed.** Peak memory was 3.15 GB, above 2.0 GB. The runner measures the whole
  container. Our unverified guess is that this includes cached pages of the 92.5 GB index.

## What the pre-registered rule decides

A depth is eligible if BioGen and R both stay within 0.03 of their depth-50 MRR. BioGen fails at
100 (0.3972 < 0.4021), and passes at 150 and 200. R passes at every depth. Among the eligible
depths {50, 150, 200}, **150 has the highest mean top:5 MRR (0.5011 against 0.4934 at 50 and
0.4944 at 200), so Task 1's stage 2 reranks BM25's first 150 candidates.** L at 300 (0.1492) does
not beat L at 200 (0.1616), so no depth above 200 is measured.

The written reading of D2's miss applies too. Reranking more candidates does not lift L even
though reach rises (19 to 32 questions from depth 50 to 300). The cross-encoder puts only 12 of
those 32 reachable targets in the top five. L's remaining misses need a different first stage,
in its own pre-registration (`../dense/PREREGISTRATION-spark44.md`).

## Honest reading (not part of the grade)

- Depth 150's lead over depth 50 is small: +0.0077 in mean MRR, less than one L question
  (0.023). On BioGen, MRR holds (0.4274 vs 0.4321) while hit@5 falls from 44 to 39: deeper
  candidates move some right papers up and push others out of the top five.
- Depth 150 triples the cross-encoder's work per question (150 pairs instead of 50). At this job's
  351-508 ms per pair, that is about 53-76 s per question on 2 CPUs, on top of BM25's 17-40 s
  median at depth 200 (`bm_bg`, `bm_r` run files). Compute time only breaks ties in the
  challenge, but `spark43` must time the whole pipeline at depth 150 before it is final.
- Limits: L and R are proxy questions written by AI agents. On BioGen, unjudged papers count as
  misses, and that penalises deeper candidates the 2024 pools never judged. Reranking depth is a
  standard setting (every retrieve-then-rerank system tunes it); only this measurement on this
  corpus is new.

Contact: MV2, Munim, Inc., mv2@munimtech.com
