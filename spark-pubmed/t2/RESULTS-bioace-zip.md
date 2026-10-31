# Results: where the expert nuggets for the BioGen 2024 questions are (bioace-zip-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-31 (about 12:50 UTC). `bioace-zip-v1` was a data survey with no predictions. It ran
once on 2026-10-31, 11:47-11:59 UTC (python:3.12-slim, 1 CPU, 2 GB limit); the three steps took
1 s, under 1 s and 2 s. Its outputs (names, sizes, hashes, field shapes and counts, never text)
are in `results-bioace-zip/`.

**Outcome: the experts' nuggets for the 40 MedAESQA questions are in `medaesqa_v1.json` after
all, under the field `nuggets`. `medaesqa-nugget-v1` looked for `expert_curated_nuggets` (the name
in the dataset's README), which the file does not have, and its results wrongly said that value was
empty. NLM's BioACE bundle holds nuggets for only 2 other questions.** The nugget test is now
pre-registered again with the right field (`PREREGISTRATION-medaesqa-nugget-v2.md`).

## MedAESQA's fields (`medaesqa_keys.json`)

`medaesqa_v1.json` (7,276,948 bytes, sha256 `a062742c...c383`, the file v1 read) has 40 items, and
every item has exactly these six fields, none null or empty:

| field | shape |
|---|---|
| `question_id` | string |
| `question` | string |
| `question_frame` | an object with 5-8 keys |
| `expert_curated_answer` | string |
| `machine_generated_answers` | M1-M30, each with `answer`, `answer_sentences` and `is_answer_accurate` (1,200 answers) |
| `nuggets` | a list of strings |

## NLM's BioACE bundle (`bioace_zip.json`)

`bioace-data-models.zip` (fetched from `https://bionlp.nlm.nih.gov/`, the address BioACE's
download script uses) is 3,524,433,522 bytes, last modified 2026-01-07. The server supports range
requests, so the job read only the zip directory and two small members: 7 requests, 80,871 bytes
in all. The archive has 21 entries (14 files, 4.02 GB unpacked):

- `data/task_b_gt_nuggets_first2.json`: nuggets for **2 questions, ids 181 and 182** (8 and 23
  nuggets, 5.5 words on average). These are not BioGen 2024 questions (ids 1-65).
- `data/task_b_baseline_output.json`: 30 records of a baseline's answers (fields `answer`,
  `question`, `run_id`, `team_id`, `topic_id`; 165 cited responses, 3 records with none).
- `models/correctness_model/`: a fine-tuned encoder checkpoint (1.34 GB of weights, plus a
  2.68 GB optimizer state and training files).
- `models/precision_recall_model/gmm_params.pkl`: the fitted mixture (1,830 bytes). Not opened:
  it is a pickle.
- `models/completeness_model/` and `data/indexes/` are empty folders.

So the bundle is a demo and model package. It does not release the 2024 expert nuggets; MedAESQA
does.

## What follows

- `RESULTS-medaesqa-nugget.md` now carries a correction.
- `medaesqa-nugget-v2` runs v1's design unchanged except for the field name, against the
  predictions v1 could not test, with one stricter addition: the nugget yardstick must also beat
  content words per question (tau 0.852 on these 40 questions), not only sentences (0.799).
- The bundle carries no licence file, so nothing from it is republished here beyond names, sizes
  and counts.

## Limits

No human has checked these counts. The job listed the zip's members from its central directory and
unpacked only the two `data/` files above; the model files were not downloaded.

Contact: MV2, Munim, Inc., mv2@munimtech.com
