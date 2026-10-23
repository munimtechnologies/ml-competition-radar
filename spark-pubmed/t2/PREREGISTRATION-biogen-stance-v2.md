# Pre-registration: how repeatable is each BioGen 2024 citation label? (job `biogen-stance-v2`)

Written on 2026-10-23 at about 22:00 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why

`biogen-stance-v1` (`RESULTS-biogen-stance.md`) found that 92 of the 168 papers judged both
Supports and Contradicts in one topic got both labels on the identical sentence text. Of 130
repeated identical sentence-paper groups that include a Contradicts label, only 11 agree
completely, against 1,453 of all 2,084 groups. Raw agreement is not corrected for chance,
though, and Contradicts is rare. This job measures, on the same repeated judgments:

- the full pair matrix, with agreeing pairs (the diagonal) counted per label;
- specific agreement per label L: 2 x (pairs agreeing on L) / (2 x (pairs agreeing on L) +
  disagreeing pairs with L on one side);
- Scott's pi over all pairs (chance agreement taken from the pooled label shares of the pairs);
- agreement for pairs inside one run's answer vs pairs from two different runs;
- how many of the 92 `same_text` papers have both labels on that text inside one run.

Prior art (found while grading v1, before this file was written): MedAESQA (Scientific Data
12:1035, 2025; PMC12179289) releases 40 of the 65 questions and reports per-label majority
agreement among at least three annotators per item: Supporting 82.09, Contradicting 67.67,
Neutral 60.14, Not Relevant 100. That is agreement within one item. This job measures something
else: agreement between separately judged items that are identical (same topic, same sentence
text, same paper), using the released final labels.

## Fixed design

`biogen_stance.py` 0.2.0, standard library only. Every 0.1.0 output is unchanged, and the new
fields are added. Same input: `/data/biogen2024/assessments.json`, which must have sha256
`78449ef2...066d` (downloaded again only if missing). 12 fake-data tests: the 10 earlier ones,
some extended with hand-computed values for the new fields, plus a formula test and a within-run
fixture. 1 CPU, 1 GB, 30 minutes.

## Already known (checks, not predictions)

- C1. Every field printed by 0.1.0 is identical (14,763 judgments; 202/168/34; 92/114/28/48;
  2,084 groups; 4,045 pairs; 3,019 agree; the same six off-diagonal counts; 130 and 11).
- C2. The off-diagonal cells of `repeated_pair_matrix` equal `repeated_pair_confusion`; the
  diagonal cells sum to 3,019; within-run + across-run pairs = 4,045.
- C3. `mixed_same_text_within_one_run` <= 92.

## Predictions

- Q1. All 12 tests pass.
- Q2. Specific agreement for Contradicts < 0.40.
- Q3. Specific agreement for Supports >= 0.75.
- Q4. Specific agreement for Neutral < 0.50.
- Q5. Scott's pi is between 0.10 and 0.50.
- Q6. Across-run pairs are at least 80% of the 4,045 pairs.
- Q7. If there are at least 20 within-run pairs, within-run agreement is higher than across-run
  agreement.
- Q8. `mixed_same_text_within_one_run` <= 20: most one-claim disagreements are between runs.

How it will be read (written now): if Q2 and Q3 both hold, Contradicts is the least repeatable
label and Supports the most. A conflict-coverage score built on single Contradicts judgments
then inherits that noise. For development we would score mixed papers as their own class and
weight a Contradicts label by its repeatability, not treat it as gold. If Q2 fails, the v1
pattern mostly comes from how rare Contradicts is, and the stronger claim is withdrawn.

Limits (same as v1): identical text is a strict test; assessor identity and judging order are
not in the file; pairs inside one group are not independent, so no confidence intervals are
claimed.

Contact: MV2, Munim, Inc., mv2@munimtech.com
