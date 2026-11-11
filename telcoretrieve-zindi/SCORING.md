# TelcoRetrieve scoring: what the public starter kit says, and what it implies

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text CC BY 4.0, code
Apache-2.0. Read 2026-11-11 between 12:10 and 12:40 UTC, two days before the challenge opens (2026-11-13
12:00 UTC). Every number below is marked provisional by the organisers' own code and may change.

## Source

The challenge's pipeline repository [`Znbne/telco-retrieve`](https://github.com/Znbne/telco-retrieve)
(the `open-telco-rag` package the prebuilt indexes were built with, Apache-2.0) is now public. It returned
404 on 2026-11-10 at about 21:00 UTC. Everything here is read at commit
[`075feaa3`](https://github.com/Znbne/telco-retrieve/tree/075feaa3bc967cdce4fb945eb1342d72f625e161)
(2026-11-10 21:47 UTC), mainly `open_telco_rag/challenge/metrics/` (`accuracy.py`, `token_efficiency.py`,
`overall_score.py`), `open_telco_rag/challenge/prompt.py`, `configs/profiles/challenge.json` and
`docs/challenge/README.md`. The question set `GSMA/telco-retrieve-QnA` still returns 401 on Hugging Face.
ITU's [event page](https://aiforgood.itu.int/event/telcoretrieve-challenge-grounding-large-language-models-llms-in-telecom-standards/)
agrees on the metrics: the public phase is scored "using accuracy and token efficiency as key metrics", and
top submissions are then assessed on a held-out set "using the same metrics".

## The metric

- **Submission:** a UTF-8 CSV with the header exactly `ID,input_prompt,answer`. `input_prompt` is the system
  message, a blank line, then the user message, exactly as sent to the generator.
- **Accuracy** = 100 x correct / questions. A valid answer is one letter A-E or `TRUE`/`FALSE`
  (case and surrounding spaces ignored). Anything else (`(B)`, `Answer: B`, `T`, blank) is wrong.
- **Token efficiency** = 100 x (2000 x N) / (2000 x N + total `input_prompt` tokens), counted with tiktoken
  `cl100k_base`. Because both sides are totals, this equals **100 x 2000 / (2000 + mean prompt tokens)**.
  The 2000 is marked "proposed, not confirmed". Any prompt over 4,096 tokens invalidates the submission.
  The answer column is not counted.
- **Overall** = 0.7 x Accuracy + 0.3 x Token efficiency. The weights are marked "provisional"; the docs say
  the organisers set them on Zindi.
- **Floor:** below 80% accuracy a submission is "not eligible for code evaluation".

This resolves item 4 of our [pre-launch notes](README.md): Zindi's API metric field still reads
`character_error_rate`, but the starter kit's scorer is the accuracy/token-efficiency blend above.

## What the defaults send

`configs/profiles/challenge.json`: the `otel-0.6b` embedder, hybrid search (dense + BM25) for 10 candidates,
the `otel-reranker-0.6b` reranker keeping 5, `google/gemma-3n-E4B-it` at temperature 0 (seed 1234), 8 answer
tokens, a 4,096-token prompt cap. The prompt is a one-line system message, up to five numbered passages
labelled with spec and release, the question, the options and a one-line answer instruction. Base-cell
chunks are bounded at 510 `cl100k_base` tokens, so five passages can approach 2,600 tokens. We have not
yet measured the defaults' real mean prompt length; that needs the questions.

## What the arithmetic implies (computed by `score_tradeoff.py`)

Token efficiency by mean prompt length: 100 tokens 95.24, 300 86.96, 600 76.92, 1,000 66.67, 2,000 50.00,
3,000 40.00.

Overall score (rows: accuracy; columns: mean prompt tokens):

| accuracy | 100 | 300 | 600 | 1,000 | 2,000 | 3,000 |
|---|---|---|---|---|---|---|
| 80 | 84.57 | 82.09 | 79.08 | 76.00 | 71.00 | 68.00 |
| 85 | 88.07 | 85.59 | 82.58 | 79.50 | 74.50 | 71.50 |
| 90 | 91.57 | 89.09 | 86.08 | 83.00 | 78.00 | 75.00 |
| 95 | 95.07 | 92.59 | 89.58 | 86.50 | 81.50 | 78.50 |

1. **Context length is the larger lever.** A pipeline at 80% accuracy with 300-token prompts (82.09) beats
   one at 95% with 2,000-token prompts (81.50). Going from 300 to 2,000 mean tokens has to buy 15.8 accuracy
   points just to break even; from 1,000 to 2,000, 7.1 points; from 300 to 1,000, 8.7 points.
2. **Each token costs most when prompts are short.** 100 more mean tokens cost the equivalent of 1.86
   accuracy points at 100 tokens, 1.55 at 300, 0.92 at 1,000 and 0.52 at 2,000. A 500-token passage added to
   a 300-token prompt must add about 6.7 accuracy points to pay for itself.
3. **The 80% floor decides the shape of a winning entry.** The best entries will likely sit just above the
   floor with very short prompts, or well above it with short prompts, rather than at high accuracy with
   long ones. A closed-book prompt (no passages, roughly 60-120 tokens) scores about 94-97 on efficiency, but only
   counts if accuracy reaches 80.
4. **Budgets are pooled.** Efficiency uses the total over all questions, so tokens can be spent unevenly:
   no passages where the retriever or reranker is confident the question needs none, more where it is not.
   A fixed top-k wastes budget. An honest adaptive rule must decide from retrieval signals; extra generator
   calls whose prompts do not appear in `input_prompt` would misreport the token count, and we would ask the
   organisers before using anything like that.
5. **Formatting is free accuracy.** Only a bare letter or `TRUE`/`FALSE` counts, so the answer parser
   (the starter kit allows a custom `--answer-parser`) should map the generator's text to exactly that form.
6. **Passage trimming beats passage dropping.** Labels, numbering and blank lines cost tokens too; passing
   the one or two most relevant sentences instead of a whole 510-token chunk is where most of the budget can
   come back. The starter kit allows a custom `--prompt-builder`; it receives the question, the passages and
   the cap, and the CSV must hold exactly what the generator receives.

## Also noticed (not claimed as defects)

- **Query encoding in the defaults.** The `otel-0.6b` registry entry sets no query or document prompt, and
  the embedder calls plain `encode()`. Sentence-transformers then applies the model's default prompt to
  every text. Our [embcheck-1](RESULTS-embcheck1.md) found the stored passages carry the query instruction,
  so in the defaults questions and passages are encoded the same way. That is the "Q" setting our queued
  [embcheck-2](PREREGISTRATION-embcheck2.md) measures. The starter kit offers no flag to drop the
  instruction for the stock `otel-0.6b` entry (`--query-prefix` applies to custom embedders), so the "D"
  setting needs a small code change.
- **Embedder named in the rules vs the kit.** Zindi's rules name `OTel-Embedding-300M`; the kit's default
  and the suggested index use `otel-0.6b`. The kit's registry lists `otel-300m` with 1,024 dimensions,
  while our earlier reading of its Hugging Face metadata gives 768 for this EmbeddingGemma fine-tune. We have not
  run it and do not know whether that field is used.
- **Floor wording.** `overall_score.py` says accuracy below 80 is "not eligible for code evaluation", not
  that the score is withheld. How Zindi ranks sub-80 entries on the leaderboard is not stated.

## Limits

This is arithmetic on a provisional formula, not a measurement. The weights (0.7/0.3), the 2,000-token
baseline and the 4,096 cap may change at launch. We have not run the pipeline, the generator or any
question. The token figures for closed-book prompts are estimates from the template, not counts.

## Files

- [`score_tradeoff.py`](score_tradeoff.py) (standard library only): token efficiency, overall score,
  break-even accuracy gains, and the tables above (`python score_tradeoff.py` or `--json`).
- [`test_score_tradeoff.py`](test_score_tradeoff.py): offline tests (`python -m unittest -v test_score_tradeoff`).
