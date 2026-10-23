# corpus_build: repair the SPARK mirror, finish the count, build the whole-corpus index

Part of `spark-pubmed/`, the open groundwork that MV2 of Munim, Inc. is building for the NIH/NLM
SPARK PubMed/PMC Challenge. The code was made with AI agents working in his name. Code is
Apache-2.0; notes are CC BY 4.0.

## Files

- `fetch_corpus.py` 0.2.2 mirrors the 1,306 `.pubmed-spark` files and checks each one against
  NLM's `.md5`. Compared with 0.2.1 in `../fts_pilot/`, it fsyncs each download before the rename
  and the marker. Its `--rehash` option re-checks every marked file and downloads again any
  file that no longer matches. The fix exists because two marked files were found cut short on
  disk (`../fts_pilot/RESULTS.md`, "What failed").
- `full_count.py` 0.2 is the whole-corpus census. Compared with 0.1, it names up to 20 duplicate
  PMIDs and the files that hold each one. It still reads 0.1's per-file checkpoints.
- `test_corpus_build.py` holds fake-data tests with no network, including a mirror file cut
  short behind a valid marker.
- `PREREGISTRATION.md` holds the predictions for job `spark32-build-v1`, written before the job
  was filed. That job runs four steps: tests, repair, count, then the first 240 minutes of the
  whole-corpus index build with `../t1_runner/build_index.py` (`detail=full`).

## Use

```
python fetch_corpus.py --rehash --data-dir raw --out-dir out --workers 4 --min-free-gb 30
python full_count.py --raw-dir raw --state-dir count --out-dir out --workers 2
python ../t1_runner/build_index.py --raw-dir raw --db spark_full.db --out-dir out --detail full
```

## Status (2026-10-23)

Job `spark32-build-v1` was filed on 2026-10-23 at about 03:15 UTC. Its tests run as its first
step. Nothing here has been graded yet.

Contact: MV2, Munim, Inc., mv2@munimtech.com
