# sparkdocs: the SPARK challenge pages' documents, read by a sealed job

Part of `spark-pubmed/`, MV2 of Munim, Inc.'s open groundwork for the NIH/NLM SPARK PubMed/PMC
Challenge. The code was made with AI agents working in his name. Code Apache-2.0; notes CC BY 4.0.

## Why

The challenge pages (https://repository.niddk.nih.gov/data-challenge/challenges/166 for Task 1,
`/199` for Task 2) link their rules and task descriptions through pre-signed download links that
expire minutes after the page is served. `fetch_docs.py` 0.1.0 reads each page, follows every
`.docx` and `.pdf` link at once, saves each file with its text, and records only the link's path
(never the signed query string). The documents themselves are not republished here; get them from
the challenge pages.

- `fetch_docs.py`: standard library, plus `pypdf` for PDFs (and `cryptography` for encrypted PDFs).
- `test_fetch_docs.py`: 3 fake-data tests, no network.

## What job `spark-docs-v1` found (2026-10-24, 12:22-12:24 UTC)

Each page links 6 documents. The rules `.docx` files, both task descriptions, both timelines and
the FAQ were read. The `2026_09_15` challenge announcement PDF is encrypted, and the job lacked
`cryptography`, so its text was not extracted; `spark-docs-v2` adds it.

Task 1 description (`PM-PMC-Task1-Description-and-Evaluation.pdf`), quoted:

- "Up to five (5) PubMed or PubMed Central items will be accepted and considered as candidate
  valid responses to each question for this task if all are appropriate; submissions will be
  penalized if they include incorrect citations. Participants can submit up to three (3)
  submissions for this task."
- "Note, only one these ranked items can be (potentially) correct. The primary evaluation metric
  for this task will be Mean Reciprocal Rank (MRR) across the questions."
- "The top N (expected to be five) systems based on Phase 1 MRR performance will advance to
  Phase 2." Phase 2 adds compute time and other criteria; "In the event of a tie in MRR, the
  additional evaluation criteria listed above may be used".
- "Submitted systems may use only publicly available, open-weight Large Language Models (LLMs),
  open-source software, and/or other publicly available computing resources." Docker images run
  in an isolated environment with no external network calls; models must be inside the image.
  The system is frozen and submitted as a Docker image by January 15, 2027.

How the "penalized" clause combines with MRR is not stated in the documents read so far: plain MRR
does not lower a score for wrong items after the right one. That is why `t1_runner/` scores ten
cutoff policies, not only "always five".

Task 2 description: 200 questions in Phase 1. The primary metric is Grounded Nugget F1 (nuggets
that are correct and supported by evidence from the corpus), folded with a conflict/controversy
detection F1 (CCA) as T2QS = w x GNF1 + (1 - w) x CCA; w is not given.

Eligibility rules: a private entity "shall be incorporated in and maintain a primary place of
business in the United States"; an individual must be a U.S. citizen or permanent resident and 18
or older. Each participant may enter "a maximum of three (3) submissions per track".

Limits: quotes are from the documents as fetched on 2026-10-24; the pages may change. No human
has checked this reading.

Contact: MV2, Munim, Inc., mv2@munimtech.com
