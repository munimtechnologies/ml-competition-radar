# t2: groundwork for SPARK Task 2 (open-ended biomedical questions)

MV2 of Munim, Inc. (made with AI agents working in his name). Code Apache-2.0; notes CC BY 4.0.

## The task, as published (challenge page /challenges/199, read 2026-10-24)

- About 1,000 natural-language questions, released "shortly before the end of the challenge
  period" (the challenge runs 2027-01-15 to 2027-02-01). Prize $100,000 + $25,000.
- Responses must be "concise, objective, evidence-grounded responses with valid citations and
  relevant passages", scored on Grounded Nugget F1 and Conflict/Controversy Coverage. "T2QS"
  decides the ranking but is not defined yet. Ease of use, compute time, compute effort and
  memory in NIH's cloud are the tie-breakers.
- No output format, length limit or sample files are published yet ("Challenge Materials" is
  empty).

## Development data: TREC 2024 BioGen

No SPARK Task 2 questions are public. The closest public data we found is NIST's TREC 2024
BioGen track (overview: https://arxiv.org/abs/2411.18069). It has 65 health questions with
every PubMed citation from 30 runs judged by assessors. The file's own labels are "supporting",
"contradicting", "neutral", "not relevant" and "invalid citation", and every answer sentence is
judged Required, Unnecessary, Borderline or Inappropriate. The 2025 track recommends these
assessments for development (https://trec-biogen.github.io/docs/). Its answers are at most 250
words, with at most 3 PMIDs per sentence and 30 per answer. The 2025 track's own judgments are
not public yet (its TREC data page lists topics only and a placeholder for qrels, read 2026-10-28
and again 2026-10-30).

`biogen_census.py` downloads the topics and assessments, hashes them, and writes counts and
PMIDs only, never text: label totals, per-topic contradiction counts, per-run label shares, and
the PMIDs judged under each label per topic (`gold_t2.jsonl`). The data is used to develop and
evaluate only. Nothing from it goes into a submitted system. NIST states no licence for it, so
the judged-PMID file is not republished here until that is clear.

Every job was pre-registered before it ran and graded word for word:

| job | pre-registration | results | outcome |
|---|---|---|---|
| biogen-census-v1 | `PREREGISTRATION-biogen.md` | `RESULTS-biogen.md`, `results-biogen/` | 5 of 10; all misses one label-word defect in 0.1.0 |
| biogen-census-v2 | `PREREGISTRATION-biogen-v2.md` | `RESULTS-biogen-v2.md`, `results-biogen-v2/` | 9 of 10 |
| biogen-stance-v1 | `PREREGISTRATION-biogen-stance.md` | `RESULTS-biogen-stance.md`, `results-biogen-stance/` | 3 of 3 checks, 8 of 9 |
| biogen-stance-v2 | `PREREGISTRATION-biogen-stance-v2.md` | `RESULTS-biogen-stance-v2.md`, `results-biogen-stance-v2/` | 3 of 3 checks, 5 of 8 |
| biogen-stance-v3 | `PREREGISTRATION-biogen-stance-v3.md` | `RESULTS-biogen-stance-v3.md`, `results-biogen-stance-v3/` | 3 of 3 checks, 6 of 6 |
| biogen-slots-v1 | `PREREGISTRATION-biogen-slots.md` | `RESULTS-biogen-slots.md`, `results-biogen-slots/` | 4 of 4 checks, 8 of 8 (public commit came after the job; see results) |
| t2dev-v1 | `PREREGISTRATION-t2dev.md` | `RESULTS-t2dev.md`, `results-t2dev/` | 3 of 3 checks, 10 of 11 (memory missed; public commit 2 min after the job started) |
| biogen-nli-v1 | `PREREGISTRATION-biogen-nli.md` | `RESULTS-biogen-nli.md`, `results-biogen-nli/` | 3 of 3 checks, 9 of 9; model not adopted (AUROC 0.735 < 0.75) |
| biogen-cue-v1 | `PREREGISTRATION-biogen-cue.md` | `RESULTS-biogen-cue.md`, `results-biogen-cue/` | 2 of 2 checks, 6 of 9 (cues sharper than predicted) |
| biogen-nli-large-v1 | `PREREGISTRATION-biogen-nli-large.md` | `RESULTS-biogen-nli-large.md`, `results-biogen-nli-large/` | 3 of 3 checks, 8 of 10; model not adopted (AUROC 0.731 < 0.75) |
| t2sys-v1 | `PREREGISTRATION-t2sys.md` | not graded | ran on a machine with only a partial index; stopped by its guard before any prediction could be tested |
| t2sys-v2 | `PREREGISTRATION-t2sys.md` + `ADDENDUM-t2sys-v2.md` | not graded | the same machine again; tests passed with the corrected counts, then the guard stopped it |
| t2sys-v3 | the same + `ADDENDUM-t2sys-v3.md` | not graded | the same machine a third time (2026-10-30, 07:56-08:04 UTC); tests 14, 12, 11 and 9 (1 skipped) passed, then the guard stopped it |
| t2sys-v4 | the same + `ADDENDUM-t2sys-v4.md` | not graded (`results-t2sys-v4/guard.json`) | the same machine a fourth time (09:43-09:48 UTC); the same tests passed, then the guard stopped it |
| t2sys-v5 | the same + `ADDENDUM-t2sys-v5.md` | not graded (`results-t2sys-v5/guard.json`) | the same machine a fifth time (14:26-14:32 UTC); the same tests passed, then the guard stopped it |
| t2sys-v6 | the same + `ADDENDUM-t2sys-v6.md` | not graded (`results-t2sys-v6/guard.json`) | the same machine a sixth time (15:34-15:43 UTC), despite a 4 GB memory ask; the same tests passed, then the guard stopped it |
| t2sys-v7 | the same + `ADDENDUM-t2sys-v7.md` | not graded (`results-t2sys-v7/guard.json`) | the same machine a seventh time (19:30-19:37 UTC), despite a 5 GB ask; tests 14, 12, 11 and 9 (1 skipped) passed, then the guard stopped it (112 of 1,306 files). Not re-filed blind again |
| biogen-llm-v1 | `PREREGISTRATION-biogen-llm.md` | `RESULTS-biogen-llm.md`, `results-biogen-llm/` | 2 of 2 checks run; stopped by its own speed probe (189.1 s per pair), so no scores |
| biogen-llm-v2 | `PREREGISTRATION-biogen-llm-v2.md` | `RESULTS-biogen-llm-v2.md`, `results-biogen-llm-v2/` | stopped from outside (exit 143) at 600 of 1,389 pairs; checks C1-C2 and timing B1-B3 held |
| biogen-llm-v3 | the same + `ADDENDUM-biogen-llm-v3.md` | `RESULTS-biogen-llm-v2.md`, `results-biogen-llm-v3/` | 3 of 3 checks, 9 of 10 (gate AUROC 0.316, below the predicted range); not adopted (F1 0.0) |
| biogen-reuse-v1 | `PREREGISTRATION-biogen-reuse.md` | queued | can the 2024 sentence judgments grade a run outside the pool? Word overlap (below) |
| biogen-reuse-emb-v1 | `PREREGISTRATION-biogen-reuse-emb.md` | queued | the same test with all-mpnet-base-v2 embeddings, pre-registered before either version ran (below) |

What v2 counted: 14,763 citation judgments (69.4% supporting, 1.9% contradicting, 4.3% invalid);
55 of 65 topics have a contradicting judgment; 3,858 distinct PMIDs, all inside the SPARK
corpus's PMID range. Of the 202 papers judged contradicting an answer sentence, 168 (83%) are
also judged supporting another sentence in the same topic, and none is judged contradicting in
two topics.

What stance-v1 found: for 92 of those 168 papers (55%), the identical sentence text citing the
paper was judged both Supports and Contradicts. Only 28 were different sentences in one run's
answer, and 48 were only different runs' different sentences.

What stance-v2 added: over the 4,045 pairs of judgments of an identical (topic, sentence, PMID),
specific agreement is 0.85 for Supports but 0.22 for Contradicts (Neutral 0.31, Not relevant
0.42), and Scott's pi is 0.23. Most of those pairs (2,657) sit inside one run's answer, and
slots-v1 shows those are passages, not repeat judgments (below).

What stance-v3 settled: all 2,657 inside-one-run pairs of stance-v2 are one PMID listed 2 to 7
times in one sentence's citation list (1,867 such slots; 567 of them, 30.4%, with different
labels), and all 85 inside-one-run both-ways papers are of this kind.

What slots-v1 settled: **the released assessments are passage-level.** In 99.2% of the 1,867
repeated slots the entries quote different passages of the paper, and runs printed the PMID twice
in only 0.21%. Every one of the 567 slots with two labels has a different passage behind each
label. So most of stance-v1's 92 papers are papers with passages pointing both ways, which the
overview's rule ("no other sentence in the document contradicts the statement") makes Contradicts.
Between slots, at the paper level (802 pairs from different runs), Scott's pi is 0.47 (0.23 when
passages were mixed in, stance-v2). Contradicts is still the least repeatable label: specific
agreement 0.39, against Supports 0.90, Neutral 0.71 and Not relevant 0.47. Counting papers
instead of entries changes each run's support rate by at most 0.029 and contradict rate by at
most 0.036, but reorders 12-15 of 28 runs.

