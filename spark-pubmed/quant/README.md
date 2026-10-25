# quant: a cheaper cross-encoder for SPARK Task 1?

MV2 of Munim, Inc. is testing whether Task 1's second stage, NCBI's MedCPT cross-encoder, can run
faster without changing what it ranks first. The code and notes were made with AI agents working
in his name. Code is Apache-2.0; notes are CC BY 4.0. No human has checked this.

The cross-encoder is the slowest stage of the Task 1 system (`../system/`): about 0.4-0.5 s per
question-article pair on 2 CPUs, 19-27 s per question at depth 50. The challenge breaks ties on
compute time and memory, so a cheaper scorer helps if it keeps the ranking. This folder tests two
settings that `../rerank/rerank.py` already has:

- dynamic int8 weights for the Linear layers (about 1.7-2.1x faster in the synthetic benchmark
  `../rerank/RESULTS.md`, but with logits that moved by up to 6.7 on the model card's example);
- 256-token inputs instead of 512 (cuts off the end of long abstracts).

Each variant rescores the same 50 candidates per question that the fp32/512 runs scored on the
three dev sets (L, BioGen Supports, R), so a change in the top five comes from the variant alone.

## Result (`RESULTS-spark42.md`, graded 2026-10-25)

4 of 4 checks and 4 of 10 predictions held; the key prediction missed. **No cheaper variant
passed the pre-registered rule, so stage 2 stays fp32 with 512-token inputs.**

| Variant | Mean top:5 MRR (L, BioGen, R) | L MRR | ms per pair | L speed-up |
|---|---|---|---|---|
| fp32/512 (base) | 0.4934 | 0.1500 | 381.7 (L) | 1.00 |
| int8/512 | 0.4586 | 0.0814 | 251.7 | 1.77 |
| fp32/256 | 0.4778 | 0.1287 | 324.5 | 1.19 |
| int8/256 | 0.4360 | 0.0636 | 181.3 | 2.12 |

Dynamic int8 reorders the top five on almost every question (the same top-five set on 5 of 43 L
questions) and halves L's MRR. 256-token inputs keep the ranking better but save only about 16%.

## Files

- `quant_run.py` 0.1.0: runs `../rerank/rerank_run.py` with `CrossEncoder(max_length, quantize)`
  and records the variant in `rerank.json`.
- `quant_table.py` 0.1.0: top-5 MRR, hits, agreement with the fp32 ranking, speed, projected
  cross-encoder hours, and the pre-registered choice of variant. Writes counts and ids only.
- `test_quant.py`: 8 tests (fake data, plus one on the published `rerank_run.py`).
- `PREREGISTRATION-spark42.md`: the job's design, 10 predictions and the decision rule, written
  before the job was filed.
- `RESULTS-spark42.md`: the grade, word for word, and what it decides.
- `results-spark42/`: the job's count files (`table.json`, each variant's `rerank.json`, the
  host, model and gold checks). No question text.

The job also uses copies of `t2dev.py` (BioGen gold) and `fetch_code.py` (fetches the published
`t1_runner`, `t2` and `rerank` code at pinned commits).

Prior art: int8 quantisation of BERT-family models (for example Q8BERT, 2019) and input
truncation are standard. What is new here is only the measurement for MedCPT's cross-encoder on
whole-PubMed candidates and these dev sets.

Contact: MV2, Munim, Inc., mv2@munimtech.com
