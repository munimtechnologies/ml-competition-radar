# SPARK Task 1 dev set R: 90 frozen known-item questions

MV2 of Munim, Inc. Written on 2026-10-22 (about 23:30 UTC) by AI agents working in his name,
**before any retrieval was scored on them**, following the R protocol fixed in advance in
[`../PREREGISTRATION.md`](../PREREGISTRATION.md). Questions and titles: CC BY 4.0. Code: Apache-2.0.

## What is here

| file | what |
|---|---|
| `r_questions.jsonl` | 90 rows `{pmid, question}`, one per record of the fixed-seed R pool (15 eligible records from each of pubmed27n0001, 0262, 0523, 0784, 1045, 1306), in pool order |
| `r_titles.jsonl` | `{pmid, title}` only, so the rule can be checked. No abstracts are republished. |
| `rq_rules.py` | the rule: no run of 3+ consecutive title words (lower-cased `[a-z0-9]+` tokens) in a question; each starts with "the "; at most 45 words |
| `test_r_questions.py` | fake-data tests of the checker, plus the check that all 90 frozen questions keep the rules |
| `check_titles.py` | re-checks the titles and the rule against PubMed's own titles (one NCBI E-utilities esummary call) |

## How the questions were written

Each question was written from the record's abstract alone, as "the study that ..." (or "the
trial / case / survey that ..."), in the words a researcher looking for that paper might use.
Every question was then hand-checked against its title for shared three-word runs. Two broke
the rule ("case report of", "in intermediate risk") and were reworded before freezing. The
test re-checks all 90 mechanically.

## What they are for

These questions are graded only once MV2's whole-corpus index exists. The prediction is **B4**: BM25 MRR@5
is between 0.20 and 0.60. The headline landmark set L and its predictions B1 to B3 are in the
same pre-registration.

## Limits

These are AI-written proxies, not NLM's expert questions. They reflect the abstract's main
finding, which may make them easier than real known-item needs, where a searcher half-remembers
a detail. The pool's oldest file, from the 1970s, is short on abstracts. Known-item question
sets exist for other literatures (for example LitSearch for computer-science papers), and
PubMedQA/BioASQ questions point to PubMed records. What is new here is only a small set that is
frozen before scoring and checked for leakage against the 2026 SPARK snapshot.
