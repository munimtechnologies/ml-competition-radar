# Pre-registration: what is inside small open models' stored parameters (param-parts-v1)

By AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-11-06,
before any safetensors header was read. Text CC BY 4.0; code Apache-2.0.

## Question

Our 5 November note (`contest-notes/2026-11-05-3b-cap.md`) counted every stored tensor and found seven
Apache-2.0 models named "3B", "micro" or "E2B" over the GenAI for Good Challenge's cap of "one generative
model with no more than 3 billion parameters". The rule does not say whether a vision or audio tower,
a multi-token-prediction (MTP) head or per-layer embedding tables count. How much of each model is
those parts, and does any of the seven fit under a narrower reading?

## Method

`param_parts.py` (this folder) reads only the JSON header of each model's safetensors files, using two
HTTP range requests per file at the commit the Hugging Face API reports (no weights are downloaded and
no token is used, so gated models are skipped). It sums the parameters of every tensor and assigns each
tensor to one part by its name: vision, audio, mtp, per_layer_embed, embed, lm_head, quant_scale or
text_core. It reports four readings:

- A, stored: every stored tensor
- B: A minus vision and audio towers
- C: B minus MTP heads
- D: C minus per-layer embedding tables (Gemma's "effective" style)

Models: the 27 in `models.txt` (the 19 of the 5 November note plus 8 more). The job runs only after this
file is public, and records the public copy's hash in `wait-public.json`.

## Predictions (graded next run, all or nothing per prediction)

- **P1.** For every model whose headers are read, A equals the Hugging Face API's `safetensors.total`
  exactly.
- **P2.** Qwen3.5-0.8B, Qwen3.5-2B and Qwen3.5-4B each have vision > 0 and MTP > 0, and Qwen3.5-4B's C
  is still over 3,000,000,000.
- **P3.** gemma-4-E2B-it has vision > 0, audio > 0 and per-layer embeddings > 1,000,000,000; its C is
  over 3,000,000,000 and its D is under it.
- **P4.** Ministral-3-3B-Instruct-2512 has vision > 0 and its B is still over 3,000,000,000.
- **P5.** SmolLM3-3B, granite-4.0-micro, granite-4.0-h-micro, granite-4.1-3b, granite-4.2-3b and
  Phi-4-mini-instruct have vision = audio = MTP = per-layer embeddings = 0, so A = B = C = D, and all
  four readings are over 3,000,000,000.
- **P6.** Of the seven Apache-2.0 models over the cap in the 5 November note, gemma-4-E2B-it is the
  only one that comes under 3,000,000,000 under any of the readings B, C or D.

A model that cannot be read (HTTP error) makes any prediction naming it "not gradable", not "held".
If a part lands in text_core because of an unexpected tensor name, the per-model name prefixes in
`param-parts.json` will show it, and the grade will say so.

## What we will publish whatever happens

The table of parts and readings, the grade of P1-P6, and a dated addendum to the 5 November note. If
P3/P6 hold, the addendum will say that Gemma 4 E2B fits only if the organisers leave per-layer
embeddings out, which the rule's wording ("parameters") does not suggest, so entrants should ask before
relying on it.

## Prior art and limits

`huggingface_hub.get_safetensors_metadata` already reads safetensors headers by range request, and
Google publishes "effective" parameter counts for its E-series models. We know of no public per-part
table of small open models against a contest cap. Parts are assigned from tensor names, which is a
heuristic; organisers may count in other ways.
