# Results: what is inside small open models' stored parameters (param-parts)

By AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com). Graded 2026-11-06.
Text CC BY 4.0; code Apache-2.0. Pre-registration: `PREREGISTRATION-param-parts.md` (this folder).

## How it ran

- The first sealed run (paramparts-v1) failed 2 of its 14 offline tests because of a slip in the
  test's own arithmetic, not in the code. The analysis never ran. The test was corrected and the job
  was filed again as paramparts-v2.
- paramparts-v2 ran on 2026-11-06 from 17:17 to 17:20 UTC. All 14 tests passed. The
  pre-registration was public before any header was read: `wait-public.json` shows the public copy's
  SHA-256 `24858a61...` equal to the local copy's, seen at 17:19:16Z. The headers were read at
  17:19:55Z.
- Of 27 models, 24 were read. Three are gated and were skipped because no token is used:
  gemma-3-1b-it, Llama-3.2-1B-Instruct and Llama-3.2-3B-Instruct.
- Outputs: `out-param-parts/param-parts.json` (every part, reading and tensor-name prefix per
  model), `out-param-parts/param-parts.md` (the table) and `out-param-parts/wait-public.json`.

## Grades (all or nothing, as pre-registered)

| # | Prediction | Grade | Evidence |
|---|---|---|---|
| P1 | Our stored count A equals the API's `safetensors.total` for every model read | **failed** | 22 of 24 match exactly. Ministral-3-3B-Instruct-2512: ours 3,849,090,412, API 3,849,090,048 (+364). gemma-4-E2B-it: ours 5,123,178,979, API 5,123,178,051 (+928). |
| P2 | Qwen3.5-0.8B, 2B and 4B have vision > 0 and MTP > 0; 4B's C is still over 3B | **held** | Vision 0.101 / 0.331 / 0.334 B; MTP 0.020 / 0.061 / 0.121 B; Qwen3.5-4B C = 4.206 B |
| P3 | gemma-4-E2B-it has vision, audio > 0 and per-layer embeddings > 1B; C over 3B, D under 3B | **held** | Vision 0.169 B, audio 0.307 B, per-layer embeddings 2.349 B; C = 4.647 B; D = 2.299 B |
| P4 | Ministral-3-3B has vision > 0 and B still over 3B | **held** | Vision 0.420 B; B = 3.429 B |
| P5 | SmolLM3-3B, Granite 4.0 Micro, 4.0 H-Micro, 4.1 3B, 4.2 3B and Phi-4-mini have no vision, audio, MTP or per-layer parts, and all four readings are over 3B | **held** | All four parts are 0 for all six. Readings 3.075 / 3.403 / 3.191 / 3.403 / 3.660 / 3.836 B |
| P6 | Of the seven Apache-2.0 models over the cap on 5 November, only gemma-4-E2B-it comes under 3B in any reading B, C or D | **held** | Only Gemma 4 E2B's D (2.299 B) is under. The other six stay over in every reading. |

**5 of 6 held.** The tensor-name prefixes were checked by hand. Qwen3.5's `mtp.*` tensors and
`model.visual.*` towers, Gemma 4's `audio_tower`, `vision_tower`, `embed_audio`, `embed_vision` and
`embed_tokens_per_layer`, and Ministral's `vision_tower` and `multi_modal_projector` were all filed
in the right part. No tower or head landed in text_core.

## Why P1 failed

Both gaps are tiny: 364 and 928 parameters, under 0.00002% of each model. No reading in the table
changes. Ministral's gap is exactly the 364 parameters we filed as quantisation scales.
`param_parts.py` counts a zero-dimensional tensor (a single number) as 1
parameter, and so does the Hugging Face Python client. Our guess is that the Hub server counts it
as 0. A follow-up job tests this, with its predictions fixed in advance in
`PREREGISTRATION-param-scalars.md`.

## What it means for a 3-billion-parameter cap

- **Gemma 4 E2B** stores 5.12 B parameters. Per-layer embedding tables make up 2.35 B (46%) of that,
  and the vision and audio towers another 0.48 B. It fits a 3 B cap only if the organisers leave out
  both the towers and the per-layer embeddings (2.30 B). The rule says "parameters" and does not
  suggest that, so ask before relying on it.
- **Ministral 3 3B** is still 3.43 B with its vision tower removed.
- **Qwen3.5** stores a vision tower and an MTP head. Qwen3.5-2B's text-only core is 1.88 B. Even
  without both parts, Qwen3.5-4B is 4.21 B.
- The other "3B"/"micro" models are text-only, so no reading of the rule brings them under the cap.
- The safe, permissive choices stay the ones in the 5 November note: Granite 3.3 2B (2.53 B),
  Qwen3.5-2B (2.27 B stored) and Qwen3-1.7B (2.03 B).

## Limits

Parts are assigned from tensor names, which is a heuristic, and organisers may count in other ways.
Gated models were not read. This counts what is stored, so tied embeddings count once.
