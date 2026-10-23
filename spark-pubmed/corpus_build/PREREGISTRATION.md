# Pre-registration: mirror repair, full count and first whole-corpus index build (job `spark32-build-v1`)

Written on 2026-10-23 at about 03:10 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

Job `spark27-fts-v3` (graded in `../fts_pilot/RESULTS.md`) mirrored all 1,306 SPARK PubMed
files and counted 1,304 of them. Two files, `pubmed27n1279.xml.gz` and `pubmed27n1281.xml.gz`,
failed with `EOFError: Compressed file ended before the end-of-stream marker was reached`. Both
were "resumed" from an earlier attempt: their `.md5ok` markers hold NLM's own md5 (the live
`.md5` file for 1279 reads `51f336e4085f408d0f42d10b5a0e54ea`, the same as its marker), but on
disk they are 27,262,976 and 25,165,824 bytes, exactly 26 and 24 MiB, while their neighbours
are 76-79 MB. Our reading: an earlier job was killed by the host after the rename and the
marker reached the disk but before all of the file's data did. That is an inference; nothing
here proves it.

`fetch_corpus.py` 0.2.2 now fsyncs each download before the rename and the marker, and
`--rehash` re-checks every marked file against its marker. `full_count.py` 0.2 also names the
duplicate PMIDs it finds. Their fake-data tests (`test_corpus_build.py`) run as the job's first
step, together with `../t1_runner/test_build_index.py`.

## Fixed design

1. Tests: `python -m unittest -v test_corpus_build test_build_index`.
2. Repair: `fetch_corpus.py --rehash --max-minutes 60 --allow-failed 0` on the same mirror.
3. Count: `full_count.py` with the same checkpoint folder, so only files without a checkpoint
   are read again.
4. Build: `build_index.py --detail full --max-minutes 240 --min-free-gb 100`, files in name order
   from `pubmed27n0001`. No optimize step. The job has 2 CPUs and 1.5 GB of memory.

`detail=full` was chosen after the pilot, not before (a post-hoc decision): on the comparison
files, `column` and `none` saved only 13% and 22% of the database size, gave the same title
MRR@5 (0.99), and made median title queries 18-19 times slower (566 and 548 ms against 30 ms).

## Predictions

Repair
- R1. The rehash flags exactly two stale markers, `pubmed27n1279` and `pubmed27n1281`. All
  other 1,304 marked files match their markers.
- R2. Both files download again and match NLM's md5, the fetch step reports 0 failed files, and
  each repaired file is between 60 and 95 MB.
- R3. The repaired mirror totals between 56.20 and 56.35 GB.

Count
- C7. All 1,306 files are counted without an error.
- C8. Each repaired file holds exactly 30,000 records, so the corpus holds exactly 39,167,524.
- C9. The whole corpus still has exactly 1 duplicate PMID.
- C10. Editorial (D016421) records total between 749,482 and 752,500, and Historical Article
  (D016456) records between 361,972 and 362,600.

Build (first 240 minutes)
- B1. The build stops on its time budget (`stopped` = "time budget"), so it is not complete,
  and it reports no problem.
- B2. It indexes at least 20,000,000 records within the budget.
- B3. Its `docs_per_second_this_run` is between 1,500 and 3,000.
- B4. Its `bytes_per_doc` (no optimize) is between 1,700 and 2,600.
- B5. `replaced_total` is at most 1.
- B6. The job's peak memory stays under 1.2 GB.

If the host stops the job before the build writes `build.json`, B1-B4 are reported as
ungraded, not as misses. Query speed on the whole corpus is not predicted here. It will be
pre-registered before the index is complete.

Contact: MV2, Munim, Inc., mv2@munimtech.com
