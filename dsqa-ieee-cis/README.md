# dsqa-ieee-cis

Open preparation by MV2 of Munim, Inc. (mv2@munimtech.com) for the IEEE CIS 2026 Technical Challenge
on Domain-Specific Question Answering with LLMs (DSQA). Made with AI agents working in his name.
Code Apache-2.0; text CC BY 4.0.

MV2 has **not** entered the contest yet (entry deadline 15 November 2026). Nothing here uses the
contest's hidden corpus, its Codabench platform, or its model.

## dsqa-retrieval-v1 (pre-registered 2026-11-06)

A CPU-only study of the retrieval half of a DSQA entry, on a 29-paper public proxy corpus built
around the organisers' public sample questions: how fast PyMuPDF and pypdf extract text, and how
often BM25, a MiniLM embedder and their fusion rank the right paper first.

- `PREREGISTRATION-dsqa-retrieval.md`: predictions P1-P7 and the decision rule, fixed before any run.
- `dsqa_retrieval.py`: the study (downloads PDFs at run time; writes only ids and scores).
- `corpus.json`: gold and distractor papers. `test_dsqa_retrieval.py`: unit tests (standard library).
- `wait_public.py`: the run waits until the pre-registration is public.

Results will be added as `RESULTS-dsqa-retrieval.md`; the pre-registration is never edited.

Starter kit and sample questions: github.com/jucls/IEEE-CIS-DSQA-Starter-Kit (MIT).
