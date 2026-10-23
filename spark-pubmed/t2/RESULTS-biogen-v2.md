# Results: census of the TREC 2024 BioGen assessments, second version (job `biogen-census-v2`)

Graded on 2026-10-23 at about 20:50 UTC, against `PREREGISTRATION-biogen-v2.md` word for word,
by AI agents working in the name of MV2 of Munim, Inc. Counts are in `results-biogen-v2/`.
`gold_t2.jsonl` (judged PMIDs per topic) stays in the job output, because NIST states no licence
for the source file. CC BY 4.0.

## What ran

Host `blade`, 1 CPU, 3 GB, 159 s in all, status ok. `biogen_census.py` 0.2.0. Both files came
from the cached data volume and hashed to the same sha256 as in v1 (topics `d4569041...8774`,
assessments `78449ef2...066d`).

## Grades: 3 of 3 checks and 9 of 10 predictions held

| # | Statement | Result | Grade |
|---|---|---|---|
| K3 | 14,763 judgments; Supports + Contradicts + Invalid = 11,150 | 14,763; 10,240 + 275 + 635 = 11,150 | held |
| K4 | 30 runs; `rl31-70b_gpt-4o_ragnarokv5biogennc_top20` and `webis-gpt-1` have no citations | 30; both have 0 | held |
| K5 | sentence labels Required 6,227, Unnecessary 1,032, Borderline 302, Inappropriate 24 | same | held |
| P1 | all 16 tests pass | "Ran 16 tests ... OK" | held |
| P2 | `citations` 14,763, `citations_without_pmid` 0, 65 topics, 65 keys matching topic ids, sentence labels = K5 | all as stated | held |
| P3 | `runs` 30, per-run citation counts sum to 14,763 | 30; the 30 per-run counts sum to 14,763 | held |
| P4 | shares: Supports 0.60-0.74, Contradicts 0.005-0.05, Invalid 0.005-0.10 | 0.6936, 0.0186, 0.0430 | held |
| P5 | at least 46 topics with a Contradicts citation | 55 | held |
| P6 | `distinct_pmids` (invalid excluded) 3,000-30,000 | 3,858 | held |
| P7 | `pmid_max` below 39,000,000; 0 over the SPARK maximum | 38,090,936; 0 | held |
| P8 | at least 1 topic-PMID pair judged both Supports and Contradicts, and `topics_with_a_pmid_judged_both` between 5 and 40 | 168 pairs; **54 topics** | **missed** (upper bound) |
| P9 | highest Supports share among runs with 100+ citations 0.70-0.90 | 0.7951 (`listgalore_gpt-4o_ragnarokv5biogen_top20`) | held |
| P10 | highest Contradicts share among those runs at most 0.08 | 0.0512 (`webis-1`) | held |

P8 missed because papers judged both ways are far more common than predicted: 54 of the 55 topics
with any Contradicts judgment have at least one paper that is also judged Supports there.

## What the counts show

- 14,763 citation judgments: Supports 10,240 (69.4%), Contradicts 275 (1.9%), Neutral 1,412,
  Not Relevant 2,201, Invalid 635 (4.3%). Contradicts judgments per topic: median 3, maximum 19.
- 3,858 distinct PMIDs were cited (invalid citations excluded), from 14,564,663 to 38,090,936;
  all are inside the SPARK corpus's PMID range. 202 distinct PMIDs were ever judged Contradicts.
- 24 of the 30 runs have at least 100 citations. Invalid citations concentrate in the few-shot
  and zero-shot Gemini Flash and GPT-4o mini runs (15-21% of their citations) and `webis-1`
  (18%); every other run is at 0-3%.
- The overview (arXiv 2411.18069) gives `listgalore_gpt-4o_ragnarokv5biogen_top20` a 79.97%
  citation support rate and a 1.76% contradict rate. Its plain label shares here are 79.51% and
  1.30%, so the overview's rates are not plain label shares (perhaps averaged per answer); this
  census does not reproduce them and does not claim to.

## Per-topic follow-up (labelled post hoc)

Reading only the per-topic Contradicts PMID lists in `gold_t2.jsonl` (numbers, no text): the
Contradicts lists hold 202 topic-PMID pairs, the same number as the 202 distinct Contradicts
PMIDs, so **no paper is judged Contradicts in more than one topic**. With the 168 mixed pairs
above, **168 of 202 (83%) papers judged contradicting an answer sentence are also judged
supporting another sentence in the same topic**; only 34 are contradicting and never
supporting. 10 topics (122, 123, 124, 135, 139, 141, 147, 151, 155, 165) have no Contradicts
judgment.

Why it may matter for SPARK Task 2 (which scores coverage of conflicting evidence): in this
data, stance looks like a property of a claim-paper pair, not of a paper. Job `biogen-stance-v1`
(`PREREGISTRATION-biogen-stance.md`) tests whether the mixed pairs are one claim judged two ways
or genuinely different claims, and how often repeated identical judgments agree.

Contact: MV2, Munim, Inc., mv2@munimtech.com
