# corpus_build: repair the SPARK mirror, finish the count, build the whole-corpus index

Part of `spark-pubmed/`, the open groundwork that MV2 of Munim, Inc. is building for the NIH/NLM
SPARK PubMed/PMC Challenge. The code was made with AI agents working in his name. Code is
Apache-2.0; notes are CC BY 4.0.

## Files

- `fetch_corpus.py` 0.2.2 mirrors the 1,306 `.pubmed-spark` files and checks each one against
  NLM's `.md5`. Compared with 0.2.1 in `../fts_pilot/`, it fsyncs each download before the rename
  and the marker. Its `--rehash` option re-checks every marked file and downloads again any
  file that no longer matches.
- `full_count.py` 0.2 is the whole-corpus census. It names up to 20 duplicate PMIDs and the
  files that hold each one.
- `test_corpus_build.py` holds fake-data tests with no network.
- `PREREGISTRATION.md` and `RESULTS.md`: job `spark32-build-v1` (repair, full count, first
  index build). 7 predictions held, 1 missed, 6 ungraded because the host stopped the build.
- `results/`: that job's raw output.
- `PREREGISTRATION-spark33.md`, `RESULTS-spark33.md`, `results-spark33/`: job
  `spark33-build-v1`, which continued the build with `../t1_runner/build_index.py` 0.3 to 830
  of 1,306 files. 13 of 13 predictions held.
- `PREREGISTRATION-spark34.md`, `RESULTS-spark34.md`, `results-spark34/`: job
  `spark34-build-v1`, which finished the index (guarded by `../t1_runner/host_guard.py`) and
  timed 20 probe questions (`../t1_runner/query_probe.py`). 14 of 16 predictions held.

## Use

```
python fetch_corpus.py --rehash --data-dir raw --out-dir out --workers 4 --min-free-gb 30
python full_count.py --raw-dir raw --state-dir count --out-dir out --workers 2
python ../t1_runner/build_index.py --raw-dir raw --db spark_full.db --out-dir out --detail full
```

## Status (2026-10-23)

The corpus is counted in full: 39,167,524 records, 1 duplicate PMID (25973045, twice in
`pubmed27n0782.xml.gz`), 750,678 editorials and 362,068 historical articles.

The whole-corpus index is complete: 1,306 of 1,306 files and 39,167,523 records (the duplicate
kept once), 92.5 GB at `detail=full`, 2,362 bytes per record. It took three jobs on one host
(spark32's partial build on the other host is not used). Whole-corpus BM25 at depth 50 takes a
6.1 s median on a warm pass and 22.7 s at worst, against 30 ms on the 1.2-million-record pilot.
The first scoring job on the dev sets is pre-registered in
`../t1_runner/PREREGISTRATION-spark35.md`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
