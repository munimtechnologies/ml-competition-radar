# Results: census of the TREC 2024 BioGen assessments (job `biogen-census-v1`)

Graded on 2026-10-23 at about 19:35 UTC, against `PREREGISTRATION-biogen.md` word for word, by
AI agents working in the name of MV2 of Munim, Inc. Counts and file structure are in
`results-biogen/`. `gold_t2.jsonl` (judged PMIDs per topic) stays in the job output, because
NIST states no licence for the source file. CC BY 4.0.

## What ran

Host `blade`, 1 CPU, 3 GB. 161 s in all, status ok. Both files downloaded from trec.nist.gov:
topics 21,598 bytes (sha256 `d4569041...8774`), assessments 11,128,359 bytes (sha256
`78449ef2...066d`). The assessments parsed in 0.1 s.

## Grades: 2 of 2 checks and 5 of 10 predictions held

| # | Statement | Result | Grade |
|---|---|---|---|
| K1 | 65 topics, ids 116-180 with no gaps, keys id/topic/question/narrative | 65, 116-180, contiguous, those 4 keys | held |
| K2 | assessments file over 10,485,760 bytes | 11,128,359 | held |
| P1 | 12 fake-data tests pass | "Ran 12 tests ... OK" | held |
| P2 | all four citation labels and all four sentence labels occur | Supports 0 and Contradicts 0 counted | **missed** |
| P3 | 65 topics, 65 keys matching topic ids | 65 and 65 | held |
| P4 | `citations_without_pmid` under 5% | 0 | held |
| P5 | Supports share 0.45-0.85; Contradicts share 0.005-0.06 | 0.0 and 0.0 | **missed** |
| P6 | at least 46 topics with a Contradicts citation | 0 | **missed** |
| P7 | `distinct_pmids` 3,000 to 30,000 | 2,075 | **missed** |
| P8 | `pmid_max` under 39,000,000; 0 PMIDs over the SPARK maximum | 38,082,262; 0 | held |
| P9 | at least one PMID judged both Supports and Contradicts in a topic | 0 | **missed** |
| P10 | Required is the most common sentence label | Required 6,227, Unnecessary 1,032, Borderline 302, Inappropriate 24 | held |

## Why five predictions missed

All five misses have one cause, and it is a defect in `biogen_census.py` 0.1.0, not a finding
about the data. `schema.json` shows the file's own citation labels:
`supporting`, `contradicting`, `neutral`, `not relevant` and `invalid citation`. Version 0.1.0
matched "supports" and "contradicts" exactly, so it counted only Neutral (1,412) and Not
Relevant (2,201) judgments, and its PMID total held only those (2,075). The fake-data tests used
the words in the track overview, not the file's words, so they could not catch it. The
pre-registration's own fallback covered a failed grouping (P3), not wrong label words.

## The file's layout (from `schema.json`)

- A list of 65 records, each with `question_id` and `machine_generated_answers`. That is a dict
  of 30 runs, each with `answer`, `answer_sentences` and `is_answer_accurate` ("yes"/"no").
- Each sentence has `answer_sentence`, `answer_sentence_id`, `answer_sentence_relevance` (the
  four sentence labels, sometimes null) and `citation_assessment`: null, or a list of
  `{cited_pmid, evidence_relation, evidence_support}`.
- Summed over the 30 run keys there are 14,763 citation judgments. Two runs
  (`rl31-70b_gpt-4o_ragnarokv5biogennc_top20`, `webis-gpt-1`) have no citations.
- `evidence_support` holds text from the cited abstract. The census never writes it out.

## Next (labelled post hoc)

`biogen_census.py` 0.2.0 reads the file's own label words, keeps the "PMIDs" of invalid
citations out of the PMID totals, and adds per-run label counts. It has 16 tests, one of them on
the real layout. It is pre-registered in `PREREGISTRATION-biogen-v2.md` and runs as
`biogen-census-v2`. P2 and P5 to P9 are tested again there, with new ranges where K3 (3,613 of
14,763 judgments are Neutral or Not Relevant) now bounds them.

Contact: MV2, Munim, Inc., mv2@munimtech.com
