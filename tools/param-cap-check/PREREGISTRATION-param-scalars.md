# Pre-registration: why two models' header counts differ from the Hugging Face API (param-scalars-v1)

By AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-11-06,
after `RESULTS-param-parts.md` and before any new header was read. Text CC BY 4.0; code Apache-2.0.

## Question

In `RESULTS-param-parts.md`, prediction P1 (our header count equals the API's `safetensors.total` for
every model read) failed on 2 of 24 models. Our count is 364 parameters higher for
mistralai/Ministral-3-3B-Instruct-2512 (exactly the 364 parameters we filed as quantisation scales)
and 928 higher for google/gemma-4-E2B-it. `param_parts.py` counts a zero-dimensional tensor (shape
`[]`, a single number) as 1 parameter. Our leading guess is that the API counts such tensors as 0.
The rival guess is that the API leaves out a whole dtype (Ministral's API entry lists only BF16 and
F8_E4M3; Gemma's lists only BF16).

## Method

`param_scalars.py` (this folder) re-reads the same safetensors headers by HTTP range request (no
weights, no token) for the 27 models in `models.txt`, using `param_parts.py` unchanged (the job checks
both files' git blob hashes first). For each model it reports parameters per dtype, the API's
parameters per dtype, the number of zero-dimensional tensors (by dtype, by part, by last name
component), and whether the gap equals that number.

## Predictions (graded next run, all or nothing per prediction)

- **S1.** Ministral-3-3B-Instruct-2512 has exactly 364 zero-dimensional tensors, all filed as
  quant_scale, and its per-dtype counts match the API once each of them is counted as 0.
- **S2.** gemma-4-E2B-it has exactly 928 zero-dimensional tensors, and its per-dtype counts match the
  API once each of them is counted as 0.
- **S3.** Each of the 22 models that matched the API on 2026-11-06 has no zero-dimensional tensor, so
  the gap equals the number of zero-dimensional tensors for every model read.
- **S4.** All of gemma-4-E2B-it's zero-dimensional tensors sit in its vision or audio tower.

If a model's revision (sha) differs from the one read on 2026-11-06, its prediction is graded on the
new revision and the change is reported. A model that cannot be read makes a prediction naming it
"not gradable".

## Why it matters

None of the 6 November cap readings can change: the gaps are under 0.00002% of each model. The point
is the tool: if S1-S3 hold, `param_parts.py` and the API disagree only on how to count a single
number, and the tool's README will say which count it reports. If the rival guess holds, the API's
total leaves out whole dtypes, and anyone checking a size cap from the API alone would undercount.

## Prior art and limits

We found no public statement of how the Hugging Face Hub server counts zero-dimensional tensors in
`safetensors.total`. The Hub's Python client counts them as 1 (`TensorInfo` in
`huggingface_hub/utils/_safetensors.py`, v0.26.0: "scalar value has no shape"), as `param_parts.py`
does, and the safetensors format allows rank-0 tensors as "merely a scalar". So if S1-S3 hold, the
server's model-info total and the client's `get_safetensors_metadata` disagree on such models. This
is an observation of the API's output on public models, not of its server code.
