# Pre-registration: embcheck-3. What are the exactly-254-character chunks in TelcoRetrieve's text_baseline index?

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-11-12 ~17:40 UTC by AI agents working in his name,
after embcheck-2's output was read and before this job runs. Text CC BY 4.0; code Apache-2.0.

## Why

embcheck-2 (exploratory: its question-count gate failed, see RESULTS-embcheck2.md) found that chunks exactly
254 characters long make up 8-9% of 10,000 sampled vectors in both the `otel-0.6b` and `qwen3-embedding-0.6b`
text_baseline cells. Yet they took only 0-4 of 1,910 top-10 slots for 191 public 3GPP questions, against
158-175 expected at their base rate, while chunks shorter than 254 characters got about their fair share.
We have not read their text. This study only describes them, from the full chunk tables, so that entrants
know what dense retrieval is skipping.

## Method (telco_embcheck3.py 0.3.0, standard library only, no network in the analysis step)

1. Read every row (`doc_id`, `text`) of the SQLite FTS5 table `bm25_index` in each cell's `_fts.db`, as
   already downloaded by embcheck-2 (dataset `GSMA/telco-retrieve-chunks`, revision `2ec07608...`, cached in
   the job's data volume; if this host's volume lacks it, the script downloads the same file at the same
   revision). Length = Python `len(text)` in characters.
2. `doc_id` looks like `Rel-19/23_series/23288-j20.md::otel-0.6b::1113`: document = text before the first
   `::`, chunk index = integer after the last `::`, series = the second path part (`23_series`).
3. Groups: L254 (exactly 254 characters) and NEAR (200-253 characters, the comparison group).
4. Per cell: row count, length histogram, L254 count and share, spike ratio = count at 254 / mean count over
   lengths 240-253 and 255-268, share of L254 chunks whose previous or next chunk index in the same document
   is also L254 (and the same for NEAR, as context), series breakdown. Content features of every L254 and
   NEAR chunk: share of letters, digits and whitespace, whether it contains `|`, whether its last non-space
   character is `.`, whether it starts with a lower-case letter, newline count, longest whitespace-free run.
5. Cross-cell: for (document, chunk index) keys present in both cells, the share with the same length.
6. 25 L254 chunks are drawn with seed 20261112 and saved for reading. Their text is not published here,
   because the dataset's licence is still "to be decided by GSMA". We will only describe them.

## Gate

- GF: each cell's table is readable and has at least 1,000,000 rows. If it fails, nothing is graded.

## Predictions (graded by hand from embcheck3.json; the script also grades itself)

| id | prediction | my confidence |
|---|---|---|
| D1 | otel: L254 chunks are between 5% and 12% of all rows | 80% |
| D2 | the two cells' L254 counts differ by less than 0.1% of otel's row count (same chunking) | 85% |
| D3 | otel: spike ratio at 254 is at least 20 | 85% |
| D4 | otel: at least 50% of L254 chunks have an L254 neighbour (previous or next index, same document) | 60% |
| D5 | otel: median letter share of L254 chunks is lower than that of NEAR chunks | 60% |
| D6 | otel: the share of L254 chunks ending in `.` is lower than that of NEAR chunks | 65% |

How we will read it:
- **D3 and D4 hold:** 254 is a hard cut made by the chunker, which slices long runs of text into fixed
  254-character pieces. D5 and D6 then say whether the runs are tables, code or other non-prose.
- **D3 fails:** 254 is not special in the full index, and embcheck-2's sample was a fluke of its 40 blocks.
- Either way, whether contest answers live in these chunks needs the contest's own questions and labels.

## Limits

Lengths only and simple character features. No embeddings and no relevance. One strategy (text_baseline),
two cells. Python character counts may differ from the chunker's own unit (it may count tokens or bytes).
