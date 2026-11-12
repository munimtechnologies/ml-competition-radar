# TelcoRetrieve Challenge (Zindi, ITU and GSMA): pre-launch notes

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text is CC BY 4.0 and code
is Apache-2.0. Everything here comes from public pages and files, read 2026-11-10 between 16:30 and 17:00 UTC,
with an addendum read between 20:45 and 21:15 UTC, study results from 2026-11-11 and 2026-11-12 and a scoring
analysis read 2026-11-11 between 12:10 and 12:40 UTC, updated between 18:15 and 18:40 UTC (marked below). The
contest facts were re-read from Zindi's public API on 2026-11-12 around 20:55 UTC. The challenge opens
2026-11-13 12:00 UTC, and the rules may change before then.

## New (2026-11-12): the 254-character chunks are not hubs. Dense retrieval almost never returns them

[RESULTS-embcheck2.md](RESULTS-embcheck2.md), pre-registered in
[PREREGISTRATION-embcheck2.md](PREREGISTRATION-embcheck2.md). **No prediction is graded.** The
pre-registration needed 300 3GPP-tagged public questions, and GSMA's `ot-lite` TeleQnA test file has only 191.
The numbers are therefore exploratory, but they are clear. Chunks exactly 254 characters long make up 8-9% of
10,000 sampled vectors in both the default `otel-0.6b` cell and the base `qwen3-embedding-0.6b` cell, yet they
took **0-4 of 1,910 top-10 slots** (158-175 expected), whether questions were encoded with or without the
query instruction. Chunks shorter than 254 characters got about their fair share. So the pre-registered worry
(instruction-dominated chunks crowding the top 10) is not supported, and the gap shows up in the cleanly built
control cell too.

Also exploratory: in the base Qwen3 cell, questions encoded *without* its query instruction make one chunk
appear in 42 of 191 top 10s. Use the instruction there.

Next: [PREREGISTRATION-embcheck3.md](PREREGISTRATION-embcheck3.md) describes these chunks from the full chunk
tables (how many there are, whether they come in runs within a document, what kind of text they hold).
Code: [telco_embcheck3.py](telco_embcheck3.py) with offline tests in
[test_telco_embcheck3.py](test_telco_embcheck3.py). It is queued and has not run yet.

## Updated (2026-11-11 ~18:30 UTC): the scoring rule, and why short prompts win

The challenge's pipeline repository [`Znbne/telco-retrieve`](https://github.com/Znbne/telco-retrieve) is
public (Apache-2.0). Its challenge docs, updated at commit `a9b61be6` (2026-11-11 16:01 UTC), give the score as
**Overall = 0.7 x Accuracy + 0.3 x Token efficiency**, with token efficiency = 100 x B / (B + T), **B = 850
tokens per question** and T the prompt tokens (`cl100k_base`), equivalently 100 x 850 / (850 + mean
`input_prompt` tokens). There is an 80% accuracy floor and a 4,096-token prompt cap. Our first reading
(12:40 UTC, commit `075feaa3`) used the kit code's earlier B = 2,000, which that code still marks "proposed,
not confirmed". (2026-11-12 20:55 UTC: `a9b61be6` is still the kit's newest commit.)

With B = 850, 80% accuracy with 300-token prompts (78.17) beats 95% with 2,000-token prompts (75.45), and going
from 300 to 2,000 mean tokens has to buy 18.9 accuracy points to break even (15.8 with B = 2,000). 100 more mean
tokens now cost 2.5 accuracy points at 300 tokens (1.6 before). Details, the full table and what it implies for
retrieval design: [SCORING.md](SCORING.md); calculator: [score_tradeoff.py](score_tradeoff.py)
(`--baseline` to change B).

The same commit moved the question set to the Zindi challenge page (`Test.csv`, Data tab) instead of Hugging
Face.

## Result (2026-11-11): the default index's passages carry the query instruction

[RESULTS-embcheck1.md](RESULTS-embcheck1.md), pre-registered in
[PREREGISTRATION-embcheck1.md](PREREGISTRATION-embcheck1.md): all 100 randomly sampled stored vectors of the
suggested starting cell `text_baseline/otel-0.6b` match their passage encoded *with* the OTel embedder's query
instruction, and none match the plain encoding. All 40 sampled vectors of the base-model control cell
`qwen3-embedding-0.6b` match the plain encoding. 3 of 5 predictions held (E2-E4); E1 failed as worded
(`max_elements` is 2,097,152, though the graph does hold 1,064,960 vectors, fewer than the 1,072,821 chunks)
and E5 failed (the instruction moves most passages only a little, median cosine 0.962).

For most passages the effect is small. For 16 of 100 it is large (cosine 0.51-0.67 between the stored vector
and the plain encoding), and 13 of those 16 are chunks exactly 254 characters long. embcheck-2 (above) then
tested whether those chunks crowd the top 10. (2026-11-11: the starter kit's default `otel-0.6b` setup encodes
questions with plain `encode()`, so they get the same default prompt as the passages; that is embcheck-2's "Q"
setting.)

## The contest (from Zindi's public API, re-read 2026-11-12 ~20:55 UTC)

- **Prize:** Zindi's reward field now reads **€25,000** (it read $20,000 before). The cash places are
  8,000 / 5,000 / 3,500 / 2,000 / 1,500 (the page labels them both "€" and "USD"; the rules say winners are paid
  "in USD or the currency of the challenge"). The top three also each get an MWC Barcelona Leader Pass (given as
  worth €2,000) and up to 1,500 towards the costs of attending MWC Barcelona in March 2027.
