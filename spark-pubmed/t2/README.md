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
not public yet (its TREC data page lists topics only, read 2026-10-28).

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
| biogen-nli-v1 | `PREREGISTRATION-biogen-nli.md` | (queued 2026-10-28) | |
| biogen-cue-v1 | `PREREGISTRATION-biogen-cue.md` | (queued 2026-10-29) | |

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
labels would already be near the 2025 state of the art. biogen-cue-v1 tests the negation premise
on BioGen 2024's human labels.

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
A BioGen 2025 paper reports that contradicting evidence is rarer and often expressed through
negation, hedging or population-specific conditions (arXiv 2603.17580). Negation cues alone will
miss many conflicts. This baseline is the floor that a later open-weight rewriting stage must
beat.

## First end-to-end numbers (`RESULTS-t2dev.md`)

BM25 over all 39,167,523 records, then `compose.py`, on the 65 BioGen questions:

- A paper judged Supports is in BM25's top 5 for 32 of 65 questions, top 20 for 55, top 100
  for 59 (top-5 MRR 0.317). Median query 15.8 s; median answer 247 words, composed in 48 ms.
- 72.9% of the answers' citations were never judged (no 2024 run cited them); 16 answers have no
  judged citation at all. Of the judged citations, 75.7% are Supports or mixed papers.
- The negation-cue conflict flag fired on no answer, although 10 answers cite a mixed paper.

## A model-based conflict flag: `nli_check.py` 0.1.0 (biogen-nli-v1, queued)

Before replacing the negation cues, `nli_check.py` measures how well an off-the-shelf NLI
cross-encoder (cross-encoder/nli-deberta-v3-base, Apache-2.0, pinned revision, CPU) recovers the
assessors' labels when it sees exactly what they judged: the quoted passage of the cited paper as
premise and the answer sentence as hypothesis. It reports AUROC, average precision, argmax and
oracle-threshold F1 for Contradicts per judgment, per citation slot and per topic-paper, and the
full label-by-prediction table. Outputs are counts and scores only. The decision rule (use this
model for compose.py 0.3.0's flag, or move to a biomedical NLI model or an LLM judge) is fixed in
`PREREGISTRATION-biogen-nli.md`.

## Do the cues mark contradictions at all? `cue_check.py` 0.1.0 (biogen-cue-v1, queued)

`cue_check.py` (standard library only) applies compose.py 0.2.0's own cue patterns, copied
verbatim, to the same passage/sentence pairs: negation, null finding and hedging in the passage,
negation in the sentence, a negation mismatch between the two, and compose.py's conflict rule
(one side reports no effect, the other a finding). For each cue it reports how often it fires per
label, the ratio of its rate among Contradicts to its rate among Supports, and precision, recall,
F1 and lift as a Contradicts flag per judgment and per citation slot. Counts and rates only.
`PREREGISTRATION-biogen-cue.md` fixes whether a negation gate goes in front of the model-based
flag and whether compose.py 0.3.0 keeps its cue flag.

## Next

1. Grade biogen-nli-v1 and biogen-cue-v1 against their pre-registrations and follow their
   decision rules.
2. Then rerun these 65 questions on the chosen Task 1 system (MedCPT cross-encoder at depth 150,
   `../system/`), compose again, and score the same way.
3. Then an open-weight stage for conflicts and rewriting, measured on judged precision and on how
   many citations were judged at all.

Helpers: `t2dev.py` (wait, download pins, gold files) and `fetch_code.py` (fetches the published
t1_runner, t2 and rerank code at pinned commits and checks each file's size).

Contact: MV2, Munim, Inc., mv2@munimtech.com
