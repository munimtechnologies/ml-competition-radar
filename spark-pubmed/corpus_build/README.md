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
- `PREREGISTRATION-spark33.md`: predictions for job `spark33-build-v1`, which continues the
  build with `../t1_runner/build_index.py` 0.3. It fetches the three files above at a pinned
  commit (`pull_pinned.py`, checked by git blob sha1).

## Use

```
python fetch_corpus.py --rehash --data-dir raw --out-dir out --workers 4 --min-free-gb 30
python full_count.py --raw-dir raw --state-dir count --out-dir out --workers 2
python ../t1_runner/build_index.py --raw-dir raw --db spark_full.db --out-dir out --detail full
```

## Status (2026-10-23)

The corpus is counted in full: 39,167,524 records, 1 duplicate PMID (25973045, twice in
`pubmed27n0782.xml.gz`), 750,678 editorials and 362,068 historical articles. The index build is
continuing in `spark33-build-v1`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
