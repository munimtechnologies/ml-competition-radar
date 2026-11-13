# TelcoRetrieve Challenge (Zindi, ITU and GSMA): notes for entrants

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text is CC BY 4.0 and code
is Apache-2.0. Everything here comes from public pages and files, read 2026-11-10 between 16:30 and 17:00 UTC,
with an addendum read between 20:45 and 21:15 UTC, study results from 2026-11-11 and 2026-11-12 and a scoring
analysis read 2026-11-11 between 12:10 and 12:40 UTC, updated between 18:15 and 18:40 UTC (marked below). The
contest facts were re-read from Zindi's public API on 2026-11-13 between 14:20 and 14:35 UTC, after the
challenge opened at 12:00 UTC. Zindi's rules record says it was last updated 2026-11-13 10:41 UTC.

## New at launch (2026-11-13 ~14:30 UTC): far fewer submissions, and the final ranking comes from re-run code

What changed on Zindi's page since our 2026-11-12 reading:

- **Submissions: 1 a day and 20 in total** ("Submission Limits: 1 submission per day, 20 submissions overall").
  On 2026-11-12 the page said 10 a day and 300 in total. Submissions that fail processing do not count. You
  pick 2 submissions for the private leaderboard; otherwise your 2 best public ones are used.
- **Questions come in three sets.** 100 questions at the start, scored on the public leaderboard
  (13 Nov 2026 - 8 Jan 2027). Five days before submissions close (about 8 Jan 2027), 200 new, unseen questions;
  the top 10 on those 200 go to code review (13 Jan). From 15 to 31 Jan 2027 Zindi re-runs the finalists' code
  on the organisers' AMD GPU cloud instances (288 GB HBM3E, 24-32 vCPUs) against another unseen question set,
  and those results set the final ranking.
- **Zindi now states the token baseline itself:** "850 tokens per question (85,000 tokens for the 100 public
  questions)", `cl100k_base`, at most 4,096 tokens per prompt, weights 0.7 accuracy and 0.3 token efficiency,
  and an 80% accuracy floor below which a submission "will be disqualified". It still gives no formula; the kit's
  docs give efficiency = 100 x B / (B + T) (see [SCORING.md](SCORING.md)). B = 850 and the 0.7 / 0.3 weights
  match what SCORING.md already uses, so its numbers stand.
- **Team size is settled at 3** everywhere on the page ("a team of up to three people"; teams are now allowed),
  and no members may be added in the final 5 days.
- **Participants:** 175, with 7 on the leaderboard, at about 14:25 UTC.
- The starter kit's newest commit is now `d1a46b4a` (2026-11-13 14:06 UTC, PR #31). The commits since
  `a9b61be6` add a slide deck and a short challenge section to the README; none touches the scorer code.

What that means in numbers (our arithmetic, approximate):

- **100 questions is a noisy yardstick.** At a true accuracy of 85%, one submission's public accuracy has a
  standard error of about 3.6 points (sqrt(0.85 x 0.15 / 100)); on the 200 final questions it is about 2.5.
  Two pipelines that disagree on 10 of the 100 questions have a paired standard error of about 3.2 points on
  their accuracy difference (sqrt(10) / 100). With 20 submissions, most public-board differences of a few
  points cannot be told apart from luck.
- **The token term is almost noise-free.** Prompt length is decided by your pipeline, not by which answers
  happen to be right. Cutting mean prompts from 600 to 300 tokens raises efficiency from 58.6 to 73.9, which is
  +4.6 overall points, worth as much as 6.6 accuracy points.
- **The 80% floor is a real risk near 80%.** Normal approximation: a pipeline that is truly 85% accurate scores
  below 80% on 100 questions about 6% of the time (about 2% on 200); one that is truly 82% accurate does so
  about 26% of the time (about 20% on 200).
- **Tuning to the 100 public questions does not carry.** The final ranking comes from re-running your code on
  questions nobody has seen, so only general choices (retrieval, context size, prompt, answer parsing) count.
  Test them locally on your own held-out questions rather than spending the 20 submissions on them.

Still open: the page says the public leaderboard covers "approximately 30%" of the test data in its summary and
"approximately 20%" in the full rules, and the full rules say the public board ranks "by the accuracy score",
which does not match the two-metric score described in the Evaluation section.

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
[test_telco_embcheck3.py](test_telco_embcheck3.py). It is queued and has not run yet (2026-11-13 14:30 UTC).

## Updated (2026-11-11 ~18:30 UTC): the scoring rule, and why short prompts win

The challenge's pipeline repository [`Znbne/telco-retrieve`](https://github.com/Znbne/telco-retrieve) is
public (Apache-2.0). Its challenge docs, updated at commit `a9b61be6` (2026-11-11 16:01 UTC), give the score as
**Overall = 0.7 x Accuracy + 0.3 x Token efficiency**, with token efficiency = 100 x B / (B + T), **B = 850
tokens per question** and T the prompt tokens (`cl100k_base`), equivalently 100 x 850 / (850 + mean
`input_prompt` tokens). There is an 80% accuracy floor and a 4,096-token prompt cap. Our first reading
(12:40 UTC, commit `075feaa3`) used the kit code's earlier B = 2,000, which that code still marks "proposed,
not confirmed". (2026-11-13: Zindi's own page now states the 850-token baseline; the kit's scorer code has not
changed.)

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

