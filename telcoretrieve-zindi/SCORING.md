# TelcoRetrieve scoring: what the public starter kit says, and what it implies

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text CC BY 4.0, code
Apache-2.0. Version 2, read 2026-11-11 between 18:15 and 18:40 UTC, two days before the challenge opens
(2026-11-13 12:00 UTC). Zindi's challenge page is the authority; these numbers can still change at launch.

## What changed in version 2 (2026-11-11 ~18:30 UTC)

The organisers' challenge docs now give the token baseline: **B = 850 tokens per question**, not the 2,000
that version 1 used. Source: `docs/challenge/README.md` in
[`Znbne/telco-retrieve`](https://github.com/Znbne/telco-retrieve) at commit
[`a9b61be6`](https://github.com/Znbne/telco-retrieve/commit/a9b61be6) (merge of pull request #29,
2026-11-11 16:01 UTC), which says: "Score = 0.7 × accuracy + 0.3 × token efficiency, where token efficiency
= 100 × B / (B + T). B is 850 tokens per question and T is the total prompt tokens. Minimum accuracy is 80%.
Every `input_prompt` must be at most 4,096 tokens." The same docs no longer call these values provisional.

Two other changes in that commit: the question set moved from Hugging Face (`GSMA/telco-retrieve-QnA`,
`Test_public.csv`) to the Zindi challenge page (`Test.csv`, Data tab, columns `ID,question,options`, no
answers), and the docs now say the leaderboard score is computed by Zindi.

One mismatch remains: the kit's scorer code (`open_telco_rag/challenge/metrics/token_efficiency.py`) still
uses 2,000, marked "proposed, not confirmed". Anyone scoring locally with the kit's `score` command
gets efficiency figures that are too high compared with the docs. We read the docs as the newer statement.
`score_tradeoff.py` now defaults to 850 and keeps 2,000 behind `--baseline 2000`.

Version 1 (B = 2,000, commit `075feaa3`) is in this file's history. Its headline, that 80% accuracy at 300
tokens beats 95% at 2,000 tokens, still holds, by a wider margin. Its marginal-cost figures were too low
for short prompts.

## The metric

- **Submission:** a UTF-8 CSV with the header exactly `ID,input_prompt,answer`. `input_prompt` is the system
  message, a blank line, then the user message, exactly as sent to the generator.
- **Accuracy** = 100 x correct / questions. A valid answer is one letter A-E or `TRUE`/`FALSE`
  (case and surrounding spaces ignored). Anything else (`(B)`, `Answer: B`, `T`, blank) is wrong.
- **Token efficiency** = 100 x B / (B + T), counted with tiktoken `cl100k_base` over the whole `input_prompt`.
  The kit's code takes both the baseline and T as totals over all questions, so this equals
  **100 x 850 / (850 + mean prompt tokens)**. A mean prompt of 850 tokens scores exactly 50. Any prompt over
  4,096 tokens invalidates the submission. The answer column is not counted.
- **Overall** = 0.7 x Accuracy + 0.3 x Token efficiency.
- **Floor:** minimum accuracy 80%. The kit's `overall_score.py` says a submission below 80 is "not eligible
  for code evaluation". How Zindi ranks sub-80 entries on the leaderboard is not stated.

## What the defaults send

`configs/profiles/challenge.json`: the `otel-0.6b` embedder, hybrid search (dense + BM25) for 10 candidates,
the `otel-reranker-0.6b` reranker keeping 5, `google/gemma-3n-E4B-it` at temperature 0 (seed 1234), 8 answer
tokens, a 4,096-token prompt cap. The prompt is a one-line system message, up to five numbered passages
labelled with spec and release, the question, the options and a one-line answer instruction. Base-cell
chunks are bounded at 510 `cl100k_base` tokens, so five passages can approach 2,600 tokens. We have not
measured the defaults' real mean prompt length: that needs the questions, which are now only on Zindi.

## What the arithmetic implies (computed by `score_tradeoff.py`, B = 850)

Token efficiency by mean prompt length: 100 tokens 89.47, 300 73.91, 600 58.62, 850 50.00, 1,000 45.95,
2,000 29.82, 3,000 22.08.

Overall score (rows: accuracy; columns: mean prompt tokens):

| accuracy | 100 | 300 | 600 | 1,000 | 2,000 | 3,000 |
|---|---|---|---|---|---|---|
| 80 | 82.84 | 78.17 | 73.59 | 69.78 | 64.95 | 62.62 |
| 85 | 86.34 | 81.67 | 77.09 | 73.28 | 68.45 | 66.12 |
| 90 | 89.84 | 85.17 | 80.59 | 76.78 | 71.95 | 69.62 |
| 95 | 93.34 | 88.67 | 84.09 | 80.28 | 75.45 | 73.12 |

1. **Context length is the larger lever, more so than in version 1.** 80% accuracy with 300-token prompts
   (78.17) beats 95% with 2,000-token prompts (75.45). Going from 300 to 2,000 mean tokens has to buy 18.9
   accuracy points to break even (15.8 with B = 2,000); from 300 to 1,000, 12.0 points; from 1,000 to 2,000,
   6.9 points. 95% at 2,000 tokens is worth the same as 76.1% at 300 tokens, and a 2,000-token entry needs
   98.9% accuracy to match 80% at 300 tokens.
2. **Short prompts are where tokens cost most.** 100 more mean tokens cost the equivalent of 3.65 accuracy
   points at 100 tokens, 2.53 at 300, 1.01 at 1,000 and 0.43 at 2,000 (version 1: 1.86, 1.55, 0.92, 0.52).
   A 500-token passage added to a 300-token prompt must now add about 9.6 accuracy points to pay for itself
   (6.7 in version 1).
3. **Long context can still win if it buys a lot.** 95% at 1,000 tokens (80.28) beats 80% at 300 (78.17),
   so the trade-off is not one-sided: what decides it is how much accuracy each passage really adds.
4. **The 80% floor decides the shape of a winning entry.** A closed-book prompt (no passages, roughly 60-120
   tokens, an estimate from the template) scores about 88-93 on efficiency, but only counts if accuracy
   reaches 80.
5. **Budgets are pooled.** Efficiency uses totals over all questions, so tokens can be spent unevenly: no
   passages where the retriever or reranker is confident none are needed, more where it is not. A fixed
   top-k wastes budget. An honest adaptive rule must decide from retrieval signals; extra generator calls
   whose prompts do not appear in `input_prompt` would misreport the token count, and we would ask the
   organisers before using anything like that.
6. **Formatting is free accuracy.** Only a bare letter or `TRUE`/`FALSE` counts, so the answer parser
   (the kit allows a custom `--answer-parser`) should map the generator's text to exactly that form.
7. **Passage trimming beats passage dropping.** Labels, numbering and blank lines cost tokens too; passing
   the one or two most relevant sentences instead of a whole 510-token chunk is where most of the budget can
   come back. The kit allows a custom `--prompt-builder`, and the CSV must hold exactly what the generator
   receives.

## Also noticed (not claimed as defects)

- **Query encoding in the defaults.** The `otel-0.6b` registry entry sets no query or document prompt, and
  the embedder calls plain `encode()`. Sentence-transformers then applies the model's default prompt to
  every text. Our [embcheck-1](RESULTS-embcheck1.md) found the stored passages carry the query instruction,
  so in the defaults questions and passages are encoded the same way. Our queued
  [embcheck-2](PREREGISTRATION-embcheck2.md) measures this as its "Q" setting.
- **Embedder named in the rules vs the kit.** Zindi's rules name `OTel-Embedding-300M`; the kit's default
  and the suggested index use `otel-0.6b`.
- **Baseline in docs vs code.** Covered above: docs 850, scorer code 2,000.

## Limits

This is arithmetic on the published formula, not a measurement. We have not run the pipeline, the generator
or any question. Closed-book token figures are estimates from the template, not counts. If Zindi's page
gives different numbers on 2026-11-13, that page wins; rerun `python score_tradeoff.py --baseline <B>`.

## Files

- [`score_tradeoff.py`](score_tradeoff.py) (standard library only): token efficiency, overall score,
  break-even accuracy gains and the tables above (`python score_tradeoff.py [--json] [--baseline N]`).
- [`test_score_tradeoff.py`](test_score_tradeoff.py): offline tests (`python -m unittest -v test_score_tradeoff`).
