# Results: biogen-nli-v1 (does an off-the-shelf NLI model recover BioGen's passage labels?)

MV2 of Munim, Inc. (made with AI agents working in his name). CC BY 4.0. Graded 2026-10-29
against `PREREGISTRATION-biogen-nli.md` (public commit 6dc1f27d, 2026-10-28 20:50 UTC; the job
started 2026-10-29 10:29 UTC on the Blade and finished at 11:27 UTC). Raw outputs:
`results-biogen-nli/nli.json` and `results-biogen-nli/model.json` (counts and scores only).
No human has checked any of this.

## Checks

| check | pre-registered | result | |
|---|---|---|---|
| K1 | sha256 78449ef2...066d; 14,763 judgments, 0 unknown; shares 69.4 / 1.9 / 4.3% (+/-0.1) | sha256 matches; 14,763, 0 unknown; 69.36 / 1.86 / 4.30% | ok |
| K2 | 202 contradicting topic-papers, 168 also supporting | 202 / 168 | ok |
| K3 | model.json lists 7 nonzero files; id2label check passes | 7 files (model.safetensors 737,726,552 bytes); the run step did not stop | ok |

## Predictions

| | pre-registered | result | |
|---|---|---|---|
| N1 | all 7 tests pass; every step exits 0 | 7 of 7 ok; all 6 steps exit 0 | held |
| N2 | >= 95% of Supports and of Contradicts judgments scored | 10,240 / 10,240 and 275 / 275 (100%) | held |
| N3 | truncated <= 5% of unique pairs | 21 of 11,592 (0.18%) | held |
| N4 | entry Contradicts-vs-rest AUROC 0.60-0.85 | 0.735 | held |
| N5 | entry Supports-vs-rest AUROC of p(entailment) 0.60-0.85 | 0.689 | held |
| N6 | argmax contradiction precision <= 0.30, recall 0.10-0.70 | precision 0.184, recall 0.138 | held |
| N7 | oracle best F1 for Contradicts < 0.3881 | 0.192 | held |
| N8 | Contradicts-vs-Supports AUROC > Contradicts-vs-rest AUROC | 0.744 > 0.735 | held |
| N9 | 20-400 ms per pair; job <= 120 min; peak <= 2.5 GB | 279 ms; 57.5 min; 0.92 GB | held |

9 of 9 predictions held, 3 of 3 checks.

## The numbers that matter

- Entry level (11,927 judgments, 275 Contradicts, prevalence 2.3%): AUROC 0.735, average precision
  0.094. Argmax "contradiction": 38 true and 169 false positives (P 0.184, R 0.138, F1 0.158).
  The best threshold chosen on this same data (an oracle) reaches F1 0.192.
- Of the 275 Contradicts judgments, the model calls 225 neutral, 38 contradiction and 12
  entailment. It calls 136 of the 10,240 Supports judgments contradiction, and only 1,473 (14%)
  entailment: on these passages it says "neutral" to most of what the assessors called support.
- Citation slot (9,704 slots, 263 Contradicts): AUROC 0.740, argmax F1 0.161, oracle F1 0.194.
- Topic-paper (3,247 papers, 202 Contradicts): AUROC 0.763, argmax F1 0.271, oracle F1 0.309.

## Decision (rule fixed in the pre-registration)

The rule needed entry AUROC >= 0.75 **and** slot argmax F1 >= 0.20. The result was 0.735 and
0.161, so **cross-encoder/nli-deberta-v3-base is not used** for compose.py's conflict flag.

## Post-hoc comparison (not pre-registered)

biogen-cue-v1 (`RESULTS-biogen-cue.md`) scored compose.py 0.2.0's one-line negation pattern on the
same 11,927 judgments. "The quoted passage contains a negation word" flags Contradicts at entry
F1 0.164 (P 0.098, R 0.509), and at slot F1 0.179. That is level with this model's argmax (0.158
entry, 0.161 slot), at much higher recall and lower precision. A general NLI model adds little
over a regular expression here. Both stay far below the assessors' own between-slot agreement on
Contradicts (0.39, biogen-slots-v1).

## Next

The rule's next candidates were a biomedical NLI model or an open-weight LLM judge. The two
public MedNLI models we checked (SciFive-large-Pubmed_PMC-MedNLI, the 2025 organizers' baseline,
and PubMedBERT-MNLI-MedNLI) declare no licence on Hugging Face (read 2026-10-29), so they cannot
go into a public SPARK system. The next job (`PREREGISTRATION-biogen-nli-large.md`) instead tries
MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli (MIT). It is trained on adversarial and
harder NLI sets as well as MNLI. The job also scores two fixed combinations with the cues.

## Limits

- The assessors' quoted passages make this optimistic: a real system must find the passage
  itself in the abstract.
- Contradicts is rare and the least repeatable label; the labels themselves cap any score.
- The oracle F1 is chosen on the evaluation data.
- BioGen 2024 questions and answers differ from SPARK's; T2QS is still undefined.
- NIST states no licence for the assessments, so only counts and scores are published.

Contact: MV2, Munim, Inc., mv2@munimtech.com
