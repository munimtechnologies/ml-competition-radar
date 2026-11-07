# param-cap-check

Check open generative models against a contest's parameter cap and licence rule, using exact counts
from the models' own safetensors files instead of the size in their names.

Made with AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com). Code Apache-2.0;
tables and notes CC BY 4.0. Stdlib Python 3 only; no token, no downloads of weights.

## Why

Some contests cap model size. The IEEE HT x UNDP GenAI for Good Challenge (Zindi Phase 1) allows "one
generative model with no more than 3 billion parameters" under a permissive licence. Names mislead:
SmolLM3-3B stores 3.075B parameters, Granite 4.0 Micro 3.40B and Gemma 4 E2B 5.12B. See
`contest-notes/2026-11-05-3b-cap.md` for the table.

## Tools

- `param_cap_check.py`: for each Hugging Face model id in a list, reads `safetensors.total` and the
  declared licence from the public model API and gives a verdict at the cap (`ok`, `over-cap`,
  `licence`, `over-cap-and-licence`, `unknown-size`).

  ```
  python param_cap_check.py --models models.txt --cap 3e9 --out-dir out
  python -m unittest test_param_cap_check -v     # 13 offline tests
  ```

  `out/param-cap.json` and `out/param-cap.md` are the output of the sealed run on 2026-11-05 at
  21:03 UTC (27 models: 11 ok, 10 over-cap, 3 licence, 3 over-cap-and-licence).

- `param_parts.py`: splits each model's stored parameters into vision, audio, multi-token-prediction
  (MTP), per-layer embeddings, embeddings, lm_head, quantisation scales and the rest. It reads only
  the JSON header of each safetensors file with two HTTP range requests, at the exact commit the API
  reports, then gives the count under four readings of a cap: A every stored tensor; B without
  vision/audio towers; C also without MTP heads; D also without per-layer embedding tables. Gated
  models are skipped.

  ```
  python param_parts.py --models models.txt --cap 3e9 --out-dir out
  python -m unittest test_param_parts -v         # 14 offline tests
  ```

  Its first run is pre-registered in `PREREGISTRATION-param-parts.md` (six predictions, written
  before any header was read). `wait_public.py` makes the sealed job wait until that file is public.
  Results: `RESULTS-param-parts.md` (5 of 6 held) and `out-param-parts/`.

- `param_scalars.py`: for each model, compares the per-dtype counts from the headers with the API's
  and counts zero-dimensional (scalar) tensors by dtype, part and name. `fetch_dep.py` fetches
  `param_parts.py` and `models.txt` and checks their git blob hashes first.

  ```
  python fetch_dep.py
  python param_scalars.py --models models.txt --out-dir out
  python -m unittest test_param_scalars -v       # 5 offline tests
  ```

  Pre-registered in `PREREGISTRATION-param-scalars.md`; results in `RESULTS-param-scalars.md`
  (4 of 4 held) and `out-param-scalars/`.

## Which count this reports

`param_parts.py` counts a zero-dimensional tensor (shape `[]`, one number) as 1 parameter, as the
`huggingface_hub` Python client (`get_safetensors_metadata`) does. On the 24 public models checked on
2026-11-07, the Hub's model-info `safetensors.total` counts such a tensor as 0. So for a model with
scalar tensors, our count A is higher than the API's by exactly their number: +364 for
Ministral-3-3B-Instruct-2512 (per-tensor FP8 scales) and +928 for gemma-4-E2B-it (scalars named
`input_min`, `input_max`, `output_min` and `output_max` in its vision and audio towers). The other 22 models have no scalar tensors and match exactly. The same
Hub rule ("a tensor without dimensions is not a parameter") was noted earlier in
https://github.com/cheesecave/cheesecave-backend/pull/90. No gap is
anywhere near large enough to change a cap verdict.

## Limits

- Counts are what the repository stores. Organisers may count differently (for example, leaving out
  a vision tower or tied embeddings). This is evidence for asking them, not a ruling.
- `param_parts.py` assigns tensors to parts by name; an unfamiliar naming scheme lands in
  `text_core`. The per-model name prefixes in its JSON output let you check.
- Licences are as declared on the model card; read the licence itself before relying on it.
