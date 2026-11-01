# Pre-registration: t2gen-v1 (can a small open model write a cited answer on a CPU?)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Written 2026-11-01 (UTC), before the job ran and before any of its output existed. The job waits
until this file is public on GitHub (`wait_public.py`) and records whether the public copy matches.

## Why

SPARK Task 2 wants written, cited answers. MV2's extractive composer only copies abstract sentences,
and `RESULTS-mv2-nugget.md` found those carry far fewer of NLM's expert facts than the LLM-written
TREC 2024 BioGen answers. Before building a written stage, this job asks a narrower question that
needs no answer-quality yardstick (none is in use: see README): **can an openly licensed
instruction model small enough for the shared CPUs write a cited answer of the right length, in
reasonable time, whose sentences stay lexically with the abstracts they cite?**

No nugget or pool-based score is computed. Both were ruled out on the 2024 data
(`RESULTS-medaesqa-nugget-v2.md`, `RESULTS-biogen-reuse*.md`), so this job does not measure
answer quality.

## Setting (fixed)

- **Questions:** the 40 MedAESQA questions (NLM, CC0 1.0, osf.io/ydbzq, `medaesqa_v1.json`,
  sha256 `a062742c…9c383`).
- **Evidence, up to K = 8 abstracts per question:** first the PMIDs cited in the expert-written
  answer (in order of appearance), then the papers BioGen 2024 assessors judged "Supports" in the
  30 runs' answers (most often judged first). Shown as the title plus the first 160 abstract words,
  numbered [1]..[k]. Titles and abstracts come from NCBI E-utilities efetch (at most 100 PMIDs per
  request, under 3 requests per second). **This is an easy, oracle-style setting:** experts and
  assessors chose the papers. It is not MV2's own retrieval.
- **Writer:** Qwen/Qwen2.5-0.5B-Instruct (Apache-2.0), revision `7ae557604adf67be50417f59c2c2f167def9a775`,
  float32, 2 threads, greedy decoding, at most 400 new tokens. One fixed prompt (`t2gen.py`
  `SYSTEM`/`PROMPT`) asks for at most 200 words, using only the abstracts, ending every sentence
  with [n] citations, and saying so when abstracts disagree or do not answer.
- **Speed guard:** after 3 answers, the job stops if the projected time exceeds 4 hours.

## Measures (`t2gen.py` 0.1.0)

Sentences are split at `.`, `!` or `?` followed by whitespace and at line breaks. Citation groups
that open a fragment are moved back to the sentence before. A sentence is **scored** if it has at
least 3 content words (lower-case word tokens minus a fixed stop list; numbers kept; [..] groups
and 6-9 digit numbers removed).

- **Speed:** seconds per answer (prompt plus generation), prompt and new tokens, tokens per second.
- **Length:** words per answer, citation groups removed. Within limit = at most 250 words
  (BioGen's limit). Truncated = 400 new tokens reached.
- **Cited share:** share of scored sentences with at least one valid [n] (1 <= n <= k shown).
  Out-of-range numbers are counted separately.
- **Grounding of a cited sentence:** the share of its content words found in the shown text of the
  abstracts it cites. `ground_any` uses all shown abstracts. Weak = below 0.5.
- **Citation targeting:** whether a cited sentence's citations include the shown abstract it
  overlaps most (ties count).
- **Verbatim:** whether a scored sentence shares an 8-word span with a shown abstract.
- **Declines:** answers matching `DECLINE_RX` ("cannot", "unable to", "does not address", "no
  information", ...).
- **Expert reference:** each expert-answer sentence with at least 3 content words, against the full
  title and abstract of the PMIDs it cites, with the same grounding and verbatim measures.
- **Negative control:** each model sentence against the shown abstracts of the next question.
- **Memory:** peak resident memory read inside the job (`ru_maxrss`).

## Checks (the job counts as run as designed only if all hold)

- K1. `python -m unittest -v test_t2gen`: **18 tests**, OK.
- K2. The pre-registration is public before the run step (`prereg_public.json`: public true,
  match true).
- K3. All 8 model files match their pinned sizes (`model.json`: problems empty).
- K4. The MedAESQA file matches its sha256 and gives 40 items.
- K5. `t2gen.json` has `problem` null: every question with evidence was answered.

## Predictions

- P1. At least 38 of 40 expert answers contain a PMID (`expert.questions_with_pmid`).
- P2. Median distinct PMIDs per expert answer between 3 and 15. At least 95% of the requested PMIDs
  come back with a non-empty abstract.
- P3. Median seconds per answer between 15 and 120 on the 2-CPU limit. Median prompt tokens
  between 1,200 and 3,000.
- P4. At least 36 of 40 answers within 250 words; median words between 80 and 220; at most 4
  truncated.
- P5. Cited share between 0.50 and 0.97. At most 10% of sentences carry an out-of-range number.
- P6. Mean grounding of cited model sentences at least 0.75, and at least 0.05 above the experts'
  mean grounding.
- P7. The experts' mean grounding between 0.45 and 0.80.
- P8. Negative control: mean grounding against the next question's abstracts at most 0.45, and at
  least 0.30 below the model's `ground_any_mean`.
- P9. Verbatim share of scored model sentences between 0.15 and 0.75, and above the experts'
  share.
- P10. Citation targeting at least 0.60.
- P11. At most 4 of 40 answers decline.
- P12. Peak resident memory at most 3.5 GB.

## Decision rule (fixed now)

The 0.5B writer is called **feasible as a draft stage** only if all six hold:
median seconds per answer <= 60; at least 36 of 40 answers within 250 words; cited share >= 0.80;
mean cited grounding >= 0.70; citation targeting >= 0.60; at most 4 declines.

- If feasible: the next step is a pre-registered test of the same writer on MV2's own retrieved
  abstracts for the 65 BioGen questions (the realistic setting), with the composer's citation
  layer checking or repairing each sentence's citations. It is still not called better than the
  extractive answers until a validated yardstick exists (TREC 2025 BioGen judgments or SPARK's own
  scorer).
- If not feasible: the failed criteria are reported. No larger model is tried on the shared CPUs
  before SPARK publishes its evaluation hardware (information session 2026-11-05), and the
  extractive composer stays the answer writer.

## Limits, stated in advance

- Lexical grounding cannot see a flipped negation, a swapped number or a wrong direction of
  effect. A high score means the words are present, not that the sentence is faithful.
- Oracle-style evidence makes this the easy case. Real retrieval will be harder.
- One prompt, one small model, greedy decoding, one machine. A negative result is about this setup
  only.
- The experts wrote from full abstracts (or more). The model saw clipped abstracts and is scored
  against what it saw, so the expert reference is a guide, not a matched comparison.
- Generated answers are derived from PubMed abstracts and are not published. Only counts and
  scores are.

## Prior art (searched 2026-11-01)

TREC 2024 and 2025 BioGen teams wrote cited answers with LLMs (mostly GPT-4-class or 70B models on
GPUs). The overviews (arXiv 2411.18069, 2603.21582) report answer and citation quality, not CPU
time or lexical grounding of sub-1B models. This job is a feasibility measurement for MV2's entry,
not a claim of novelty.
