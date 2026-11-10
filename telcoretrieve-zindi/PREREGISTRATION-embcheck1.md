# Pre-registration: embcheck-1. Were the passages in TelcoRetrieve's default index embedded with the query instruction?

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-11-10 ~17:00 UTC by AI agents working in his name,
before the job ran and before any stored vector was read. Text CC BY 4.0; code Apache-2.0.

## Why

Zindi's TelcoRetrieve Challenge (ITU and GSMA, $20,000, opens 2026-11-13) gives every entrant prebuilt
retrieval indexes over 3GPP Release 19 in `GSMA/telco-retrieve-chunks`. The suggested starting cell is
`telcoretrievechallenge/fixed-grid/text_baseline/otel-0.6b`, which holds 1,072,821 chunks.

What we saw before writing this, all from public files (2026-11-10, 16:30-17:00 UTC):

- The cell's `ingest.log` says `Loading embedding model: farbodtavakkoli/OTel-Embedding-0.6B` (that repo id now
  resolves to `farbodtavakkoli/OTel-Embedding-600M`, a Qwen3-Embedding-0.6B fine-tune). It then prints the
  sentence-transformers notice: "Default prompt name is set to 'Retrieval-query'. This prompt will be applied to
  all inference calls, except if a `prompt` or `prompt_name` parameter is provided."
- That model's `config_sentence_transformers.json` sets `default_prompt_name` to `Retrieval-query`. The query
  instruction is "Instruct: Given a telecom domain query, retrieve relevant passages that answer the query\nQuery:"
  and the document prompts are empty.
- `Qwen/Qwen3-Embedding-0.6B` (the base model, used for the control cell `text_baseline/qwen3-embedding-0.6b`)
  sets `default_prompt_name` to null.
- The ingest code (`Znbne/telco-retrieve`, package `open-telco-rag` 0.1.0) is not public (GitHub returns 404),
  so we cannot read how it calls `encode`.
- In `GRID_MANIFEST.json`, the cell's `data_level0.bin` is 4,511,170,560 bytes and `length.bin` is
  4,259,840 bytes. With hnswlib's default M=16 (4,236 bytes per element at 1,024 dimensions), that is exactly
  1,064,960 slots, fewer than the 1,072,821 chunks. We have NOT read `header.bin` yet.

The notice alone does not show that passages were prefixed: it is printed whenever the model loads. A plain
`model.encode(passages)` would add the query instruction to every passage. A pipeline that passes
`prompt_name="Retrieval-document"` would not. This study tests which one happened, from the stored vectors
themselves.

## Method (telco_embcheck.py 0.1.0)

1. Pin the dataset's current revision through the Hugging Face API.
2. For each cell, read `header.bin` (100 bytes) and parse the hnswlib persistent header.
3. Draw internal positions uniformly from [0, cur_element_count). The seed is 20261110, with 100 positions in
   the otel cell and 40 in the control. Read each element's bytes from `data_level0.bin` with an HTTP range
   request, which gives the stored float32 vector, the label and the delete flag.
4. Map label to chunk id with `index_metadata.pickle` (117 MB), using a restricted unpickler that refuses
   every global except plain builtins and a stub for Chroma's own class.
5. Find each chunk's text in the cell's FTS5 database. The schema is discovered at run time: the id column is
   the one that equals a sampled chunk id, and the text column is the longest string in that row. The control
   cell first tries the otel cell's database, since chunk text is shared within a strategy.
6. Re-encode each text on CPU in float32 with the cell's model at its current Hugging Face revision, two ways:
   - document mode: `default_prompt_name` cleared, the model's document prompt (empty for both models)
   - query mode: the model's query instruction
7. Compute the cosine between the stored vector and each re-encoding. Verdict per chunk at threshold 0.99:
   "query", "document", "both" or "neither".

The cell was embedded on a GPU in float16. A faithful CPU float32 re-encoding should land well above 0.99.

## Predictions (graded by hand from embcheck1.json; the script also grades itself)

- **E1 (layout):** header.bin parses with version 1, 4,236 bytes per element, 1,024 dimensions and
  max_elements 1,064,960. The persisted HNSW graph therefore holds fewer vectors than the 1,072,821 chunks.
  Caveat, stated now: Chroma may keep the rest in its write-ahead queue inside `chroma.sqlite3` and add them
  when the collection is loaded. This study does not test that, so E1 says nothing about whether those chunks
  can be retrieved.
- **E2 (decoding works):** at least 90 of the 100 otel samples resolve to a chunk text and get a verdict.
- **E3 (main):** at least 90% of resolved otel samples are "query". This would mean the passages were embedded
  with the query instruction. Our prior is about 60%.
- **E4 (control):** at least 30 control samples resolve, and at least 90% of them are "document".
- **E5 (the two modes really differ):** the median cosine between the document-mode and query-mode
  re-encodings of the same otel passages is below 0.95.

How we will read it:
- **E3 and E4 both hold:** the default index was built with the query instruction on passages, and the base
  model control was not, which fits the `default_prompt_name` mechanism. We would tell the organisers on the
  contest's discussion board once MV2 has an account, and say it in his public notes. Whether this hurts
  retrieval is a separate question. It needs the contest's questions, which are not public yet.
- **E3 fails with mostly "document":** the pipeline handled prompts correctly. That is a negative result, and
  we report it as one.
- **Mostly "neither":** the FTS text is not exactly what was embedded. The result is inconclusive.
- **E5 fails:** the instruction barely moves the vectors. Then E3 can still be graded, but it matters little.

## Limits

This is one strategy (text_baseline) and one control cell. 140 vectors are sampled. CPU float32 is compared
with GPU float16. The model is read at today's revision, which may differ from the one used at ingest
(2026-10-08). If so, both modes could drop below 0.99 ("neither"). No retrieval quality is measured.
