# Results: the BioGen leave-out test with sentence embeddings (biogen-reuse-emb-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Graded 2026-10-31 (about 11:10 UTC) against `PREREGISTRATION-biogen-reuse-emb.md`, word for word.
The job ran once on 2026-10-31, about 07:48-07:58 UTC (python:3.12, 2 CPUs, 3 GB limit). Its
outputs, counts and scores only, are in `results-biogen-reuse-emb/` (`emb.json`, `emb_runs.json`,
`model.json` and the three `*_public.json` checks).

**Outcome: 5 of 5 checks, 7 of 9 predictions. Embeddings score Required sentences no better than
word overlap (AUROC 0.705 against 0.702), and answer length still ranks the 30 runs by official
completeness better (Kendall tau 0.80 against 0.82). By the rule fixed in advance the embedding
proxy is not used, and no further variant of this proxy is tried on the 2024 judgments.**

## Checks

| check | pre-registered | observed | held |
|---|---|---|---|
| C1 | `wait_public.py` exits 0; `match` recorded | exit 0; public copy seen 07:48:49 UTC, sha256 `7dfe3319...f08c` on both sides, `match` true | yes |
| C2 | `test_biogen_reuse_emb` runs 7 tests, all pass | "Ran 7 tests", OK | yes |
| C3 | public `biogen_reuse.py` and `official_biogen2024.json` match the job's copies | `match` true for both (`e3c044d7...1529`, `504a548f...f0ec`) | yes |
| C4 | `fetch-model` exits 0, `problem` null, weights sha256 as pinned | exit 0; `model.safetensors` `78c0197b...5658`, 437,971,872 bytes | yes |
| C5 | run step exits 0, `problem` null, data as pinned, `agree` true | exit 0; both files as pinned; `agree` true (word-overlap AUROC 0.7023 / 0.7124, tau 0.703, length 0.8186, 7,932 sentences, all equal to biogen-reuse-v1) | yes |

## Predictions

| | pre-registered | observed | held |
|---|---|---|---|
| E1 | 65 topics, 30 runs, 7,932 sentences, 30 runs ranked | exactly these | yes |
| E2 | embedding team-out sentence AUROC 0.60-0.80 | 0.7050 | yes |
| E3 | higher than word overlap's on the same sentences | 0.7050 against 0.7023 | yes (by 0.003) |
| E4 | bootstrap 95% interval of that difference wholly above 0 | -0.0170 to 0.0211 (median 0.0019) | **no** |
| E5 | run-out minus team-out AUROC 0.00-0.05 | 0.7144 - 0.7050 = 0.0094 | yes |
| E6 | tau-b (bar 0.7), team-out recall vs completeness R, >= 0.50 | 0.7958 | yes |
| E7 | that tau above the length baseline's | 0.7958 against **0.8186** | **no** |
| E8 | tau-b (bar 0.7), team-out precision vs official precision, >= 0.30 | 0.4677 | yes |
| R1 | embedding <= 30 min on 2 threads; peak memory <= 2,000 MB | 510.2 s for 6,430 texts; 1,154.9 MB | yes |

## Decision (fixed in advance)

The proxy needed team-out AUROC >= 0.60 **and** E6 **and** E7. E7 did not hold, so **the
embedding proxy is not MV2's development metric**. The word-overlap proxy (`biogen-reuse-v1`)
failed the same way, so neither passes, and by the rule no further variant of this proxy (other
bars, the soft scores, other models) is tried on the 2024 judgments.

## What the numbers show (no predictions; read with care)

- **Embeddings close most of the gap to length, not all of it.** Recall's tau rises from 0.70
  (words, bar 0.5) to 0.80 (embeddings, bar 0.7). The length baseline is 0.82.
- **Bar sensitivity (not a result).** Embedding recall's tau is 0.82 at bar 0.5, 0.81 at 0.6, 0.80
  at 0.7, 0.79 at 0.75, 0.77 at 0.8 and 0.85, and 0.68 at 0.9. Only the loosest bar edges past
  length (0.8237 against 0.8186). Choosing it now would fit the bar to this data, so it is not used.
- **Precision ranks much better with embeddings:** tau 0.47 against official precision (words:
  0.26 at bar 0.5).
- **Leave-one-run-out no longer collapses.** With words, keeping the scored run's team mates in the
  pool cut recall's tau to 0.39. With embeddings at bar 0.7, run-out (0.797) and team-out (0.796)
  agree, at least on these 30 runs.
- Per-run numbers at every bar are in `emb_runs.json`.

## What this means for SPARK Task 2

On the 2024 judgments, a pool of other runs' Required sentences, matched by words or by
embeddings, does not rank systems better than counting their sentences. A rewriting stage cannot
be developed against this yardstick. The remaining route is a reference that no run produced:
NLM's expert nuggets. `medaesqa-nugget-v1` tried MedAESQA's copy and found the nugget field empty
(`RESULTS-medaesqa-nugget.md`).

## Limits

30 runs from 5 teams, so tau mostly reflects the gaps between teams; one model and one primary bar;
the official completeness clusters a pool that includes the scored run, so it and a leave-out
proxy measure different things. No human has checked these counts.

Contact: MV2, Munim, Inc., mv2@munimtech.com
