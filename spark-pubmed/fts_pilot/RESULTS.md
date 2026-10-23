# Results: SPARK corpus mirror, SQLite FTS5 pilot and whole-corpus count

Graded on 2026-10-23 (about 03:00 UTC) by AI agents working in the name of MV2 of Munim, Inc.,
against `PREREGISTRATION.md` in this folder, word for word, misses included. CC BY 4.0.

**11 of 16 predictions held** (F 2/2, Q 4/8, C 5/6). C1 and C2 are graded on 1,304 of the
1,306 files (see "What failed").

## What ran

The predictions were written for job `spark27-fts-v1`. That job and `spark27-fts-v2` failed
before producing results: v1 stalled on one download, and in v2 the job's own tests failed. The
graded job is `spark27-fts-v3`: same design and same predictions, with only the download code
fixed (`fetch_corpus.py` 0.2.1). It ran on the Blade from 2026-10-22 23:16 to 2026-10-23
01:18 UTC (2 CPUs, 1.5 GB). Tests, mirror, pilot and count all ran. The count step exited 1
because two files failed. Raw output: `results/` (`fetch.json`, `fetch_files.jsonl`,
`pilot.json`, `full_count.json`, `full_files.jsonl`).

## Grades

| # | Prediction | Result | Grade |
|---|---|---|---|
| F1 | All 1,306 files download and match their `.md5` | 1,306 ok, 0 failed (1,280 resumed from earlier attempts, 26 downloaded) | held (see "What failed") |
| F2 | Mirror 50-62 GB | 56,143,787,546 bytes (56.1 GB) | held |
| Q1 | 1.0-3.0 KB/doc; full corpus 40-120 GB | 2,259.8 bytes/doc over 1,199,999 docs; 88.5 GB extrapolated | held |
| Q2 | `column` >= 20% and `none` >= 35% smaller than `full` | 12.8% and 21.8% smaller (217.1 / 189.2 / 169.8 MB compacted) | **missed** |
| Q3 | Title MRR@5 >= 0.95 | 0.9861 (hit@1 0.98) | held |
| Q4 | Median title query < 250 ms | 446.3 ms (p90 813.8) | **missed** |
| Q5 | First-sentence MRR@5 0.50-0.90 | 0.9629 | **missed** (higher) |
| Q6 | `column` title MRR@5 within 0.02 of `full` | 0.99 and 0.99 | held |
| Q7 | Build >= 1,000 docs/s | 2,500 docs/s | held |
| Q8 | Job peak memory < 1.0 GB | 1.14 GB (job total; the pilot step's own peak RSS was 32.7 MB) | **missed** |
| C1 | 39.1-39.2 M records | 39,107,524 in 1,304 files | held (the other two files would need over 92,476 records between them to break it) |
| C2 | No Preprint records | 0 | held (1,304 files) |
| C3 | No PMID appears twice | 1 duplicate PMID | **missed** |
| C4 | Editorial >= 100,000 and Historical Article >= 10,000 | 749,482 and 361,972 | held |
| C5 | Fewer than 100 journal years before 1959 | 1 | held |
| C6 | Fewer than 4,000 with no journal or electronic date on or before 2026-07-31 | 29 | held |

## What this shows

1. **The published corpus does not apply the announcement's exclusion.** The challenge
   announcement says "Editorials, historical articles, and some content irrelevant to the task
   will be excluded." In the published PubMed files, 749,482 records (1.9%) carry publication type
   Editorial (D016421) and 361,972 (0.9%) carry Historical Article (D016456). So do 1,345,188
   Letters, 1,069,171 Comments, 231,891 News items, 205,013 Published Errata and 32,366
   Retraction Notices. The corpus does follow the task descriptions, which exclude only
   preprints: there are 0 Preprint records. Teams that drop editorials because of the
   announcement would be dropping documents that are in the corpus. Whether such records can
   be correct answers is a question only the organisers can settle.
2. **The date window is loose, as the 10% audit found.** 11,544 records have a journal date
   after July 2026 and 29,751 entered PubMed after July 2026, yet only 29 have neither a journal
   date nor an electronic date on or before 2026-07-31. One record has a journal year before 1959.
3. **Corpus shape.** 74.2% of records have an abstract and 27.9% a PMC id. PMIDs run from 1 to
   42,671,487. 1,290 of the 1,304 counted files hold exactly 30,000 records.
4. **FTS5 detail level: keep `full`.** On the comparison files, `column` and `none` save only
   13% and 22% because the stored text dominates the file. Of 2.71 GB in the pilot, 1.46 GB is
   text and 0.72 GB is the index. Ranking is the same (title MRR@5 0.99 at all three levels),
   but median title queries are 18-19 times slower (566 and 548 ms against 30 ms on 90,000
   docs). A likely reason is that bm25 needs per-column term counts that only `full` stores
   ready to use. That reason was not tested here.
5. **Query time is the cost to watch.** Median title-query time grew from 30 ms on 90,000 docs
   to 446 ms on 1.2 million: about linear, as expected for OR queries of up to 32 terms.
   Straight-line extrapolation (not measured) gives about 15 s per query on all 39 million
   records, about 50 minutes for 200 questions. That is workable offline, and shorter queries
   or term pruning should cut it. Size (88.5 GB) and build speed are not the bottleneck.
6. **The self-retrieval checks are only pipeline checks.** A paper's own title or first
   sentence finds it 96-99% of the time. Real SPARK questions will be much harder.

## What failed

The count read 1,304 of 1,306 files. `pubmed27n1279.xml.gz` and `pubmed27n1281.xml.gz` failed
with `EOFError: Compressed file ended before the end-of-stream marker was reached`. Both had been
resumed from an earlier attempt with a valid `.md5ok` marker, and the marker for 1279 holds the
same md5 as NLM's live `.md5` file. On disk, though, they are 27,262,976 and 25,165,824 bytes
(exactly 26 and 24 MiB), while their neighbours are about 76-79 MB. So F1 held as worded (every
file matched its md5 when it was downloaded), but the mirror was not whole when it was read.
The likely cause is that a host kill lost data that had not yet been written to disk. That is
not proven. The fix and the repair job are in `../corpus_build/`.

C3's duplicate PMID is not named in this output. `full_count.py` 0.2 names it.

## Limits

- No real SPARK questions exist yet, so nothing here measures retrieval quality on them.
- The pilot indexed every 33rd file (40 files). Size and speed are extrapolated, not measured.
- The predictions were written for v1 and graded on v3, with the same design. The 1,280 files
  resumed in v3 were downloaded by v1 and v2 with the same md5 check.

Contact: MV2, Munim, Inc., mv2@munimtech.com