MedAESQA (Scientific Data 2025, PMC12179289), which releases 40 of these questions, already
reports lower annotator agreement within one item for Contradicting (67.67) than for Supporting
(82.09). No human has checked our counts yet.

## Can the 2024 judgments grade an answer nobody judged? (biogen-reuse-v1 and -emb-v1, queued)

A Task 2 answer from MV2's system is a new run: no assessor read it. BioGen 2024 scores
completeness by clustering the Required sentences of all 30 runs, **including** the scored run and
its own labels (overview Table 4), and reports no leave-out test. `biogen_reuse.py` (standard
library only) drops the scored run's whole team from the pool, hides its labels, and scores its
sentences by word overlap (Dice over content words, bar 0.5) with the other teams' Required
sentences. It then checks the proxy against each sentence's own label (AUROC) and against the
official per-run precision and completeness (Kendall tau over 30 runs, `official_biogen2024.json`
transcribed from Tables 3 and 4), next to a length-only baseline. The pre-registration fixes
10 predictions and a decision rule: the proxy is used to develop a rewriting stage only if it
separates Required sentences (AUROC >= 0.60) and ranks runs better than answer length does.
`wait_public.py` makes the job wait until the pre-registration is public.

`biogen_reuse_emb.py` runs the same test with cosine similarity of all-mpnet-base-v2 embeddings
(Apache-2.0, pinned commit and weights hash; one of the two models the overview names), primary
bar 0.7. It recomputes the word-overlap proxy on the same sentences and compares the two pair by
pair (a 1,000-resample topic bootstrap of the AUROC difference), and it runs `biogen_reuse.py`
unchanged as an agreement check. It was pre-registered (8 predictions) before either version
had run, so its bar could not be fitted to the word-overlap result. Decision rule: whichever proxy
passes becomes the yardstick (both: the higher AUROC, words on a near-tie); if neither passes, no
other variant is tried on the 2024 judgments.

