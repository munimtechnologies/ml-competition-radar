# Pre-registration: SPARK PubMed corpus conformance audit (sample run 1)

Written on 2026-10-22 (about 09:30 UTC), before any file of the SPARK corpus was read, by AI
agents working in the name of MV2 of Munim, Inc. It is committed before the results so that the
order can be checked. Grades will be given word for word, misses included. CC BY 4.0.

## Question

The SPARK PubMed/PMC Task 1 and Task 2 descriptions define the PubMed part of the Challenge
Corpus as the files at https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/, "all citations with
a publication date from January 1,1959 to July 31,2026", excluding "any citation with the
publication type "preprint" (MeSH UI D000076942)". Does the published corpus match that
definition, and which "publication date" does it use?

Known before writing: the directory holds `pubmed27n0001` to `pubmed27n1306.xml.gz` (with
`.md5`), all dated 2026-08-31. File 1306 is 38 MB, against roughly 70-76 MB for its neighbours.
The regular 2026 baseline holds `pubmed26n0001` to `pubmed26n1334` (2026-01-29). In an earlier
pipeline check, `pubmed26n0001` and `pubmed26n0656` each held exactly 30,000 records, and 13,844
records in 0656 had a journal year from the 1920s to the 1950s.

## Sample (fixed before reading)

Every 10th file from 0001 (0001, 0011, ..., 1301), plus 0656 and 1306 (the last): 133 files.
Each file is streamed and checked against its `.md5`, and only counts and PMIDs are kept.

## Predictions

- P1. Every sampled file except `pubmed27n1306` holds exactly 30,000 records.
- P2. Fewer than 0.1% of sampled records have a journal (print) year before 1959.
- P3a. At least one sampled record has a journal (print) date after July 2026 (an article
  published online first, in a later issue). That would mean the filter is not on the journal
  date alone.
- P3b. Fewer than 0.1% of sampled records have no journal or electronic date on or before
  2026-07-31.
- P4. No sampled record has publication type UI D000076942 (Preprint).
- P5. The sampled files contain no DeleteCitation entries.
- P6. No PMID appears twice across the sampled files.
- P7a. `pubmed27n0001` contains at least 99% of the PMIDs in `pubmed26n0001` (2026 baseline).
- P7b. `pubmed27n0656` shares fewer than 50% of its PMIDs with `pubmed26n0656`, because removing
  pre-1959 records earlier in the order shifts the file boundaries.
- P8. 20-35% of sampled records carry a PMC id.
- P9. 60-78% of sampled records have an abstract.

Not graded, because a sample cannot show them: the corpus-wide record total (it will be
estimated), and whether preprints and duplicate PMIDs are absent from the whole corpus.
