# Results: embcheck-2 (read by hand, 2026-11-12). Gate GQ failed, so no prediction is graded

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text CC BY 4.0; code
Apache-2.0. Pre-registration: [PREREGISTRATION-embcheck2.md](PREREGISTRATION-embcheck2.md). Code:
[telco_embcheck2.py](telco_embcheck2.py) 0.2.0 (reusing [telco_embcheck.py](telco_embcheck.py) 0.1.0 unchanged
from commit 4717478, [base_files_embcheck2.json](base_files_embcheck2.json)). Machine output:
[embcheck2.json](embcheck2.json) and [RESULTS-embcheck2-auto.md](RESULTS-embcheck2-auto.md). Run: 2026-11-12
13:48-14:20 UTC in a sealed container (CPU, peak memory 1.33 GB). All offline tests passed. The
pre-registration was public on GitHub before any stored vector was read, and the public copy matched the local
one byte for byte ([prereg_public_embcheck2.json](prereg_public_embcheck2.json), seen 13:57:50Z).

## Gate failure: 191 questions, not 300

The pre-registration required at least 300 3GPP-tagged questions (gate GQ) and said that if a gate failed, no
prediction would be graded. GSMA's `GSMA/ot-lite` file `test_teleqna.json` (revision `1c0f2eac`) holds only
**191** distinct questions whose trailing tag contains "3GPP", and all 191 were used. We did not count them
before pre-registering, and that was our mistake. Gate GA held: both cells resolved 10,000 of 10,000 sampled
vectors. **So P1-P6 stay ungraded.** The numbers below are exploratory. What the predictions would have
scored is shown only so that readers can see it, and is not counted as a result.

## Exploratory headline: the 254-character chunks are not hubs. They are almost never retrieved

Chunks exactly 254 characters long make up 8.3% of the sampled `otel-0.6b` vectors and 9.2% of the control
cell's vectors (`qwen3-embedding-0.6b`). Out of 1,910 top-10 slots (191 questions x 10), they took:

| cell | query encoding | 254-char chunks: slots taken | slots expected at base rate | questions with any in top 10 |
|---|---|---|---|---|
| otel-0.6b | Q (with instruction, the kit's default) | **2** | 158 | 2 of 191 |
| otel-0.6b | D (no instruction) | 4 | 158 | 4 of 191 |
| qwen3-embedding-0.6b (control) | Q (its own query instruction) | 1 | 175 | 1 of 191 |
| qwen3-embedding-0.6b (control) | D (no instruction) | 0 | 175 | 0 of 191 |

The pre-registered worry was the opposite. embcheck-1 found that the query instruction dominates these chunks'
stored vectors, and we expected them to crowd the top 10 for unrelated questions. They do sit much closer to
the bare instruction's encoding than long chunks do (median cosine 0.46 vs 0.09 in otel, 0.29 vs 0.17 in the
control). Even so, they almost never come near a real question.

**The instruction bug is not what keeps them out.** The control cell, built the standard way, shows the same
near-zero rate. **Shortness doesn't explain it either.** Chunks *shorter* than 254 characters get about their
fair share. In otel (Q), 21.3% of the sample is below 254 characters and takes 20.4% of the slots (ratio 0.96).
In the control the ratios are 0.91 (Q) and 1.20 (D). Whatever these exactly-254-character chunks are, dense
retrieval almost never surfaces them, in either cell, with either query encoding.

We have not read their text. The next study, [PREREGISTRATION-embcheck3.md](PREREGISTRATION-embcheck3.md), only
describes them (how many exist in the full index, whether they come in runs within a document, and what kind of
text they hold). With no relevance labels, nobody yet knows whether any contest answer lives in them.

## What the predictions would have scored (exploratory, not graded)

| id | prediction | value | would have |
|---|---|---|---|
| P1 | otel L254 base rate 5-25% | 8.29% | held |
| P2 | otel, Q: L254 ratio >= 2.0 | **0.013** (2 slots vs 158 expected) | **failed, in the opposite direction** |
| P3 | control, Q: L254 ratio <= 1.5 and below otel's Q ratio | 0.006 vs 0.013 | held, but only because both are near zero, which is not what it meant |
| P4 | otel: L254 ratio lower with D than with Q | 0.025 (D) vs 0.013 (Q) | failed (4 slots vs 2: noise) |
| P5 | otel L254 - LONG instruction affinity >= 0.2 and above the control's gap | 0.372 vs 0.116 | held |
| P6 | Q: N10 skewness higher in otel than control | 4.45 vs 5.35 | failed |

With 191 questions instead of 300, the main reading would not change. A 2-in-1,910 share against 158 expected
is far outside anything the smaller question set could explain. Even so, the gate was set in advance, and it
stands.

## Other exploratory observations

- **Hubs exist, but they are ordinary chunks.** In otel (Q), the chunk retrieved most often (TS 23.288, 187
  characters) appears in 9 of 191 top 10s. The 20 biggest hubs have instruction cosines of 0.03-0.36, and none
  is 254 characters. 86% of the sampled chunks are never retrieved at all (with 1,910 slots over 10,000
  chunks, most chunks would be missed anyway).
- **The base Qwen3 cell needs its query instruction.** Questions encoded *without* it in the control cell
  produce heavy hubness: one chunk (out of 10,000) lands in 42 of 191 top 10s, the top 1% of chunks take 51%
  of all slots, and N10 skewness is 16.3, against 5.3 with the instruction. In the otel cell, dropping the
  instruction changes little (skewness 3.71 vs 4.45; top 1% take 18% vs 19%).
- **Chunk length (for prompt budgets).** Character quantiles of the 10,000 sampled otel chunks are 132 / 254 /
  405 / 629 / 929 (5th / 25th / 50th / 75th / 95th percentile). We did not count tokens. Under
  [SCORING.md](SCORING.md)'s rule (B = 850), every retrieved chunk is paid for in token efficiency, so a
  median-length chunk has to earn its place.

## Deviations from the plan

1. Gate GQ failed (191 < 300 questions), as described above. The script stopped grading itself as designed.
2. The models ran in bfloat16 on CPU (recorded this time). That is coarser than the stored GPU float16
   vectors, but it cannot turn 158 expected slots into 2.

## Limits

These are 10,000 of about 1.06 million vectors per cell, taken in 40 blocks of neighbouring ids. The questions
are 191 public TeleQnA questions about 3GPP Releases 14-19, not the contest's questions. Only text_baseline
was checked, with one seed. There are no relevance labels, so this measures where chunks land, not whether
answers are found. Nothing here uses Zindi's data or is a contest submission.
