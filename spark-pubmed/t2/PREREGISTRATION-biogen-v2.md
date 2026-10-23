# Pre-registration: census of the TREC 2024 BioGen assessments, second version (job `biogen-census-v2`)

Written on 2026-10-23 at about 19:45 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why a second version

`biogen-census-v1` (graded in `RESULTS-biogen.md`) parsed the file and grouped it correctly into
65 topics, but `biogen_census.py` 0.1.0 looked for the label words "supports" and "contradicts".
The file says "supporting" and "contradicting", and has a fifth citation label, "invalid
citation". So v1 counted only the Neutral and Not Relevant judgments (3,613), and every
prediction about support and contradiction failed for that reason.

`biogen_census.py` 0.2.0 reads the file's own words, keeps the PMIDs of invalid citations
(placeholders such as "1") out of the PMID totals, and counts labels per run (each topic holds
the answers of 30 runs under `machine_generated_answers`). 16 fake-data tests, including one with
the file's real layout. Same files, same data volume (`trec-biogen-2024`), so the job reads the
cached copies and checks their sha256 again.

## Already known from v1's schema.json (checks, not predictions)

- K3. 14,763 citation judgments in all (the `citation_assessment[]` counts summed over the 30
  run keys), each with a `cited_pmid`. 3,613 of them are Neutral or Not Relevant (v1), so
  Supports + Contradicts + Invalid = 11,150.
- K4. 30 runs per topic. Two runs (`rl31-70b_gpt-4o_ragnarokv5biogennc_top20`, `webis-gpt-1`)
  have no citations at all.
- K5. Sentence labels as in v1: Required 6,227, Unnecessary 1,032, Borderline 302,
  Inappropriate 24.

## Predictions

Parser
- P1. All 16 tests pass.
- P2. `citations` = 14,763, `citations_without_pmid` = 0, `topics` = 65,
  `topic_keys_matching_topic_ids` = 65, and the sentence-label counts equal K5.
- P3. `runs` = 30, and the per-run citation counts add up to 14,763.

Labels
- P4. Share of all citation judgments: Supports between 0.60 and 0.74; Contradicts between
  0.005 and 0.05; Invalid between 0.005 and 0.10.
- P5. At least 46 of the 65 topics (70%) have at least one citation judged Contradicts.
- P6. `distinct_pmids` (invalid citations excluded) is between 3,000 and 30,000.
- P7. `pmid_max` is below 39,000,000 and `pmids_over_spark_max` is 0.
- P8. `topic_pmid_pairs_supports_and_contradicts` is at least 1, and
  `topics_with_a_pmid_judged_both` is between 5 and 40.

Runs (compared with the track overview, arXiv 2411.18069: best citation support rate 79.97%,
contradict rates 0 to 6.13%; its definitions may differ from a plain label share)
- P9. Among runs with at least 100 citations, the highest Supports share is between 0.70 and
  0.90.
- P10. Among the same runs, the highest Contradicts share is at most 0.08.

Limits written down now: run names that are not plain ids become `run<i>` by position, which
merges runs wrongly if the file lists them in a different order per topic; P3 and the per-run
counts would then show it.

Contact: MV2, Munim, Inc., mv2@munimtech.com
