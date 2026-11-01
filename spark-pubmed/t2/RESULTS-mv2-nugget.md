# Results: MV2's extractive Task 2 answers against NLM's expert nuggets (mv2-nugget-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Graded 2026-11-01 (about 09:50 UTC) word for word against `PREREGISTRATION-mv2-nugget.md`, which
was public before the job read any data (`results-mv2-nugget/prereg_public.json`: seen
2026-11-01 08:30:52 UTC, sha256 `3b8555db...`, match true). No human has checked these numbers.

The job ran on 2026-11-01 from 08:20:07 to 08:33:00 UTC (python:3.12-slim, 1 CPU, 1 GB). Its input
was MV2's 65 `t2dev-v1` answers (BM25 over the full SPARK corpus, then composer 0.2.0: whole
sentences quoted from PubMed abstracts). Those answers contain abstract text and stay local; only
counts and scores are published (`results-mv2-nugget/`).

## Checks: 7 of 7 held

| check | result |
|---|---|
| C1 `fetch_public.py` exits 0 (2 files at their pins; `medaesqa_nugget.py` at `5c2f2ca` declares 0.2.0) | exit 0; all 3 match; marker `VERSION = "0.2.0"` |
| C2 `test_mv2_nugget`: 7 tests, all pass | "Ran 7 tests", OK |
| C3 `wait_public.py` exits 0 | exit 0, match true |
| C4 run step exits 0, `problem` null | exit 0, null |
| C5 `mv2_answers` 65; all 40 questions mapped; `mv2_answered` 40; `nugget_fields` `{"nuggets": 40}` | 65 (698 sentences); 40 by id, 0 unmatched; 40; `{"nuggets": 40}` |
| C6 yardstick equals `medaesqa-nugget-v2`'s | expert control 89.5203, shuffled 0.0833, tau 0.4051 in both |
| K3 MV2 against the next question's nuggets <= 10 | 0.0 |

## Predictions: 3 of 5 held

| prediction | result | held? |
|---|---|---|
| M1 as written, MV2 beats fewer than 15 of the 30 runs at matched length | beats **0** (0 ties) | yes |
| M2 the ceiling beats at least 15 | beats **0** | no |
| M3 at 40 content words MV2 ranks 16th or lower of 31 | 31st | yes |
| M4 whole answers: MV2 ranks 1st of 31 | 28th | no |
| R1 run step at most 5 minutes | 0.9 s | yes |

## Decision

The rule applies only if `medaesqa-nugget-v2` made the matcher a yardstick or an equal-length
comparison. It did neither (`RESULTS-medaesqa-nugget-v2.md`: N3 failed), so **the numbers are
recorded and nothing is decided.** Had the rule applied, the ceiling's 0 of 30 would have been
outcome **C**: the facts the experts list are missing from MV2's candidate sentences, so sentence
selection cannot fix it.

## The numbers

Nugget recall at bar 0.6, in percent of each question's expert nuggets, averaged over 40 questions:

| budget (content words) | MV2 as written | MV2 rank of 31 | runs' median | best run | MV2 ceiling | runs' ceiling median |
|---|---|---|---|---|---|---|
| 20 | 2.24 | 31 | 10.50 | 13.77 | 5.33 | 15.30 |
| 40 | 4.10 | 31 | 14.59 | 17.30 | 7.09 | 17.95 |
| 60 | 4.62 | 31 | 17.01 | 20.73 | 7.09 | 18.13 |
| whole answer | 7.09 | 28 | 18.13 | 21.86 | 7.09 | 18.13 |

- MV2's whole answers average 137.6 content words (10.6 sentences), at least 1.5 times the
  longest run (88.4). Even so, they cover 7.1% of the experts' nuggets, against a median of 18.1%
  for the runs, every one of them shorter. Only the three shortest runs (webis-2, -3 and -5, 16-23
  content words) score lower.
- MV2's ceiling already reaches 7.09 at 40 content words: every nugget-covering sentence MV2 has
  fits in 40 words. More of the same sentences would not help.
- Matched length, run by run: MV2's recall is lower on 10-31 of the 40 questions and higher on
  0-3. The mean gap is -12.2 points (ceiling -9.8). Cutting at sentence boundaries leaves MV2 7.5
  content words short of each run on average, too little to explain a gap of this size.
- The ten 2024 runs whose names say the answer was written by the LLM alone (`*.llm_only*`,
  Llama-3 8B/70B; in the `rarr_*` ones citations were attached afterwards) reach 16.7-21.4%, about
  three to five times MV2's recall at the same length.

## What it suggests, and what it does not show

This does not test why MV2's sentences miss the facts. Three readings fit, and this job cannot
separate them: BM25 retrieval brings the wrong papers (only 32 of 65 questions have a judged
supporting paper in its top 5, `RESULTS-t2dev.md`); abstracts report study results ("in 120
patients, X lowered Y"), while experts write general facts ("X treats Y"); or word containment
favours the general wording LLM answers share with the experts. The matcher failed its own bar for
ranking systems, so the size of the gap is evidence, not a verdict.

For MV2's SPARK Task 2 entry this is still the clearest signal so far: quoting abstract sentences,
even the best ones, covers far fewer of the experts' facts than every LLM-written answer from 2024.
The extractive composer stays as the citation and grounding layer, not as the answer writer.

## Oddity

On webis-2 (16.2 content words per question) MV2's ceiling (1.90) is below its cut answer (2.24).
The cut always keeps MV2's first sentence even when it is longer than the run's whole answer, and
the ceiling never goes over budget. So at very short budgets the "ceiling" is not a strict bound.
It shows in the means only for webis-2 and changes no count above: on webis-2 the run's 5.81 is
above both.

## Limits

MV2's composer was tuned on these 65 questions (judged precision), not on nuggets. 40 questions,
30 runs from 5 teams. MV2 retrieves from the 2027 PubMed baseline that SPARK uses, while the runs
used 2024's. Length is counted in content words. No human has checked any count here.

## Files

`results-mv2-nugget/`: `mv2_nugget.json` (checks, yardstick cross-check, matched-length per run,
fixed budgets), `mv2_systems.json` (per system: recall, ceiling and words per budget),
`fetch_public.json`, `prereg_public.json`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