- **Dates:** opens 2026-11-13 12:00 UTC; entries close 2027-01-06 23:59; submissions close 2027-01-13 22:25;
  the contest ends 22:55. Phase 1 (public evaluation) runs 13 November 2026 - 13 January 2027 and Phase 2
  (private evaluation) 15-31 January 2027, with AMD GPU instances available from 15 January 2027.
- **Task:** answer questions grounded in 3GPP standards.
- **Required models:**
  - generator `google/gemma-3n-e4b-it`
  - embedder `farbodtavakkoli/OTel-Embedding-300M`
  - reranker `farbodtavakkoli/OTel-Reranker-0.6B`
  - Fine-tuning them is allowed; other pretrained models only if openly available to everyone.
- **Data and tools:** only the provided datasets may be used. AutoML tools are not permitted, nor paid services
  or free trials that need a credit card. The rules do not mention AI-assisted code.
- **Limits:** an 80% accuracy floor (below it a submission is disqualified); 10 submissions a day, 300 in total.
- **Metric on Zindi:** listed as "multi" (token efficiency and accuracy). The page itself gives no formula, B or
  token cap; those come from the starter kit (above).

## Things that do not line up yet (worth asking about once the forum opens)

1. **Embedder name.** Zindi names `OTel-Embedding-300M`, a fine-tune of `google/embeddinggemma-300m` with
   768 dimensions. GSMA's suggested starting index, `fixed-grid/text_baseline/otel-0.6b`, was built with
   `farbodtavakkoli/OTel-Embedding-0.6B` according to its own `ingest.log`. That repo id now resolves to
   `OTel-Embedding-600M`, a fine-tune of `Qwen/Qwen3-Embedding-0.6B` with 1,024 dimensions. None of the 18
   base cells is labelled as built with the 300M OTel model. The closest, `embeddinggemma-300m-fp32`, is named
   after the base Gemma embedder. (2026-11-11: the starter kit's challenge profile also defaults to
   `otel-0.6b`, and its registry lists `otel-300m` with 1,024 dimensions.)
2. **Public/private split.** The summary says about 30/70, the full rules about 20/80 (still so on 2026-11-12).
3. **Team size.** The rules say up to 4 members. The API metadata says 3 and `allow_teams: false`.
4. **Metric.** *Resolved 2026-11-11 by the starter kit:* 0.7 x accuracy + 0.3 x token efficiency, see
   [SCORING.md](SCORING.md). Zindi's API metric field read `character_error_rate` on 2026-11-11 and reads
   "multi" (token efficiency, accuracy) on 2026-11-12. *Open mismatch (2026-11-11 18:30 UTC):* the kit's docs
   give B = 850, its scorer code still uses 2,000 ("proposed, not confirmed").
5. **Pipeline code and questions.** *Code resolved 2026-11-11:* `Znbne/telco-retrieve` is public
   (Apache-2.0). *Questions (18:30 UTC):* the kit's docs now point to `Test.csv` on the Zindi challenge page
   (columns `ID,question,options`, no answers) instead of `GSMA/telco-retrieve-QnA` on Hugging Face.
6. **Prize pool.** *Mostly resolved 2026-11-12:* Zindi's reward field now says €25,000, matching ITU's AI for
   Good event page. The listed cash places still add up to 20,000, and the page mixes "€" and "USD" labels.
   ITU lists a launch webinar on 13 November 2026 at 14:00 CET.
7. **Query instruction on passages** (2026-11-11): see the result above.

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
- **The command shows no prompt flag.** Neither `command.txt` passes anything about query or document prompts.

The persisted HNSW graph of the default cell holds 1,064,960 vectors (embcheck-1 read its header: exactly
65 x 16,384), fewer than its 1,072,821 chunks. The verification report counts 1,072,821 Chroma ids in SQLite,
so the remaining 7,861 are most likely held in Chroma's write-ahead queue and added to the graph when the
collection loads. This is noted here, not claimed as a defect.

## Files

- `SCORING.md`, `score_tradeoff.py`, `test_score_tradeoff.py` (2026-11-11, version 2 at 18:30 UTC with
  B = 850): the scoring rule and its arithmetic (standard library only).
- `telco_embcheck.py` 0.1.0, `test_telco_embcheck.py`, `requirements.txt`: embcheck-1.
- `embcheck1.json`, `RESULTS-embcheck1-auto.md`, `prereg_public_embcheck1.json`: its machine output and its
  proof that the pre-registration was public first.
- `telco_embcheck2.py` 0.2.0, `test_telco_embcheck2.py`, `fetch_base_embcheck2.py`, `wait_public.py`:
  embcheck-2 (it downloads `telco_embcheck.py` unchanged from commit 4717478).
- `RESULTS-embcheck2.md`, `embcheck2.json`, `RESULTS-embcheck2-auto.md`, `prereg_public_embcheck2.json`,
  `base_files_embcheck2.json` (2026-11-12): embcheck-2's write-up, machine output and proofs.
- `PREREGISTRATION-embcheck3.md`, `telco_embcheck3.py` 0.3.0, `test_telco_embcheck3.py` (2026-11-12):
  embcheck-3, standard library only. It reuses `wait_public.py` unchanged.
