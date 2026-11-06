# dsqa-ieee-cis

Open preparation by MV2 of Munim, Inc. (mv2@munimtech.com) for the IEEE CIS 2026 Technical Challenge
on Domain-Specific Question Answering with LLMs (DSQA). Made with AI agents working in his name.
Code Apache-2.0; text CC BY 4.0.

MV2 has **not** entered the contest yet (entry deadline 15 November 2026). Nothing here uses the
contest's hidden corpus, its Codabench platform, or its model.

## dsqa-retrieval-v1 (pre-registered 2026-11-06, graded 2026-11-06)

A CPU-only study of the retrieval half of a DSQA entry, on a 29-paper public proxy corpus built
around the organisers' public sample questions: how fast PyMuPDF and pypdf extract text, and how
often BM25, a MiniLM embedder and their fusion rank the right paper first.

**Result: 5 of 7 predictions held** (`RESULTS-dsqa-retrieval.md`). PyMuPDF extracted 576 pages in
2.8 s, 13.8 times faster than pypdf. On the 7 gradable questions MiniLM put the right paper first
7 times, BM25 6 and their fusion 6; the right paper fit in the context window every time. BM25 did
not beat MiniLM (P3 failed), so the pre-registered rule picks PyMuPDF text with the BM25 + MiniLM
fusion for a first entry.

- `PREREGISTRATION-dsqa-retrieval.md`: predictions P1-P7 and the decision rule, fixed before any run.
- `RESULTS-dsqa-retrieval.md`: grades, per-ranker table, timings and limits.
- `results-dsqa-retrieval.json`: the job's raw output (ids, timings and scores only).
- `dsqa_retrieval.py`: the study (downloads PDFs at run time; writes only ids and scores).
- `corpus.json`: gold and distractor papers. `test_dsqa_retrieval.py`: unit tests (standard library).
- `wait_public.py`: the run waits until the pre-registration is public.

The pre-registration is never edited.

Starter kit and sample questions: github.com/jucls/IEEE-CIS-DSQA-Starter-Kit (MIT).
