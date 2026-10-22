# SPARK Task 1 dev sets: results of job spark29-dev-v1 (graded 2026-10-22, about 20:45 UTC)

MV2 of Munim, Inc. Graded by AI agents working in his name, against `PREREGISTRATION.md` in this
folder (written about 14:50 UTC and published before this output was read). Text CC BY 4.0.

Job: `spark29-dev-v1`, status ok, 2026-10-22 14:31-14:36 UTC, 107 NCBI E-utilities calls,
6 corpus files downloaded and md5-checked. Raw outputs: `results/dev.json`,
`results/landmarks_verified.json`.

## Grades (word for word against the pre-registration)

| # | Prediction | Result | Grade |
|---|---|---|---|
| A1 | >= 44 of 47 landmarks verify by some strategy | 46 of 47 | held |
| A2 | >= 38 of 47 verify by title words + year | 45 of 47 | held |
| A3 | >= 90% of verified landmarks have year_diff 0 | 46 of 46 (100%) | held |
| A4 | 8-18 verified landmarks carry a PMC id | 12 | held |
| A5 | no verified landmark has an excluded type | none | held |
| A6 | C01-C03 verify and fall outside the window; C04 not found | C01 1953, C02 1951, C03 1944 verified, none in window; C04 not found | held |
| A7 | no landmark ends with status `error` | 0 errors | held |
| R1 | all six corpus files download and match NLM's md5 | 6 of 6, no problems | held |
| R2 | pubmed27n0001 eligible share < 0.25 | 0.4255 | **missed** |
| R3 | pooled eligible share of the other five files 0.45-0.80 | 0.7817 | held |
| R4 | pool holds exactly 90 records, 90 distinct PMIDs | 90 / 90 | held |

**10 of 11 held.** R2 was wrong: the oldest file, which holds 1970s records, is not mostly
abstract-less. 42.6% of its records have a title, an abstract of at least 80 words and no excluded
publication type. The share rises steadily with file number: 0.43, 0.66, 0.77, 0.79, 0.84, 0.90.

## Hand check of every verified landmark

Every one of the 46 verified landmarks and 3 verified controls was read by hand. In each case the
PubMed title is the paper meant: the title ratio is 1.0 in every case, and the first author and
journal match the hint. Notes:

- **L17** (Zhou et al. 2020, bat-origin coronavirus) had a runner-up, PMID 33199918, at ratio
  0.945. PubMed's summary shows it is the December 2020 *Addendum* to the same paper (publication
  type Published Erratum). The tool correctly chose the original, PMID 32015507.
- **L34** (Zhu et al. 2020) had 8 hits for its title words. The exact title was chosen
  (PMID 31978945).
- **L30** (Towbin 1979, western blot) failed the title search (0 hits) but verified through
  first author + year + journal. That is the fallback working as designed.
- **L46** and the controls have all-capital titles in PubMed. The match lower-cases text, so they
  still score 1.0.

## Not found

- **L37** (Huntington's disease gene, Cell 1993): a **false negative of the verifier**. The
  title+year search returned exactly one hit, PMID 8458085. PubMed's summary (read 2026-10-22)
  shows the right paper, but its title ends with ". The Huntington's Disease Collaborative Research
  Group." and it has no personal author. That pushed the difflib ratio below 0.85. Decision, made
  after reading the output and labelled as such: L37 enters the headline set as a hand-verified
  item (PMID 8458085). The pre-registered A-grades above stay as computed (46).
- **C04** (Kaplan and Meier 1958, J Am Stat Assoc): title+year and author+year+journal returned 0
  hits. A title-only search returned one hit, which did not pass the title-ratio check. As
  predicted, the statistics journal paper is not a PubMed record.

## What the dev sets now hold

- **Headline L**: 43 landmarks after excluding the 4 contested ones (L24, L38, L40, L43): the 42
  that verified automatically plus L37 verified by hand. All are in the 1959-2026 window. Whether
  each one is in the SPARK snapshot is checked against the full index (B-grades) and not assumed.
- **R pool**: 90 records, 15 from each of six evenly spaced files. Questions for R are written
  next, from abstracts only, under the frozen protocol. They are published before any retrieval
  is scored on them.

## Limits

Landmark questions were written by AI agents and lean towards famous molecular biology. A PubMed
record is not proof that a paper is in the SPARK snapshot. The R2 miss means the earlier guess
that old records are mostly abstract-less was wrong for this corpus. It does not change the
B-predictions, which are graded only on the full index.