## The contest (from Zindi's public API, re-read 2026-11-13 ~14:25 UTC)

- **Prize:** Zindi's reward field reads **€25,000** (it read $20,000 before 2026-11-12). The cash places are
  8,000 / 5,000 / 3,500 / 2,000 / 1,500 (the page labels them both "€" and "USD"; the rules say winners are paid
  "in USD or the currency of the challenge"). The top three also each get an MWC Barcelona Leader Pass (given as
  worth €2,000) and up to 1,500 towards the costs of attending MWC Barcelona in March 2027.
- **Dates:** opened 2026-11-13 12:00 UTC; entries close 2027-01-06 23:59; submissions close 2027-01-13 22:25;
  the contest ends 22:55. Public phase on 100 questions 13 Nov - 8 Jan; 200 final questions 8-13 Jan; top 10
  selected 13 Jan; code review on unseen questions 15-31 Jan 2027 (see "New at launch" above).
- **Task:** answer questions grounded in 3GPP standards. Submission: one CSV with columns `ID, input_prompt,
  answer`, where `input_prompt` is the full prompt sent to the generator (system prompt and retrieved context
  included) and `answer` is a letter A-E or TRUE/FALSE.
- **Required models:**
  - generator `google/gemma-3n-e4b-it`
  - embedder `farbodtavakkoli/OTel-Embedding-300M`
  - reranker `farbodtavakkoli/OTel-Reranker-0.6B`
  - Fine-tuning them is allowed; other pretrained models only if openly available to everyone.
- **Data and tools:** only the provided datasets may be used. AutoML tools are not permitted, nor paid services
  or free trials that need a credit card. The rules do not mention AI-assisted code. Seeds must be set and
  results must reproduce.
- **Limits:** an 80% accuracy floor (below it a submission is disqualified); **1 submission a day, 20 in total**
  (was 10 a day, 300 in total, on 2026-11-12); teams of up to 3.
- **Metric on Zindi:** "multi" (token efficiency 0.3, accuracy 0.7), with an 850-token-per-question baseline.

## Things that do not line up yet (worth asking about on the forum)

1. **Embedder name.** Zindi names `OTel-Embedding-300M`, a fine-tune of `google/embeddinggemma-300m` with
   768 dimensions. GSMA's suggested starting index, `fixed-grid/text_baseline/otel-0.6b`, was built with
   `farbodtavakkoli/OTel-Embedding-0.6B` according to its own `ingest.log`. That repo id now resolves to
   `OTel-Embedding-600M`, a fine-tune of `Qwen/Qwen3-Embedding-0.6B` with 1,024 dimensions. None of the 18
   base cells is labelled as built with the 300M OTel model. The closest, `embeddinggemma-300m-fp32`, is named
   after the base Gemma embedder. (2026-11-11: the starter kit's challenge profile also defaults to
   `otel-0.6b`, and its registry lists `otel-300m` with 1,024 dimensions.)
2. **Public/private split.** The summary says about 30/70, the full rules about 20/80 (still so on 2026-11-13
   after launch). The full rules also say the public board ranks "by the accuracy score".
3. **Team size.** *Resolved 2026-11-13:* 3 everywhere, teams allowed.
4. **Metric.** *Resolved:* 0.7 x accuracy + 0.3 x token efficiency with B = 850, now stated on Zindi's page
   too (no formula there). The kit's scorer code still uses 2,000 ("proposed, not confirmed").
5. **Pipeline code and questions.** *Code resolved 2026-11-11:* `Znbne/telco-retrieve` is public
   (Apache-2.0). *Questions (18:30 UTC):* the kit's docs point to `Test.csv` on the Zindi challenge page
   (columns `ID,question,options`, no answers) instead of `GSMA/telco-retrieve-QnA` on Hugging Face.
6. **Prize pool.** *Mostly resolved 2026-11-12:* Zindi's reward field says €25,000, matching ITU's AI for
   Good event page. The listed cash places still add up to 20,000, and the page mixes "€" and "USD" labels.
7. **Query instruction on passages** (2026-11-11): see the result above.

## The prebuilt indexes (`GSMA/telco-retrieve-chunks`, folder `telcoretrievechallenge/`)

- 18 base cells (3 chunking strategies x 6 embedders), each 7.15-10.26 GB. Each cell is a Chroma store with
  cosine distance plus an SQLite FTS5 (BM25) database, built from `GSMA/3GPP` Release 19 (1,557 files).
- 36 enriched cells (406 GB) and 18 cells with 8B embedders.
- `archive/` (about 1 TB) is not part of the challenge.
- The text is verbatim 3GPP material. Zindi lists the challenge data as CC-BY-SA 4.0; the index dataset's own
  card still said "to be decided by GSMA" when we read it on 2026-11-10.

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
