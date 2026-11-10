# TelcoRetrieve Challenge (Zindi, ITU and GSMA): pre-launch notes

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text is CC BY 4.0 and code
is Apache-2.0. Everything here comes from public pages and files, read 2026-11-10 between 16:30 and 17:00 UTC,
with an addendum read between 20:45 and 21:15 UTC (marked below). The challenge opens 2026-11-13 12:00 UTC, and
the rules may change before then.

## The contest (from Zindi's public API)

- **Prize:** $20,000 (8,000 / 5,000 / 3,500 / 2,000 / 1,500).
- **Dates:** entries close 2027-01-06, submissions close 2027-01-13, private evaluation runs 15-31 January 2027.
- **Task:** answer questions grounded in 3GPP standards.
- **Required models:**
  - generator `google/gemma-3n-e4b-it`
  - embedder `farbodtavakkoli/OTel-Embedding-300M`
  - reranker `farbodtavakkoli/OTel-Reranker-0.6B`
  - Fine-tuning them is allowed.
- **Data:** only the provided datasets may be used. There is an 80% accuracy floor. Each team gets 10
  submissions a day.

## Things that do not line up yet (worth asking about once the forum opens)

1. **Embedder name.** Zindi names `OTel-Embedding-300M`, a fine-tune of `google/embeddinggemma-300m` with
   768 dimensions. GSMA's suggested starting index, `fixed-grid/text_baseline/otel-0.6b`, was built with
   `farbodtavakkoli/OTel-Embedding-0.6B` according to its own `ingest.log`. That repo id now resolves to
   `OTel-Embedding-600M`, a fine-tune of `Qwen/Qwen3-Embedding-0.6B` with 1,024 dimensions. None of the 18
   base cells is labelled as built with the 300M OTel model. The closest, `embeddinggemma-300m-fp32`, is named
   after the base Gemma embedder.
2. **Public/private split.** The summary says about 30/70, the full rules about 20/80.
3. **Team size.** The rules say up to 4 members. The API metadata says 3 and `allow_teams: false`.
4. **Metric.** The API's metric field is `character_error_rate`, while the text describes an accuracy score
   with token efficiency. No formula is published yet.
5. **Pipeline code and questions.** `Znbne/telco-retrieve` (the `open-telco-rag` package the indexes were
   built with) returns 404 on GitHub (checked again 2026-11-10 ~21:00 UTC). The Hugging Face collection linked
   from the contest page returns 401, and so does `GSMA/telco-retrieve-QnA`. All three are probably private
   until launch. No `Test.csv` or question set is public yet.
6. **Prize pool.** ITU's AI for Good event page gives the pool as €25,000, while Zindi gives $20,000. ITU
   lists a launch webinar on 13 November 2026 at 14:00 CET.

## The prebuilt indexes (`GSMA/telco-retrieve-chunks`, folder `telcoretrievechallenge/`)

- 18 base cells (3 chunking strategies x 6 embedders), each 7.15-10.26 GB. Each cell is a Chroma store with
  cosine distance plus an SQLite FTS5 (BM25) database, built from `GSMA/3GPP` Release 19 (1,557 files).
- 36 enriched cells (406 GB) and 18 cells with 8B embedders.
- `archive/` (about 1 TB) is not part of the challenge.
- The text is verbatim 3GPP material, and the dataset's own licence is still "to be decided by GSMA".

## Addendum (read 2026-11-10, 20:45-21:15 UTC): what the cells' own verification reports say

Each cell ships `command.txt` (the exact ingest command) and `_COMPLETE.json` (a 16-check verification
report). We read both for two text_baseline cells, `otel-0.6b` and `embeddinggemma-300m-fp32`, and listed the
other two strategies' folders. The short version: the indexes are carefully built, and two common worries do
not apply.

- **No silent truncation.** Chunks are bounded at 510 `tiktoken cl100k_base` tokens, and the build re-checks
  every chunk against each embedder's own tokenizer limit (`--bound-verify minilm=256, bge=512, bge-m3=512,
  qwen3-embedding-0.6b=512, embeddinggemma-300m=512`, outliers split). Both reports show `over_limit: 0` for all
  1,072,821 chunks; the longest are 254 (MiniLM, limit 256), 504 (bge-m3) and 510 (Qwen3, Gemma) tokens.
  (The fixed-grid README warns that 23-58% of the *enriched* chunks exceed MiniLM's 256 limit; this is about the
  base cells only.)
- **EmbeddingGemma was built in float32.** EmbeddingGemma does not support float16 activations. All three
  strategies name their Gemma cell `embeddinggemma-300m-fp32`, and the text_baseline report records
  `torch.float32`, 768 dimensions, `max_seq_length` 2048. The `otel-0.6b` cell was built in `torch.float16` on
  `cuda:0` with `max_seq_length` 1024 and 1,024 dimensions (about 510 chunks/s, 2,104 s).
- **Counts agree.** Chroma, the FTS table, its distinct ids and the Chroma ids in SQLite all hold 1,072,821
  chunks, all 1,557 files are present (spec 25331 is the one expected, error-only gap), 10,000 sampled vectors are
  finite, and the code is `open-telco-rag` 0.1.0 at commit `fdda5839`, clean.
- **One label to ignore.** The first check is named `chunk_count_is_1086324` and reads `true`, while every count
  in the same report is 1,072,821 (13,503 fewer). The name looks stale; the counts themselves agree with each
  other.
- **The command shows no prompt flag.** Neither `command.txt` passes anything about query or document prompts,
  so they do not settle the open question below.

## Open question under test: embcheck-1

The OTel embedder's sentence-transformers config sets `default_prompt_name = "Retrieval-query"`. Code that
calls `model.encode(passages)` without a prompt name therefore adds the query instruction to every passage.
This is a known trap; see sentence-transformers PRs #4095 and #4110. The default cell's ingest log prints the
library's notice about this default. The notice alone does not prove that passages were prefixed, and the
ingest code is not public.

[PREREGISTRATION-embcheck1.md](PREREGISTRATION-embcheck1.md) tests it from the stored vectors themselves:
- It reads 100 random vectors from the default cell's HNSW file with HTTP range requests.
- It looks up their text and re-encodes each passage on CPU with and without the instruction.
- It runs the same check on the base-model cell `qwen3-embedding-0.6b` as a control.

Code: [telco_embcheck.py](telco_embcheck.py), with offline tests in
[test_telco_embcheck.py](test_telco_embcheck.py). Results will be added here when the job finishes.

A note on timing: the pre-registration was written on 2026-11-10 before 16:40 UTC. Our first attempt to
publish it, at 16:40 UTC, failed with a GitHub HTTP 504, so it was sent again unchanged about 21:15 UTC. The job
had not started by then: it was still waiting in the compute queue, and it does not read any stored vector until
the public copy matches the local one byte for byte.

The same file sizes also show something about the default cell's HNSW graph. `data_level0.bin` has room for
1,064,960 vectors (at 4,236 bytes each), fewer than its 1,072,821 chunks. The verification report (read after
the pre-registration was written) counts 1,072,821 Chroma ids in SQLite, so the remaining ~7,900 are most likely
held in Chroma's write-ahead queue and added to the graph when the collection loads. This is noted here, not
claimed as a defect; embcheck-1's E1 only reads the persisted header.
