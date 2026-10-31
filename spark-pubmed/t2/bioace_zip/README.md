# bioace_zip: where are NLM's expert nuggets for the BioGen 2024 questions?

MV2 of Munim, Inc. (made with AI agents working in his name). Code Apache-2.0; notes CC BY 4.0.

`medaesqa-nugget-v1` found the `expert_curated_nuggets` value empty in all 40 items of the public
MedAESQA file (`../RESULTS-medaesqa-nugget.md`). `bioace_zip.py` 0.1.0 (standard library only)
looks in two places:

- `python bioace_zip.py medaesqa --data-dir D --out-dir O` loads `medaesqa_v1.json` (pinned
  sha256 `a062742c...c383`) and writes `medaesqa_keys.json`: every item field with how often it is
  present, null or empty, and its structure. This tells "missing" from "null".
- `python bioace_zip.py zip --data-dir D --out-dir O` reads NLM's `bioace-data-models.zip` (the
  bundle BioACE's `download_data_models.sh` fetches) with HTTP range requests: the end record, then
  the central directory. It never downloads the whole archive. It lists every member's name and
  size, and unpacks only data files (`.json`, `.jsonl`, `.tsv`, `.csv`, `.txt`) whose names mention
  nuggets or ground truth, or that sit in a `data/` folder, within size caps (32 MB compressed per
  file, 128 MB in all). It checks each file's CRC, saves it under `D/bioace/`, and writes
  `bioace_zip.json` with each file's structure, record count, question ids and list lengths.

Output is names, sizes, field names, ids and counts only, never question, answer or nugget text.
BioACE's repository has no licence file and the bundle states none that we have seen, so nothing
from it is republished here. This is a data survey with no predictions; any test that uses what it
finds is pre-registered first.

`test_bioace_zip.py` (9 tests) builds a zip in memory and checks listing, unpacking, the size caps,
the zip64 fields, safe paths and the text-free descriptions.

Contact: MV2, Munim, Inc., mv2@munimtech.com