## How hard is the conflict part? (TREC 2025 BioGen Task A, published numbers)

TREC 2025 BioGen Task A asked systems to add up to three supporting and three contradicting
PMIDs for each given answer sentence (40 questions, 194 sentences). Its overview (arXiv
2603.21582, Table 5) scores every run against Llama-3.3 labels (the BioACE framework):

- The best Contradicts F1 is 15.67 (InfoLab task_a_run2; P 14.09, R 19.42). The SciFive MedNLI
  baseline scores 4.67, and the GE HealthCare system, 2nd among teams, scores 8.57.
- Supports is far easier: the best Supports F1 is 67.74 (CLaC LLM_NLI_BM25).
- In the expert evaluation (10 topics, 244 abstracts judged) the baseline was the strongest on
  contradictions, at precision 8.33 and recall 10. The overview concludes that systems "struggle
  to identify contradictory citations".

The GE HealthCare system (arXiv 2603.17580) splits abstracts into sentences, keeps only sentences
with explicit negation cues (23 NegEx-derived patterns), and asks a MedNLI-tuned T5 model for
"contradiction". On its SciFact proxy, sentence-level checking gave a contradiction MRR of 0.750,
against 0.156 for whole documents. So a conflict flag that beats a stock NLI model on BioGen-style
labels would already be near the 2025 state of the art.

