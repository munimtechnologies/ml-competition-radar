# Results: SPARK PubMed corpus conformance audit (sample run 1)

By AI agents working in the name of MV2 of Munim, Inc., 2026-10-22. CC BY 4.0. No human has
reviewed these numbers yet. The predictions in `PREREGISTRATION.md` were written before any
corpus file was read; they are graded below word for word, misses included.

## Run

- Job `spark27-audit-v1`, sealed container, python:3.12, 2 CPUs. Started 2026-10-22 09:27 UTC,
  finished 09:40 UTC (audit step 698 s). Peak memory 0.08 GB. All 4 tests passed first.
- Command: `python audit.py --stride 10 --also 0656 --workers 3` (plus scratch and output paths).
- The live listing held 1,306 files (`pubmed27n0001` to `pubmed27n1306.xml.gz`). 133 files were
  sampled: every 10th from 0001, plus 0656 and 1306. All 133 matched their `.md5`; none failed.
- Sampled: 5,684,171,870 bytes compressed, 3,977,567 records.

## Grades (10 of 11 held)

| # | Prediction | Measured | Grade |
|---|---|---|---|
| P1 | Every sampled file except 1306 holds exactly 30,000 records | 131 of 132 do; `pubmed27n0851` holds 29,999 | MISS |
| P2 | Under 0.1% have a journal year before 1959 | 1 of 3,977,567 (PMID 13823065, journal year 1958) | HIT |
| P3a | At least one has a journal date after July 2026 | 3,564 (0.09%) | HIT |
| P3b | Under 0.1% have no journal or electronic date on or before 2026-07-31 | 3 (0.0001%) | HIT |
| P4 | No Preprint publication type (D000076942) | 0 | HIT |
| P5 | No DeleteCitation entries | 0 | HIT |
| P6 | No PMID twice across the sample | 0 duplicates | HIT |
| P7a | `pubmed27n0001` holds at least 99% of `pubmed26n0001`'s PMIDs | 30,000 of 30,000 (100%) | HIT |
| P7b | `pubmed27n0656` shares under 50% of `pubmed26n0656`'s PMIDs | 0 of 30,000 (0%) | HIT |
| P8 | 20-35% carry a PMC id | 27.46% | HIT |
| P9 | 60-78% have an abstract | 73.58% | HIT |

## What it shows

- **The corpus matches its definition closely.** In the sample: no preprint-type records, no
  deletions, no duplicate PMIDs, and only 1 record with a journal year before 1959.
- **Which "publication date"?** The window is not applied to any single date field:
  - 3,564 sampled records have a journal (issue) date after July 2026;
  - 659 have an electronic date after July 2026;
  - 16,969 (0.43%) entered PubMed (PubMedPubDate "pubmed") after July 2026.

  All of these are in the corpus. Only 3 records (PMIDs 42391011, 42627672, 42627673; journal date
  2026-08-27) have neither a journal nor an electronic date on or before 2026-07-31. So "journal
  date or electronic date, whichever is in the window" fits 3,977,564 of 3,977,567 records. This is
  an inference from counts. NLM's selection code was not seen.
- **Size.** Every sampled file except 0851 and the last holds 30,000 records, and the last file
  (1306) holds 17,568. That puts the whole PubMed part at about 1,305 x 30,000 + 17,568, so
  roughly 39.17 million records (an estimate from a sample, not a count). Compressed size, by
  the sample's mean of 42.7 MB per file, is roughly 56 GB.
- **Record coverage.** 73.6% of records have an abstract, 82.6% have MeSH headings and 27.5% have
  a PMC id. Journal years run from 1958 (1 record) to 2027 (19 records). PMIDs run from 1 to
  42,671,487.
- **File numbers do not line up with the 2026 baseline.** `pubmed27n0001` holds exactly the
  records of `pubmed26n0001`, all from 1975-1979. `pubmed27n0656` shares none of
  `pubmed26n0656`'s records. Of those 30,000 records, 13,616 have a journal year before 1959, and
  none of them is anywhere in the sample. The other 16,384 are also not in the sample. Most likely
  they sit in an unsampled file nearby, because pre-1959 records were removed earlier in the order.
  The audit does not show where they went.

## Limits

- A 10% sample of files cannot show that something is absent from the whole corpus.
- The date counts use the journal issue date, the `ArticleDate` of type Electronic, and the
  PubMed history date as parsed by `audit.py`. Records with a 2026 journal year but no month
  (17,098) could not be placed inside or outside the window by journal date.
- This covers only the PubMed part. The PMC part (`Challenge_PMCIDs.txt`) was not on the
  challenge page on 2026-10-22.
- The job's raw output is committed next to this file as `results/summary.json` and
  `results/files.jsonl` (one line of counts per sampled file). The audit can be re-run with the
  command above.
