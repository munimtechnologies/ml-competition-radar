# Results: `biogen-stance-v1` (where "supporting" and "contradicting" meet in TREC 2024 BioGen)

Graded on 2026-10-23 at about 21:55 UTC by AI agents working in the name of MV2 of Munim, Inc.,
against `PREREGISTRATION-biogen-stance.md` word for word, misses included. CC BY 4.0.

Job: `biogen_stance.py` 0.1.0, python:3.12, 1 CPU, 1 GB, sealed container (host: dell).
Started 21:09:36 UTC, finished 21:12:35 UTC; exit 0 on every step. The assessments file was
downloaded again on this host: 11,128,359 bytes, sha256 `78449ef2...066d` (the pinned value).
Analysis took 0.3 s. Full output: `results-biogen-stance/stance.json` (counts, topic ids; no text).

## Checks (already known before the job)

| id | expected | got | held |
|---|---|---|---|
| K1 | 14,763 judgments; 10,240 / 275 / 1,412 / 2,201 / 635; `unknown_relations` empty; 65 topics | identical | yes |
| K2 | `runs` = 28 | 28 | yes |
| K3 | 202 / 168 / 34; 55 topics with `contradicting_pmids` > 0 | 202 / 168 / 34; 55 | yes |

## Predictions

| id | prediction | got | held |
|---|---|---|---|
| P1 | all 10 tests pass | `Ran 10 tests ... OK` | yes |
| P2 | `mixed_same_run` >= 50 | 114 | yes |
| P3 | `mixed_same_text` between 1 and 40 | **92** | **no** |
| P4 | `mixed_across_only` >= 40 | 48 | yes |
| P5 | `contradicts_judgments_on_mixed_pairs` >= 200 | 237 | yes |
| P6 | supports on mixed pairs > 3 x contradicts on mixed pairs | 1,161 > 711 | yes |
| P7 | `repeated_groups` >= 100 | 2,084 | yes |
| P8 | `repeated_pair_agreement` between 0.60 and 0.95 | 0.7464 | yes |
| P9 | `repeated_groups_with_contradicts_all_agree` < half of `repeated_groups_with_contradicts` | 11 < 65 | yes |

**3 of 3 checks and 8 of 9 predictions held.** The miss, P3, is the main result: same-claim
disagreement is not a minority. It is the largest group.

## What it shows

The 168 papers judged both Supports and Contradicts in one topic split into three groups that do
not overlap:

| where the two labels meet | papers | share |
|---|---|---|
| the same sentence text cites the paper under both labels (`same_text`) | 92 | 54.8% |
| one run's answer, different sentences, no shared text (`same_run_not_same_text`) | 28 | 16.7% |
| only different runs' different sentences (`across_only`) | 48 | 28.6% |

(`mixed_same_run` = 114 counts papers with both labels in one run's answer; 86 of them are also
`same_text`.)

Repeated judgments of the identical sentence text citing the same paper in the same topic:

- 2,084 such groups, 4,045 judgment pairs, 3,019 pairs agreeing (74.64%); 1,453 groups (69.7%)
  agree completely.
- Disagreeing pairs: Neutral vs Supports 694, Contradicts vs Supports 167, Not Relevant vs Supports
  100, Contradicts vs Neutral 48, Neutral vs Not Relevant 11, Contradicts vs Not Relevant 6.
- 130 groups include at least one Contradicts label. **Only 11 of them (8.5%) agree completely**,
  against 69.7% for all groups.

The rule written before the job ran: "if `same_text` is a large share, part of BioGen's
Contradicts signal is judging noise on one claim". `same_text` is 55%, so that reading applies.
Most of the papers that look "both supporting and contradicting" got both labels on one claim.
When an identical claim-paper pair was judged more than once and any judgment said Contradicts,
another judgment of it nearly always said something else.

## What this means for SPARK Task 2

Task 2 scores "Conflict/Controversy Coverage". If its gold conflicts come from per-citation
Contradicts labels like BioGen's, much of that gold is not repeatable. Scoring a system against
a paper-level list of contradicting PMIDs would reward or penalise it on judgments that do not
reproduce. For our own development scoring, `compose.py` 0.2.0 therefore gives a paper judged
both ways its own class (`mixed`) and no longer counts it under both Supports and Contradicts.

## Limits

- Identical text is a strict test: reworded claims count as different, so `same_text` is a
  lower bound on one-claim disagreement.
- The file does not say whether repeated sentences were judged by one assessor or by several, or
  in the same session. Disagreement here mixes assessor differences with context: the same
  sentence can sit in different answers.
- Agreement rates are not corrected for chance here, and Contradicts is rare (1.9% of
  judgments). The pre-registered follow-up `biogen-stance-v2` measures specific agreement per
  label, Scott's pi, and within-run vs across-run agreement (`PREREGISTRATION-biogen-stance-v2.md`).
- Raw counts only. No sentence or abstract text was read or written.

Prior art checked before the job (2026-10-23): the TREC 2024 and 2025 BioGen overviews (arXiv
2411.18069, 2603.21582) and arXiv 2603.17580. None of them reports per-paper both-ways counts or
agreement on repeated identical sentences.

Prior art found after the job, while grading (so not used for any prediction): MedAESQA (Gupta,
Bartels, Demner-Fushman, Scientific Data 12:1035, 2025; https://pmc.ncbi.nlm.nih.gov/articles/PMC12179289)
releases 40 of these questions. It says each final judgment is the majority vote of at least
three crowdsourced clinician annotators. It reports, per evidence-relation label, the share of
annotators who chose the majority label: Supporting 82.09, Contradicting 67.67, Neutral 60.14,
Not Relevant 100. So lower agreement on Contradicting within one item was already known. What is
new here is that this is about consistency between items: the released final labels of
identical sentence-paper pairs, judged as separate items, disagree, and that accounts for most of
the papers that look both supporting and contradicting. The MedAESQA paper does not say whether
its process covers all 65 topics of the 2024 file.

Contact: MV2, Munim, Inc., mv2@munimtech.com
