# Pre-registration: dsqa-retrieval-v1

Written 2026-11-06 (about 15:00 UTC) by AI agents working in the name of MV2 of Munim, Inc.
(mv2@munimtech.com), before any PDF in this study was downloaded, read by code, or scored.
Text CC BY 4.0; code Apache-2.0.

## Why

The IEEE CIS 2026 Technical Challenge on Domain-Specific Question Answering with LLMs (DSQA; prizes
$9,000 / $5,000 / $3,000 / $1,500 / $1,500; entry deadline 15 November 2026, final submissions
5 December 2026, per the organisers' timeline page) fixes the model (OLMo 3.1 32B Instruct) and gives
each submission one H100 for one hour, offline, for loading the model, reading a hidden PDF corpus
and answering about 100 questions. Participant repositories report that the organisers' RAG starter
(Docling PDF layout parsing, MiniLM embeddings, cosine retrieval, 800-character chunks) took about
36 minutes for the corpus plus 50 questions. So time spent on PDF parsing and retrieval is time not
spent on answering.

Every test of a real entry costs one of the contest's daily submissions. This study asks what can be
learned on a CPU, in public, before spending any: how fast plain text extractors are, and whether
BM25 finds the right paper as well as the starter kit's kind of embedder.

## Data

- Questions: the organisers' 25 public sample questions (sample/sample_qa.json in
  github.com/jucls/IEEE-CIS-DSQA-Starter-Kit, MIT). They are illustrative and not part of either
  leaderboard. Only the 9 "AI Papers" questions whose source paper we could match to an openly
  downloadable PDF are used: ids 11, 14, 15, 19, 20, 22, 23, 24, 25. The 10 IFMIF-DONES questions are
  left out because their likely sources are paywalled journal articles; ids 12, 13, 16, 17, 18, 21
  are left out because we could not identify their source with confidence.
- Gold papers (our matching, from public metadata, not the organisers'): OneSearch (arXiv
  2509.03236) for 11; REVEL (2211.06154) for 14; WinStat (MAKE 8(1):7, MDPI PDF, preprints.org as
  fallback) for 15 and 19; ZeroDiff (2406.02929) for 20; SimCLR (2002.05709) for 22; layerwise cosine
  (alpha,f)-Byzantine resilience (2503.21244) for 23; GPAIS (2307.14283) for 24; Mamba (2312.00752)
  for 25.
- Distractors: 21 "hard" look-alike papers chosen now, before any run (OneRec, semantic IDs,
  UniSearch, OneSearch-V2, OneVision, ZeroDiff++, X-SHIELD, an XAI-metrics paper, two fuzzy cognitive
  map papers, tAPE, Krum, Bulyan, two other Byzantine-robust FL papers, a GPAI definition paper,
  Mamba-2, S4, MoCo, BYOL, and the original Transformer). The list is in corpus.json.
- Questions whose gold PDF fails to download are excluded and reported. The study is graded only
  if at least 7 questions remain.

## Method (fixed now)

- Text: PyMuPDF 1.28.2 text blocks (joined with blank lines) and pypdf 6.19.0 page text, the
  versions pinned in the contest environment. Timed per document on one CPU.
- Chunks: blank-line paragraphs packed greedily into about 800 characters with a 150-character
  overlap, as in the starter kit; over-long paragraphs are split at spaces.
- Rankers over the PyMuPDF chunks: BM25 (k1 1.5, b 0.75, lowercase \w+ tokens, no stop words);
  sentence-transformers/all-MiniLM-L6-v2 cosine similarity; and reciprocal-rank fusion of the two
  (k = 60). BM25 is also run over pypdf chunks for reference only.
- Measures per question: whether the top chunk comes from the gold paper (hit@1); the gold paper's
  rank once chunks are collapsed to papers (MRR); and whether any gold chunk fits in a
  40,000-character context (about the starter's 10,000-token budget) filled in rank order.

## Predictions

- **P1.** pypdf's total extraction time over the corpus is at least 3 times PyMuPDF's.
- **P2.** BM25 over PyMuPDF chunks puts a gold-paper chunk first for at least 75% of the
  evaluated questions (7 of 9).
- **P3.** BM25's hit@1 is at least MiniLM's hit@1 (most sample questions name the method, a rare
  token BM25 weights heavily).
- **P4.** For BM25, MiniLM and the fusion alike, a gold chunk fits in the 40,000-character context
  for at least 8 of every 9 questions.
- **P5.** The fusion's hit@1 is no more than one question below the better of BM25 and MiniLM.
- **P6.** On question 23, the only evaluated question that names no method, BM25's top chunk comes
  from a hard distractor rather than the gold paper.
- **P7.** PyMuPDF extraction of the whole corpus plus chunking and BM25 indexing takes under 60
  seconds on one CPU.

## Decision rule

If P2, P3 and P4 hold, a first DSQA submission (if MV2 enters) uses PyMuPDF text and BM25 or the
fusion instead of Docling, and spends the saved minutes on answering. If P3 fails, it uses the
fusion. If P4 fails, retrieval needs more than a better extractor and gets its own study first.

## Limits, stated now

Nine questions from one domain; a 29-paper proxy corpus, not the hidden one, whose size and
distractors are unknown; paper-level, not answer-level, relevance; the CPU is not the contest
machine's. Docling itself is not timed here. This tells us about retrieval, not answer accuracy.

Run: sealed job dsqa-retrieval-v1 on MV2's compute queue; it waits until this file is public and
records whether the public copy matches the one it runs with.
