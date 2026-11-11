# Results: embcheck-1 (graded by hand, 2026-11-11)

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text CC BY 4.0; code
Apache-2.0. Pre-registration: [PREREGISTRATION-embcheck1.md](PREREGISTRATION-embcheck1.md). Code:
[telco_embcheck.py](telco_embcheck.py) 0.1.0. Machine output: [embcheck1.json](embcheck1.json) and
[RESULTS-embcheck1-auto.md](RESULTS-embcheck1-auto.md). Run: 2026-11-11 00:32-01:11 UTC in a sealed
container (peak memory 1.24 GB). All 9 offline tests passed. The pre-registration was public on GitHub
before any stored vector was read, and the public copy matched the local one byte for byte
(`prereg_public_embcheck1.json`, seen 00:32:28Z).

**Headline: the passages in TelcoRetrieve's suggested starting index were embedded with the query
instruction.** All 100 randomly sampled vectors of `GSMA/telco-retrieve-chunks`,
`telcoretrievechallenge/fixed-grid/text_baseline/otel-0.6b`, match their passage encoded *with* the OTel
embedder's query instruction ("Instruct: Given a telecom domain query, retrieve relevant passages that
answer the query\nQuery:"), and none match the plain passage encoding. In the control cell built with the
base model (`qwen3-embedding-0.6b`, which has no default prompt), all 40 sampled vectors match the plain
encoding. This fits the sentence-transformers mechanism the pre-registration described: the OTel model's
config sets `default_prompt_name = "Retrieval-query"`, so `model.encode(passages)` without a prompt name
prefixes every passage with the query instruction. Whether this hurts retrieval is not measured here.

## Numbers

Dataset revision `2ec07608ee2a77a59a3f5995ca3c10e9cba4c976`. Models re-encoded at
`OTel-Embedding-600M@f7755f84` and `Qwen3-Embedding-0.6B@97b0c614`, sentence-transformers 5.7.0, torch
2.15.0 (CPU).

| cell | sampled | resolved to text | verdict | median cos(stored, plain) | median cos(stored, with instruction) | median cos(plain, with instruction) |
|---|---|---|---|---|---|---|
| otel-0.6b | 100 | 100 | **query 100** | 0.962 | 1.000 | 0.962 |
| qwen3-embedding-0.6b (control) | 40 | 40 | **document 40** | 1.001 | 0.971 | 0.970 |

- otel: every sample's cosine with the instruction encoding is 0.998 or more; every sample's cosine with
  the plain encoding is 0.986 or less. The gap is at least 0.012 on every sample.
- **Where the instruction dominates.** For 16 of the 100 otel passages, the stored vector is far from the
  plain encoding (cosine 0.51-0.67). 14 of the 100 sampled chunks are exactly 254 characters long, and 13 of
  those 14 are among the 16; the other 3 are 118-199 characters. The 14 come from 13 different
  documents, among them service-based core network specifications (TS 29.509, 29.510, 29.522, 29.562),
  RAN protocol specifications (TS 36.331, 38.473 twice) and conformance test specifications (TS 34.229-5,
  38.141-1, 38.521-3). We have not read these chunks' text and do not know why so many are exactly 254
  characters. For longer passages the instruction moves the vector little (cosine
  about 0.95-0.98).
- **Index layout.** Both cells' `header.bin`: hnswlib persistence version 1, 4,236 bytes per element
  (1,024 dimensions), M 16, ef_construction 100, `max_elements` 2,097,152, `cur_element_count`
  1,064,960. The metadata pickle also counts 1,064,960 elements added. So the persisted HNSW graph holds
  7,861 fewer vectors than the 1,072,821 chunks (0.73%). 1,064,960 is exactly 65 x 16,384. Chroma may
  add the rest from its SQLite queue when the collection loads; this study does not test that.

## Predictions, graded by hand (the code's `grade()` agrees on all five)

| id | prediction | value | held |
|---|---|---|---|
| E1 | header: version 1, 4,236 bytes/element, 1,024 dims, max_elements 1,064,960, so fewer vectors than chunks | version 1, 4,236, 1,024 as predicted; **max_elements 2,097,152**, cur_element_count 1,064,960 < 1,072,821 | **no** (as worded: I took the file's slot count for max_elements; the substance, 1,064,960 persisted vectors, held) |
| E2 | at least 90 of 100 otel samples resolve and get a verdict | 100 of 100 | yes |
| E3 | at least 90% of resolved otel samples are "query" | 100 of 100 | **yes** |
| E4 | at least 30 control samples resolve and at least 90% are "document" | 40 of 40, all "document" | yes |
| E5 | median cosine between plain and instruction encodings of the otel passages is below 0.95 | 0.962 | **no** (most passages move little; a minority moves a lot) |

## Deviation from the plan

The pre-registration said the re-encoding would run "in float32". The script did not set a dtype, and some
cosines exceed 1 by up to about 0.0015 (for example 1.0015), which unit vectors computed in float32 cannot
do. The model most likely ran in its stored half-precision dtype. That error is about 8 times smaller than
the smallest gap between the two encodings on any sample, so no verdict depends on it. embcheck-2 records
the dtype.

## What it means for entrants

1. If you use the `otel-0.6b` cell, its passages carry the query instruction. Do not assume the usual
   asymmetric setup (instruction on queries only) when choosing how to encode your questions. Test both
   ways on the contest's own questions.
2. The effect is uneven: small for ordinary prose passages and large for short or code-like chunks. Those
   may behave like generic "telecom query" vectors. [PREREGISTRATION-embcheck2.md](PREREGISTRATION-embcheck2.md)
   tests whether they crowd the top 10 for real 3GPP questions.
3. The base-model cell (`qwen3-embedding-0.6b`) was built the standard way and is a clean comparison.

## Closest prior work found

sentence-transformers PRs #4095 and #4110 discuss `default_prompt_name` silently applying a query prompt
to documents. We found no public report, as of 2026-11-11, that this happened in the TelcoRetrieve
prebuilt indexes, or a measurement of it from stored vectors.

## Limits

One strategy (text_baseline), 100 + 40 vectors, CPU re-encoding in the model's default dtype against GPU
float16 storage, models at their 2026-11-11 revisions (ingest ran 2026-10-08; the near-1.0 cosines suggest
the weights did not change). No retrieval quality was measured. Nothing here uses Zindi's data or is a
contest submission.
