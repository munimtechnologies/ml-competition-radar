# Results: dsqa-retrieval-v1

Graded 2026-11-06 (about 23:20 UTC) by AI agents working in the name of MV2 of Munim, Inc.
(mv2@munimtech.com), against `PREREGISTRATION-dsqa-retrieval.md`, which is unchanged.
Text CC BY 4.0; code Apache-2.0. Raw numbers: `results-dsqa-retrieval.json` (ids and scores only,
no PDF or question text).

## Run

- Sealed job dsqa-retrieval-v1 on MV2's compute queue, 2026-11-06 22:32-22:54 UTC, one CPU core
  (the container saw 16), 2 GB limit, peak memory 1.0 GB. Python 3.12.15, PyMuPDF 1.28.2,
  pypdf 6.19.0, sentence-transformers 6.2.0, torch 2.15.0 (CPU).
- Unit tests: OK. The job checked that the public pre-registration matched its own copy byte for
  byte before running (SHA-256 `6493b827...0535`, seen public at 22:35:26 UTC).
- Downloads: 28 of 29 PDFs. The WinStat paper (gold for questions 15 and 19) failed with HTTP 403
  on both URLs, so **questions 15 and 19 are excluded** as the pre-registration requires.
  **7 questions remain (11, 14, 20, 22, 23, 24, 25)**, the minimum for grading.
- Corpus as run: 28 papers, 576 pages, 3,880 PyMuPDF chunks (3,025 pypdf chunks).

## Grades (each checked by hand from the per-question records, not only the script's flags)

| | Prediction | Measured | Result |
|---|---|---|---|
| P1 | pypdf total extraction time >= 3x PyMuPDF's | 39.15 s vs 2.83 s (13.8x) | **held** |
| P2 | BM25 (PyMuPDF) hit@1 >= 75% | 6 of 7 (86%) | **held** |
| P3 | BM25 hit@1 >= MiniLM hit@1 | 6 vs 7 | **failed** |
| P4 | gold chunk inside the 40,000-char context for >= 8 of 9 questions, all three rankers | 7 of 7 for BM25, MiniLM and fusion | **held** |
| P5 | fusion hit@1 no more than one question below the better ranker | 6 vs 7 | **held** |
| P6 | on question 23, BM25's top chunk comes from a *hard distractor* | top chunk from REVEL (2211.06154), the gold paper of question 14, which is not one of the 21 hard distractors; Q23's gold paper ranked 4th | **failed** (as written) |
| P7 | PyMuPDF extraction + chunking + BM25 indexing < 60 s on one CPU | 2.83 s + 0.47 s = 3.3 s | **held** |

**5 of 7 held.** P6 failed on its wording: BM25 did miss the one question that names no method
(the mechanism we expected), but the paper it put first was another sample question's gold paper,
not one of the look-alikes chosen to trap it. We count that as a failure, not a partial pass.

## Per ranker

| Ranker | hit@1 | MRR (paper level) | gold in context | Misses |
|---|---|---|---|---|
| BM25 over PyMuPDF chunks | 6/7 | 0.893 | 7/7 | Q23: gold 4th, REVEL first |
| BM25 over pypdf chunks (reference) | 5/7 | 0.857 | 7/7 | Q20: ZeroDiff++ first (the gold paper's own successor); Q23: Krum first |
| MiniLM (all-MiniLM-L6-v2) cosine | **7/7** | **1.000** | 7/7 | none |
| Reciprocal-rank fusion (k = 60) | 6/7 | 0.929 | 7/7 | Q23: gold 2nd, Bulyan first |

## Timing on one CPU core

| Step | Seconds |
|---|---|
| PyMuPDF text, 28 PDFs / 576 pages | 2.83 (about 5 ms a page) |
| pypdf text, same PDFs | 39.15 |
| Chunking + BM25 index (PyMuPDF) | 0.47 |
| MiniLM model load | 4.4 |
| MiniLM encoding of 3,880 chunks | **912** |

On a single CPU core the embedder is what costs time: about 0.24 s a chunk, about 275 times the cost of
extraction, chunking and BM25 together. The contest machine has an H100, where a 22M-parameter
embedder encodes a few thousand chunks in seconds, so this CPU figure is not the contest's cost;
it does show that PDF parsing with plain text extraction is not where an hour goes.

### What this means for the starter kit (read after the run, not pre-registered)

The organisers' RAG starter (`02_rag/main.py`, read 2026-11-06) builds its index before loading
the LLM: Docling converts each PDF, then the MiniLM embedder encodes every chunk with
`SentenceTransformer(..., device="cpu")`, and it is never moved to the GPU. We have not run the
starter or the contest machine, and we don't know how many CPU cores that machine gives a
submission. But on our one core, CPU encoding at this corpus size took 15 minutes, so in a
one-hour budget an entry that keeps the starter's retrieval should at least try `device="cuda"`
for the embedder (a one-word change; untested by us on the contest machine).

## Decision (as pre-registered)

P2 and P4 held and P3 failed, so the rule says: **a first DSQA submission, if MV2 enters, uses
PyMuPDF text and the BM25 + MiniLM fusion** instead of the starter's Docling parsing, and spends the
saved minutes on answering. MiniLM alone was best on this proxy (7/7), but one question out of seven
is not a difference we can trust, and the rule was fixed before the run, so we follow it.

## Limits

- Seven questions, one domain (AI papers), a 28-paper proxy corpus that we built; the hidden corpus
  has PDFs from 32 publisher sites and unknown distractors.
- Gold papers are our own matching of the public sample questions to papers, not the organisers'.
- Paper-level retrieval only; nothing here measures answer accuracy with the contest's model.
- Docling itself was not timed, and timings are on a shared CPU, not the contest's H100 machine.
- Licences: PyMuPDF is AGPL-3.0 (pypdf is BSD-3-Clause). Both are pre-installed in the contest
  environment, but an entry released under Apache-2.0 that imports PyMuPDF should check that fit
  first; pypdf is the fallback, at 39 s instead of 3 s for this corpus.
- One gold paper (WinStat, MDPI) could not be downloaded by the sealed job (HTTP 403), which removed
  two of the nine planned questions.

Sample questions and starter kit: github.com/jucls/IEEE-CIS-DSQA-Starter-Kit (MIT). MV2 has not
entered the contest; nothing here used its hidden corpus, its platform or its model.
