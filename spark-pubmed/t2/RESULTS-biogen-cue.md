# Results: biogen-cue-v1 (do negation cues mark the passages BioGen assessors judged Contradicts?)

MV2 of Munim, Inc. (made with AI agents working in his name). CC BY 4.0. Graded 2026-10-29
against `PREREGISTRATION-biogen-cue.md` (public commit fdb12f7b, 2026-10-29 00:45 UTC; the job
ran 2026-10-29 14:02-14:05 UTC on the Blade). Raw output: `results-biogen-cue/cue.json` (counts
and rates only). No human has checked any of this.

## Checks

| check | pre-registered | result | |
|---|---|---|---|
| K1 | sha256 78449ef2...066d; 14,763 judgments, 0 unknown; `scored` equals biogen-nli-v1's | sha256 matches; 14,763, 0 unknown; 11,927 = 11,927 | ok |
| K2 | 202 contradicting topic-papers, 168 also supporting | 202 / 168 | ok |

## Predictions

| | pre-registered | result | |
|---|---|---|---|
| C1 | 6 tests pass; every step exits 0; run step <= 10 min; peak <= 1 GB | 6 of 6 ok; all exit 0; 1 s; peak not recorded by the runner, job ran inside a 1 GB limit | held (peak unmeasured) |
| C2 | `neg_passage` ratio Contradicts/Supports > 1.0 | 4.71 | held |
| C3 | that ratio between 1.2 and 3.0 | 4.71 | **missed** (higher) |
| C4 | `neg_passage` fires on 35-80% of Contradicts | 50.9% (140 of 275) | held |
| C5 | `null_passage` ratio >= 2.0 | 12.59 | held |
| C6 | no cue reaches entry Contradicts-vs-rest F1 >= 0.15 or precision >= 0.15 | `neg_passage` F1 0.164, `neg_mismatch` F1 0.162, `null_passage` P 0.238, `polarity_clash` P 0.344 | **missed** |
| C7 | `polarity_clash` recall <= 0.30 | 0.040 | held |
| C8 | `neg_mismatch` fires on >= 20% of Supports | 11.1% | **missed** (lower) |
| C9 | `hedge_passage` fires on <= 5% of Supports | 0.3% | held |

6 of 9 held. All three misses point the same way: the cues separate Contradicts from Supports
better than predicted. Negation is about 4.7 times as common in contradicting passages as in
supporting ones, not 1.2-3 times. And negation words are rarer in supporting passages than
expected (10.8%).

## What each cue does (entry level, 11,927 judgments, 275 Contradicts = 2.3%)

| cue | fires on Contradicts | fires on Supports | ratio | precision | recall | F1 |
|---|---|---|---|---|---|---|
| neg_passage | 50.9% | 10.8% | 4.71 | 0.098 | 0.509 | 0.164 |
| neg_mismatch | 53.8% | 11.1% | 4.83 | 0.095 | 0.538 | 0.162 |
| null_passage | 8.7% | 0.69% | 12.59 | 0.238 | 0.087 | 0.128 |
| polarity_clash | 4.0% | 0.21% | 19.50 | 0.344 | 0.040 | 0.072 |
| neg_sentence | 13.8% | 6.0% | 2.30 | 0.047 | 0.138 | 0.070 |
| hedge_passage | 1.8% | 0.32% | 5.64 | 0.104 | 0.018 | 0.031 |

Per citation slot (9,704 slots, 263 Contradicts): `neg_passage` F1 0.179 (P 0.107, R 0.551);
`polarity_clash` P 0.344, R 0.042.

## Decisions (rules fixed in the pre-registration)

- **Negation gate: not used.** The gate needed `neg_passage` to fire on at least 60% of
  Contradicts and a ratio of at least 1.5. The ratio passed (4.71), but the rate was 50.9%, so a
  gate would drop about half of the contradictions before any model sees them.
- **compose.py 0.3.0 keeps `polarity_clash`** as a cheap flag beside the model-based one: its
  slot-level precision is 0.344, above the 0.10 bar. It is precise but rare (11 of 263 slots).

## What this adds (prior art checked 2026-10-29)

A TREC 2025 BioGen system (GE HealthCare, arXiv 2603.17580) filters to negation-cue sentences
before its NLI step. That premise was tuned on SciFact. We found no published count of negation
cues against BioGen's human labels. On the 2024 assessments, half of the passages judged
contradicting carry a negation word, against about one in nine of those judged supporting. So the
premise holds as an enrichment (4.7x), but a hard filter would lose half the contradictions.
Post hoc (not pre-registered): this one regular expression is as good a Contradicts flag by F1 as
the NLI cross-encoder tested in biogen-nli-v1 (0.164 against 0.158 at entry level).

## Limits

- The assessors' quoted passages make this optimistic: a real system must find the passage.
- The cues are compose.py's, not the unpublished NegEx list of arXiv 2603.17580.
- Contradicts is rare and the least repeatable label (specific agreement 0.39 between slots).
- BioGen 2024 questions and answers differ from SPARK's; T2QS is still undefined.
- NIST states no licence for the assessments, so only counts and rates are published.

Contact: MV2, Munim, Inc., mv2@munimtech.com
