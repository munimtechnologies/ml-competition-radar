# speed: faster BM25 queries on the whole SPARK PubMed index

Part of `spark-pubmed/`, MV2 of Munim, Inc.'s open groundwork for the NIH/NLM SPARK PubMed/PMC
Challenge. The code was made with AI agents working in his name. Code Apache-2.0; notes CC BY 4.0.

## Why

On the whole index (39,167,523 records, 92.5 GB, SQLite FTS5), one BM25 query took a median
35.4 s on the R dev set, 27.2 s on headline L and 15.8 s on the 65 TREC 2024 BioGen questions
(`../t1_runner/RESULTS-spark35.md`, `../t2/RESULTS-t2dev.md`). Compute time is one of the
challenge's tie-breakers.

## Files

- `prune.py` 0.1.0: re-runs a `t1.py` ranked.jsonl's questions with only the words found in 1 to
  `--max-df` records (each word's record count is probed once per run, capped at max-df + 1
  rows). If fewer than 2 words survive, the question runs with all its words ("fallback"). Writes
  ranked.jsonl in `t1.py`'s format, so `t1.py score` applies unchanged, and run.json with probe
  and query times, fallbacks, and top-1 and top-5 agreement with the input baseline. Standard
  library only.
- `test_prune.py`: 6 fake-data tests on a five-record FTS5 index (no network).
- `PREREGISTRATION.md`: predictions for job `spark37-speed-v1` (caps of 400,000 and 2,000,000
  records on R, L and BioGen), written before the job was filed.
- `PREREGISTRATION-spark37-addendum.md`: the one change made for `spark37-speed-v3` before it
  ran (memory ask 2 GB to 4.5 GB, so the job waits for the machine that holds the index); V10 is
  withdrawn and replaced by V10b.

## Use

```
python prune.py --db spark_full.db --needs out_r/ranked.jsonl --out-dir p400k_r --max-df 400000
python t1.py score --ranked p400k_r/ranked.jsonl --gold dev/gold.jsonl --out-dir p400k_r
```

## Status (2026-10-24)

The pre-registration was committed at 05:42:38 UTC (commit `5abdd686`). `spark37-speed-v1` and
`spark37-speed-v2` were both placed on the Dell, which holds only a partial copy of the index
(112 of 1,306 files), and `host_guard` stopped each one with exit 3 before any query ran (v2 at
08:35 UTC): check K1, "premise not met", as pre-registered. Nothing was graded. The compute runner
picks the machine with the most memory left after a job's expected use, and with the Blade's two
slots full the Dell took the small 2 GB ask. `spark37-speed-v3` therefore asks for 4.5 GB, with
nothing else changed; see `PREREGISTRATION-spark37-addendum.md`. Results will be graded in
`RESULTS-spark37.md`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
