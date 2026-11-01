# Results: t2gen-v1 (can a small open model write a cited answer on a CPU?)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Graded 2026-11-01 (UTC) against `PREREGISTRATION-t2gen.md`, word for word. No human has checked
these numbers yet.

**Short answer: no, not in this setup.** Qwen2.5-0.5B-Instruct ran on 2 CPUs, but in 22 of the 40
answers it wrote only citation markers (for example `[1] [2] [3] [4] [5] [6] [7] [8]`) and no
sentence at all. Most of the other answers copied the titles and abstracts it was shown. The writer
met 2 of the 6 criteria of the decision rule, so it is **not feasible as a draft stage**. The
extractive composer stays MV2's answer writer, and no larger model is tried on the shared CPUs
before SPARK publishes its evaluation hardware.

## The run

- Job `t2gen-v1`, `t2gen.py` 0.1.0, on the shared machine's 2-CPU, 4 GB limit. It ran from
  2026-11-01 18:46 to 19:40 UTC (the answer step took 2,777 s). Every step exited 0.
- The pre-registration was public before the run step and the public copy matched the local file
  (sha256 `0ea70933…01aa`, seen at 18:49:03 UTC; the commit landed at 14:24 UTC).
- Files published here: `results-t2gen/t2gen.json` (totals), `results-t2gen/per_question.json`
  (per-answer and per-sentence counts and scores, no text), `results-t2gen/model.json` and
  `results-t2gen/prereg_public.json`. The generated answers are **not** published: they are derived
  from PubMed abstracts.

## Checks (all must hold for "run as designed")

| check | result | held |
|---|---|---|
| K1. 18 tests OK | `Ran 18 tests`, `OK` | yes |
| K2. pre-registration public before the run step | public true, match true | yes |
| K3. 8 model files at pinned sizes | problems empty | yes |
| K4. MedAESQA sha256 and 40 items | `a062742c…9c383`, 40 items | yes |
| K5. `problem` null, every question with evidence answered | null; 40 of 40 answered | yes |

The job ran as designed.

## Predictions: 8 of 12 held

| prediction | result | held |
|---|---|---|
| P1. >= 38 of 40 expert answers contain a PMID | 40 | yes |
| P2. median distinct PMIDs per expert answer 3-15; >= 95% of requested PMIDs with an abstract | 8; 784 of 787 (99.6%) | yes |
| P3. median seconds per answer 15-120; median prompt tokens 1,200-3,000 | 23.5 s; 2,043.5 | yes (see note 1) |
| P4. >= 36 of 40 within 250 words; median words 80-220; <= 4 truncated | 34; **0**; 8 | **no** (all three parts missed) |
| P5. cited share 0.50-0.97; <= 10% of sentences with an out-of-range number | 0.373; 0.96% | **no** |
| P6. mean grounding of cited model sentences >= 0.75 and >= expert mean + 0.05 | 0.448 (experts 0.569) | **no** |
| P7. experts' mean grounding 0.45-0.80 | 0.569 | yes |
| P8. negative control <= 0.45 and >= 0.30 below the model's `ground_any_mean` | 0.227; 0.843 - 0.227 = 0.616 | yes |
| P9. verbatim share 0.15-0.75 and above the experts' | 0.593 (experts 0.055) | yes |
| P10. citation targeting >= 0.60 | 0.364 | **no** |
| P11. <= 4 of 40 answers decline | 0 | yes |
| P12. peak resident memory <= 3.5 GB (`ru_maxrss`) | 3.078 GB | yes |

## Decision rule: 2 of 6 criteria met, not feasible

| criterion | result | met |
|---|---|---|
| median seconds per answer <= 60 | 23.5 s | yes (see note 1) |
| >= 36 of 40 answers within 250 words | 34 | no |
| cited share >= 0.80 | 0.373 | no |
| mean cited grounding >= 0.70 | 0.448 | no |
| citation targeting >= 0.60 | 0.364 | no |
| <= 4 declines | 0 | yes |

As fixed in advance: the failed criteria are reported, the extractive composer stays the answer
writer, and no larger model is tried on the shared CPUs before the SPARK information session
(2026-11-05) says what hardware NLM evaluates on.

## What went wrong (read from the answers locally; not pre-registered)

These counts come from `per_question.json` and from reading the answers on MV2's machine. They
were not predicted, so they describe this run and test nothing.

1. **Answers with no sentence: 22 of 40.** In 21 the model returned only the abstract numbers
   (17-39 new tokens). In one more it listed abstract titles inside square brackets (172 tokens),
   which the scorer strips as citation groups. All 22 count as 0 words, which is why the median
   length is 0 and why the median time is low.
2. **Copying the evidence.** At least 8 of the 18 answers with text start with `[n]` and then
   repeat that abstract's title and opening sentences, often for several abstracts in a row. 59%
   of the scored sentences share an 8-word span with a shown abstract (the experts: 5.5%), and their
   words are found somewhere in the shown abstracts 84% of the time, yet only 37% of them carry a
   citation. One answer wrote fifteen near-identical sentences about the same gene until it hit
   the 400-token cap.
3. **Made-up content.** One answer opens by calling melanoma the most common skin cancer, which
   is wrong (basal cell carcinoma is), and its sentences share few words with the shown abstracts
   (6 of its 13 scored sentences ground below 0.28 in all eight; mean 0.36). Another gives three different papers
   the same PubMed Central link, which the model invented. Lexical grounding cannot catch a false
   statement built from words that do appear in the abstracts, as the pre-registration warned.
4. **Speed without the empty answers.** Over the 18 answers with text, the median time is 89.5 s,
   so the speed criterion would also fail if the empty answers were left out. The slowest answer
   (931 s for 400 tokens) points to a busy shared machine at that moment.

## Notes and limits

1. P3 and the speed criterion hold only because 22 answers were nearly empty. They are graded as
   written, but they are not evidence that a 0.5B writer is fast enough.
2. **Citation placement is a measurement limit.** The model usually puts `[n]` at the start of a
   sentence. The pre-registered splitter moves a citation group that opens a fragment back to the
   sentence before (written for `risk. [1] Next`), so a leading citation is credited to the
   previous sentence. This lowers cited share, cited grounding and targeting for answers written
   that way. It cannot change the decision: the length criterion (34 of 40 within 250 words) fails
   on its own, and 22 answers contain no sentence to cite. No re-scoring was done.
3. **The grounding bar is strict for paraphrase.** The expert answers ground at 0.569 against the
   full abstracts they cite, and 34% of their sentences fall below 0.5. A writer that paraphrases
   as the experts do would miss a 0.70 lexical-grounding bar too. A later written stage needs a
   different faithfulness check than word overlap.
4. One prompt, one 0.5B model, greedy decoding, one shared machine, and an easy oracle-style
   evidence set. This is a negative result for this setup only, not for small models in general.

## What follows

- SPARK Task 2 answers stay extractive (`compose.py`), the citation and grounding layer.
- After 2026-11-05: if NLM's information session says the evaluation runs with a GPU or gives
  enough time per question, a written stage with a larger openly licensed model is designed and
  pre-registered then, with a faithfulness check other than word overlap.
- Answer quality is judged only against the TREC 2025 BioGen judgments (BioACE) once they are
  public, or SPARK's own scorer.

Contact: MV2, Munim, Inc., mv2@munimtech.com
