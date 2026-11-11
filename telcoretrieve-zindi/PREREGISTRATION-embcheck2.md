# Pre-registration: embcheck-2. Do the instruction-dominated chunks of TelcoRetrieve's default index crowd the top 10?

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-11-11 ~02:30 UTC by AI agents working in his name,
after embcheck-1 was graded and before this job ran. Text CC BY 4.0; code Apache-2.0.

## What embcheck-1 found (graded by hand, see RESULTS-embcheck1.md)

- All 100 sampled passages of the default cell `text_baseline/otel-0.6b` match their encoding WITH the
  OTel embedder's query instruction (cosine 0.998 or more), and none match the plain encoding (0.986 or
  less). All 40 control passages (`qwen3-embedding-0.6b`, base model, no default prompt) match the plain
  encoding.
- For most passages the instruction moves the vector only a little (median cosine 0.962 between the two
  encodings). For 16 of 100 it moves it a lot (0.51-0.67). 14 of the 100 sampled chunks are exactly 254
  characters long, and 13 of those 14 are among the 16.
- We have not read any of these chunks' text and do not know why so many are exactly 254 characters.

## Question

Where the instruction dominates a stored vector, the vector mostly encodes "a telecom query", not the
passage. A question encoded with the same instruction shares that component. So these chunks may rank
high for many unrelated questions (hubs). That would hurt an entrant who uses the default index with
default query encoding. Does it happen, and does encoding questions without the instruction avoid it?

## Method (telco_embcheck2.py 0.2.0; reuses telco_embcheck.py 0.1.0 unchanged from commit 4717478)

1. Dataset revision pinned to embcheck-1's (`2ec07608...`); model revisions pinned to embcheck-1's.
2. For each cell (otel and control), read 40 aligned blocks of 250 consecutive internal ids (10,000 stored
   vectors) chosen with seed 20261111 (the same positions in both cells) with HTTP range requests. Map
   labels to chunk ids (restricted unpickler) and look up each chunk's text length in the cell's FTS5
   database. Deleted or unresolved vectors are dropped.
3. Questions: GSMA's public Open Telco `GSMA/ot-lite` file `test_teleqna.json` (TeleQnA, MIT licence).
   Keep questions whose trailing tag contains "3GPP", remove the tag, drop duplicates, and pick 300 with
   seed 20261111. Only question text is used, never the answer choices.
4. Encode the questions with the cell's own model on CPU (dtype recorded) two ways: Q, with the model's
   query instruction (what an entrant does by default), and D, without it. Also encode the bare
   instruction (the empty string with the query prompt).
5. Exact cosine top 10 over the 10,000 sampled vectors for each question. Groups: L254 (exactly 254
   characters), SHORT (254 or fewer), LONG (500 or more). For each cell and query mode: the group's base
   rate, its share of the 3,000 top-10 slots, ratio = share / base rate, the share of questions with at
   least one L254 chunk in the top 10, and the skewness of N10 (how often each chunk appears in any top 10).
   Instruction affinity = cosine between each stored vector and the bare-instruction encoding.

## Gates

- GA: each cell resolves at least 9,000 of its 10,000 sampled vectors.
- GQ: at least 300 3GPP-tagged questions are available.
If a gate fails, no prediction is graded.

## Predictions (graded by hand from embcheck2.json; the script also grades itself)

| id | prediction | my confidence |
|---|---|---|
| P1 | otel: the L254 base rate in the 10,000-vector sample is between 5% and 25% (embcheck-1 saw 14/100) | 80% |
| P2 | otel, Q mode: L254 chunks take at least 2.0 times their base rate of top-10 slots | 60% |
| P3 | control, Q mode: the L254 ratio is at most 1.5 and lower than otel's Q ratio | 60% |
| P4 | otel: the L254 ratio with D-mode questions is lower than with Q-mode questions | 65% |
| P5 | otel: median instruction affinity of L254 minus that of LONG is at least 0.2, and larger than the same difference in control | 55% |
| P6 | Q mode: N10 skewness is higher in otel than in control | 60% |

How we will read it:
- **P2-P4 hold:** the default index has instruction-dominated hub chunks, and encoding questions without
  the instruction is a cheap query-side mitigation. MV2's entry would use it (or another cell), and we
  would tell the organisers on the contest forum once he has an account.
- **P2 fails:** the 254-character chunks are not hubs, and the prompt bug matters less for retrieval than
  its size suggests. A negative result, reported as one.
- No relevance labels exist for these questions, so this measures crowding, not accuracy. A real
  accuracy test needs the contest's questions (expected from 13 November 2026).

## Limits

10,000 of about 1.06 million vectors per cell, in 40 blocks of neighbouring ids (neighbours in insertion
order tend to come from the same specification). 300 TeleQnA questions about 3GPP Releases 14-19 against
a Release 19 corpus. CPU re-encoding in the model's default dtype. One seed. Only text_baseline.
