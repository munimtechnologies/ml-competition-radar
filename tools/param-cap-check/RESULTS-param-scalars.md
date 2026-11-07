# Results: why two models' header counts differ from the Hugging Face API (param-scalars)

By AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com). Graded 2026-11-07.
Text CC BY 4.0; code Apache-2.0. Pre-registration: `PREREGISTRATION-param-scalars.md` (this folder).

## How it ran

- Sealed job paramscalars-v1 ran on 2026-11-07 from 00:37:57 to 00:41:10 UTC (python:3.12, 1 CPU,
  1 GB, network on).
- `fetch_dep.py` checked `param_parts.py` and `models.txt` against their git blob hashes. Both
  matched (`d02b5505...` and `6cb8553e...`), so the code that produced `RESULTS-param-parts.md` was
  reused unchanged.
- All 5 offline tests passed.
- The pre-registration was public before any header was read. `wait-public.json` shows the public
  copy's SHA-256 (`12736e59...`) equal to the local copy's, seen at 00:39:30Z. The headers were read
  at 00:40:07Z.
- Of 27 models, 24 were read. The same three gated models as before were skipped (no token is used):
  gemma-3-1b-it, Llama-3.2-1B-Instruct and Llama-3.2-3B-Instruct.
- Neither model with a gap had changed revision since 6 November: gemma-4-E2B-it is still at
  `4adf1574...` and Ministral-3-3B-Instruct-2512 at `b35d4dfe...`.
- Outputs: `out-param-scalars/param-scalars.json` (per-dtype counts from the headers and from the
  API, plus zero-dimensional tensors by dtype, part and last name component, for each model),
  `out-param-scalars/param-scalars.md` and `out-param-scalars/wait-public.json`.

## Grades (all or nothing, as pre-registered)

| # | Prediction | Grade | Evidence |
|---|---|---|---|
| S1 | Ministral-3-3B-Instruct-2512 has exactly 364 zero-dimensional tensors, all quant_scale, and its per-dtype counts match the API once each is counted as 0 | **held** | 364 zero-dimensional BF16 tensors, all quant_scale (182 `activation_scale`, 182 `weight_scale_inv`). Counting them as 0 gives BF16 822,899,712 and F8_E4M3 3,026,190,336, equal to the API. |
| S2 | gemma-4-E2B-it has exactly 928 zero-dimensional tensors, and its per-dtype counts match the API once each is counted as 0 | **held** | 928 zero-dimensional BF16 tensors. Counting them as 0 gives BF16 5,123,178,051, equal to the API. |
| S3 | Each of the 22 models that matched on 6 November has no zero-dimensional tensor, so the gap equals the number of zero-dimensional tensors for every model read | **held** | All 22 have 0 zero-dimensional tensors and a gap of 0. The gap equals the zero-dimensional count for 24 of 24 models read. |
| S4 | All of gemma-4-E2B-it's zero-dimensional tensors sit in its vision or audio tower | **held** | 480 audio and 448 vision; none elsewhere. Their names end in `input_min`, `input_max`, `output_min` or `output_max`, 232 of each. |

**4 of 4 held.** The rival guess, that the API leaves out a whole dtype, is ruled out. Both models'
API entries list the same dtypes the headers do (`dtypes_missing_from_api` is empty for every
model), and per dtype the only difference is the scalars.

## What this shows

On these 24 public models, the Hugging Face Hub's model-info `safetensors` totals count a
zero-dimensional (scalar) tensor as **0** parameters. The Hub's own Python client counts it as
**1**: `TensorInfo.__post_init__` in `huggingface_hub/utils/_safetensors.py` (checked on `main`,
2026-11-07) multiplies the shape and falls back to 1 when the shape is empty, with the comment
"scalar value has no shape". `param_parts.py` does the same. So `HfApi.model_info(...,
expand=["safetensors"])` and `HfApi.get_safetensors_metadata(...)` can give different totals for the
same commit of the same model. They differ by exactly the number of scalar tensors.

This is an observation of the API's output on public models, not of the server's code, which is not
public.

**Prior art (found after grading).** The pre-registration said we had found no public statement of
this. A search after grading found one: cheesecave-backend pull request #90 (merged 2026-10-15),
which rebuilds the Hub's `safetensors` summary from file headers, follows the rule "a tensor without
dimensions is not a parameter". Its notes report that also counting zero-dimensional tensors got 21
more repositories wrong, in a test against about 188 real Hub repositories
(https://github.com/cheesecave/cheesecave-backend/pull/90). So this check confirms a known behaviour
on another set of models, with each gap matched exactly by its scalar tensors and dtype by dtype. It
is not a first. We have not found the Hub team documenting the rule.

## Does it matter?

Not for any size cap: the gaps are 364 and 928 parameters, under 0.00002% of each model. No reading
in the 5 and 6 November tables changes. It matters to anyone who checks one source against the other
and expects them to match exactly, for example a test or a reproducibility check. In this sample the
scalars were of two kinds: per-tensor quantisation scales (Ministral's FP8 checkpoint) and
single-number bounds stored per layer (Gemma 4's `input_min`/`output_max` tensors). Other models of
either kind are likely to show the same gap, but that was not tested here.

## What changes in the tool

`param_parts.py` keeps counting a scalar as 1, like the Python client and like the safetensors
format, which treats a rank-0 tensor as one value. The README now says so and explains the
difference from the API. `param_scalars.py` reports both counts.

This closes the parameter-cap line of work: the 5 November table, the 6 November parts split and this
check are all graded.

## Limits

- 24 models, mostly small text and multimodal models. Other quantisation formats may store scale
  tensors differently.
- Three gated models were not read.
- The server's rule is inferred from its output (24 of 24 consistent), not read from its code.
