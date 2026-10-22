# spark-pubmed: groundwork for the NIH/NLM SPARK PubMed/PMC Challenge

Open groundwork for the NIH/NLM SPARK PubMed/PMC Challenge (Task 1, Known-Item & Provenance
Retrieval), by MV2 of Munim, Inc. The code and notes were made with AI agents working in his
name. Code: Apache-2.0 (the repository's `LICENSE`). Notes and data: CC BY 4.0.

This folder sits inside `ml-competition-radar`. It was planned as a separate repository,
`spark-pubmed-retrieval`, but GitHub refused to create that repository twice on 2026-10-22
("secondary rate limit"), so the work is published here instead.

## What is here now

`corpus_audit/` checks the PubMed part of the challenge corpus against the challenge's own
definition. The Task 1 and Task 2 descriptions say the PubMed files are at
https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/ and that the corpus "includes all citations
with a publication date from January 1,1959 to July 31,2026 and excludes any citation with the
publication type "preprint" (MeSH UI D000076942)". On 2026-10-22 that directory listed
`pubmed27n0001.xml.gz` to `pubmed27n1306.xml.gz`, all dated 2026-08-31. NLM's regular 2026
baseline has `pubmed26n0001` to `pubmed26n1334`.

PubMed records carry several dates (the journal issue date, the electronic publication date,
the date the record entered PubMed), and the definition does not say which one it uses. The
audit counts, per file: records, records outside the window by each date, preprint-type
records, DeleteCitation entries, PMC ids and abstracts. It also checks for duplicate PMIDs and
compares two files with their 2026-baseline counterparts.

- `corpus_audit/audit.py`: Python standard library only. It streams each chosen file from NLM,
  checks it against its `.md5` file and keeps only counts and PMIDs. Nothing downloaded is kept
  or executed. A rerun resumes from its checkpoints.
- `corpus_audit/test_audit.py`: tests on fake data, with no network.
- `corpus_audit/PREREGISTRATION.md`: the eleven predictions written before any corpus file was
  read. The first run samples 133 of the 1,306 files: every 10th file, plus 0656 and the last one.
- `corpus_audit/RESULTS.md`: the graded results. `corpus_audit/results/`: the run's raw output.

Run (from `spark-pubmed/`): `python corpus_audit/audit.py --data-dir <scratch> --out-dir <out>
--stride 10 --also 0656`.

`fts_pilot/` is the next step. It mirrors the whole corpus (md5-checked, resumable) and measures
whether an on-disk SQLite FTS5 (BM25) index, built with the standard library only, can hold all
of it on one CPU machine. It measures bytes per document, build speed, query speed, and the
size/ranking trade-off of FTS5's three detail levels. The same job then counts every record of
the mirror, including every publication type, to test a sentence of the challenge announcement:
"Editorials, historical articles, and some content irrelevant to the task will be excluded."
The task descriptions exclude only preprints. The predictions are in
`fts_pilot/PREREGISTRATION.md`, written before the job ran.

- `fts_pilot/fetch_corpus.py`: md5-checked, resumable mirror of all 1,306 files.
- `fts_pilot/fts_pilot.py`: the FTS5 size and speed pilot.
- `fts_pilot/full_count.py`: whole-corpus record count with per-file checkpoints.
- `fts_pilot/test_fts_pilot.py`: tests on fake data, with no network. They passed as the first
  step of the sealed job `spark27-fts-v1` on 2026-10-22.

`dev_sets/` builds two practice question sets, because no SPARK questions are public yet and a
search found no public known-item benchmark over PubMed:

- `dev_sets/landmarks.json`: 47 well-known first reports since 1959 (CRISPR-Cas9, PCR, iPS
  cells, BLAST, HIV, and others), each with a plain-language question, plus four pre-1959
  controls. Titles and years were recalled and are only hints: `dev_sets.py` keeps an item only
  if PubMed's own record (NCBI E-utilities) has a near-identical title and year.
- `dev_sets/dev_sets.py`: the lookups, and a fixed-seed sample of 90 records with abstracts from
  six evenly spaced corpus files, for questions written later from the abstracts alone.
- `dev_sets/test_dev_sets.py`: tests on fake data, with no network.
- `dev_sets/PREREGISTRATION.md`: predictions for the lookups and for later BM25 scores, written
  before anything was looked up.

## Status

The first audit run is done and graded: 10 of 11 predictions held (`corpus_audit/RESULTS.md`).
In a 133-file sample (3,977,567 records), the corpus matches its definition closely:

- no preprint-type records, no deletions and no duplicate PMIDs;
- only 1 record with a journal year before 1959.

The date window is not applied to one date field. Records with a journal date, an electronic
date or a PubMed entry date after July 2026 are all included, and only 3 records have neither
a journal nor an electronic date inside the window. That reading is an inference from counts.

The whole PubMed part is estimated at about 39.17 million records, roughly 56 GB compressed.
One miss: file `pubmed27n0851` holds 29,999 records, not 30,000.

The FTS5 pilot job started on 2026-10-22 at 10:47 UTC and was still running when this folder
was first published. Nothing in `fts_pilot/` is a finding until its results are graded here.
The dev-set lookups (`dev_sets/`) were queued on 2026-10-22 at about 14:50 UTC and are ungraded.

## Limits

- A 10% sample of files cannot show that something is absent from the whole corpus. A zero in
  the sample is evidence, not proof.
- This covers only the PubMed part. The PMC part is defined by a `Challenge_PMCIDs.txt` list,
  which was not on the challenge page on 2026-10-22.
- NIH's general challenge page describes the PMC part as about 50,000 CC0 articles. The task
  descriptions describe a Creative Commons, NIH-funded subset. Only the task descriptions were
  used here.
- No SPARK questions have been published, so nothing here measures retrieval quality on them.
  The dev sets are AI-written proxies, not NLM's expert questions.

Contact: MV2, Munim, Inc., mv2@munimtech.com