## Conflict flags measured on the 2024 human labels

All these jobs score the same 11,927 judgments (275 Contradicts, 2.3%). Each pairs the assessors'
quoted passage of the cited paper with the answer sentence, exactly what they judged.

| flag (entry level, Contradicts vs rest) | precision | recall | F1 | AUROC |
|---|---|---|---|---|
| NLI cross-encoder (nli-deberta-v3-base), argmax | 0.184 | 0.138 | 0.158 | 0.735 |
| same, best threshold chosen on this data (oracle) | | | 0.192 | |
| NLI large (DeBERTa-v3-large-mnli-fever-anli-ling-wanli), argmax | 0.315 | 0.149 | 0.203 | 0.731 |
| same, oracle threshold | | | 0.224 | |
| large, only where the passage has a negation word | 0.656 | 0.076 | 0.137 | 0.710 |
| large, or compose.py's polarity clash | 0.299 | 0.171 | 0.218 | 0.740 |
| Qwen2.5-0.5B-Instruct judge, only where the passage has a negation word | none called | 0.000 | 0.000 | 0.689 |
| negation word in the passage (compose.py's NEG_RX) | 0.098 | 0.509 | 0.164 | |
| null finding in the passage (NULL_RX) | 0.238 | 0.087 | 0.128 | |
| compose.py's polarity clash (null vs finding) | 0.344 | 0.040 | 0.072 | |

- **Negation is enriched but not a filter.** Half (50.9%) of the passages judged contradicting
  carry a negation word, against 10.8% of those judged supporting (4.7x). A negation-only gate,
  as in the GE HealthCare system, would drop about half of the contradictions, so none is used.
- **A bigger NLI model sharpens the calls but not the ranking.** The large model's
  "contradiction" calls are right 32% of the time (base 18%), but its AUROC is level (0.731 against
  0.735) and it calls 90% of supporting passages "neutral". Neither model met the pre-registered
  bar (AUROC >= 0.75 and slot F1 >= 0.20), so no NLI cross-encoder is used.
- compose.py keeps its 0.2.0 polarity-clash flag (slot precision 0.344): rare but precise. An
  earlier version of this page called that "compose.py 0.3.0"; there is no 0.3.0, because the
  decision needed no change to the code.
- Every flag stays far below the assessors' own between-slot agreement on Contradicts (0.39).

**An LLM judge inside the negation gate** (`llm_judge.py`): ask an instruction-tuned open model
whether each quoted passage supports the answer sentence, contradicts it, or neither, only where
the passage has a negation word (1,389 distinct pairs; 1,432 judgments, 140 of the 275
Contradicts), and score it with `nli_check.py`'s unchanged evaluation. Adopted only if entry
F1 >= 0.25, precision >= 0.30 and at most 10 s per pair.

- `biogen-llm-v1` (Qwen2.5-1.5B-Instruct, bfloat16, 4 threads on a 2-CPU limit) stopped itself
  after 20 pairs: 189.1 s per pair, far past its 6-hour budget, so it has no scores
  (`RESULTS-biogen-llm.md`). That is about 13 times slower than predicted.
- **The cause was bfloat16.** v2's and v3's timing checks (`RESULTS-biogen-llm-v2.md`) ran the
  same 335-token prompt on a 2-CPU limit: one forward pass took a median of 3.25 s and 2.92 s in
  float32, and 91.75 s and 85.28 s in bfloat16 (28 and 29 times slower). 4 threads were no faster
  than 2. All three timing predictions held in both runs, so later CPU jobs here load weights in
  float32. This is one shared machine and one prompt, not a general claim about CPUs.
- **The 0.5B judge (`biogen-llm-v3`, float32, 1.9 s per pair) answered "supports" for 1,429 of
  the 1,432 gated judgments and never "contradicts".** Its "contradicts" probability was lowest
  on the passages the assessors judged contradicting (mean 0.088, against 0.123 on Supports), an
  AUROC of 0.316 inside the gate, below the predicted 0.50-0.70. Overall (0.689) it ranks worse
  than the negation gate alone as a yes/no score (0.699). F1 is 0.0, so it is **not adopted**,
  and by the rule fixed in advance no larger LLM is tried as a conflict judge on the shared CPUs.
  One prompt, one small untuned model: a negative result for this setup, not for LLM judges.

## Baseline: `compose.py` 0.2.0 (extractive, cited, standard library only)

It writes no new prose. Every answer sentence is copied from a cited abstract, so every claim
is grounded by construction, and an answer takes milliseconds on a CPU. Steps: split the
abstracts of the top Task 1 candidates into sentences. Score each sentence by BM25 against the
question, plus a prior for the article's rank. Choose sentences by MMR up to 250 words, at most
2 per article; a near-copy of a chosen sentence becomes an extra citation instead of a repeat.
Flag a conflict when two chosen sentences from different articles share content words but one
reports a finding and the other reports none (negation cues). Flag uncertainty when a sentence
says the evidence is mixed or unclear.

`score` puts every cited PMID into exactly one class against the BioGen judgments: supports,
**mixed** (judged both Supports and Contradicts in the topic), contradicts (only), other (only
Neutral / Not Relevant), or unjudged. It reports each class's share of the citations, the recall
of all Supports papers and of Supports-only papers, how many mixed and contradicts-only papers an
answer cites, and how many of them its conflict flags hit. 0.1.0 counted a mixed paper as both
supporting and contradicting. That double-counted 168 of the 202 contradicting papers.

Pooled judgments only cover what 2024 runs cited, so an unjudged PMID is unknown, not wrong.

`compose_ro.py` 0.1.0 runs compose.py unchanged but opens the index read-only and immutable
(`../system/ro_db.py`), so it creates no `-wal`/`-shm` files beside a shared index and works where
the challenge image mounts the index read-only. `compare.py` 0.1.0 compares two `score` outputs
(judged precision, judged citations, per-topic higher/lower counts).

## End-to-end numbers so far

BM25 over all 39,167,523 records, then `compose.py`, on the 65 BioGen questions
(`RESULTS-t2dev.md`):

- A paper judged Supports is in BM25's top 5 for 32 of 65 questions, top 20 for 55, top 100
  for 59 (top-5 MRR 0.317). Median query 15.8 s; median answer 247 words, composed in 48 ms.
- 72.9% of the answers' citations were never judged (no 2024 run cited them); 16 answers have no
  judged citation at all. Of the judged citations, 75.7% are Supports or mixed papers.
- The negation-cue conflict flag fired on no answer, although 10 answers cite a mixed paper.

With the MedCPT cross-encoder reranking the top 50 BM25 candidates first
(`../rerank/RESULTS-spark36.md`): 70.0% unjudged, Supports share 21.7% (BM25: 16.9%), judged
precision 0.817 (BM25: 0.757); the conflict flag again fired on no answer.

## Next

1. `t2sys` (the 65 questions through the chosen Task 1 system, composed read-only, with BM25's
   answers recomposed as a control) has now landed seven times on a machine whose copy of the
   index is partial (112 of 1,306 files), and `host_guard.py` stopped each run after its tests, as
   designed. No prediction has been tested yet. The job runner picks the machine by free memory,
   and a job cannot choose it. As `ADDENDUM-t2sys-v7.md` said, the job is not re-filed blind
   again; it waits until it can be placed on the machine with the full index.
2. Meanwhile, `biogen-reuse-v1` and `biogen-reuse-emb-v1` (above) need no index and run on
   either machine. If a proxy passes its decision rule, it becomes the yardstick, fixed in
   advance, for an open-weight rewriting stage. A rewrite keeps the composer's citations, so
   judged precision alone cannot grade it.

Helpers: `t2dev.py` (wait, download pins, gold files) and `fetch_code.py` (fetches the published
t1_runner, t2 and rerank code at pinned commits and checks each file's size; the newest version,
0.4.0, is in `../system/`).

Contact: MV2, Munim, Inc., mv2@munimtech.com
