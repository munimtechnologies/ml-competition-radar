# Dis-Chem Product Data Enrichment Challenge (Zindi): day-one notes

Notes for entrants, written by MV2 of Munim, Inc. on 2026-11-13 (about 16:30 UTC), less
than two hours after the challenge opened. They were made with AI agents working in MV2's
name, from the public Zindi API (`api.zindi.world/v1/competitions/dischem-product-data-entichment-challenge`,
read 2026-11-13 ~16:25Z). MV2 has not entered yet and has not seen the data files. Text is
CC BY 4.0; any code in this repository is Apache-2.0.

Everything below is either a quote/paraphrase of the page (marked "page") or arithmetic
(marked "arithmetic"). Nothing here was checked against the real data. If the page changes,
the page wins.

## Facts (page)

- Task: enrich, validate and standardise product catalogue records for Dis-Chem (a South
  African pharmacy retailer) in **ten output fields** defined in `submission_format.json`.
  Three are text fields (`online_name`, `short_description`, `long_description`); the other
  seven "contain lists or structured objects". "If a detail cannot be verified, leave its
  output cell blank." Copy each `record_id` into `article_id`.
- Data: `Test_Masked.csv` **1,157** records; `unlabelled_data.csv` 13,864 records with no
  labels; `template_input.csv` / `template.csv` **14** worked examples; `product_images.zip`
  (~2.5 GB) with `image_mapping.xlsx`; a guardrail PDF, `columns.docx`, `submission_format.json`,
  `SampleSubmission.csv`. A `do_not_predict_fields` column lists fields that do not apply
  to a product; leave those blank. "Do not enter text such as N/A."
- Metric `llm_judge_data_enrichment`:
  - Text fields get a semantic quality score of 1.00 / 0.75 / 0.50 / 0.25 / 0.00, averaged
    over the products where that field has reference information.
  - Each structured field gets **one pooled F1**: TP, FP and FN are summed over all evaluated
    products, then F1 = 2TP / (2TP + FP + FN). Matching is by meaning; each reference value
    matches once; "Duplicate values and harmless, compatible details are not penalised";
    an "incorrect, conflicting, or otherwise unacceptable extra is a false positive".
  - A field with no reference information for a product is not evaluated for that product.
  - Overall = plain mean of the evaluated field scores, each field weighted equally.
  - The judge "does not consult product images or other sources". Scoring takes 30-40 min.
- Phase 1 runtime limits: 3 h end-to-end inference, US$20 all-in inference cost, one GPU
  with at most 24 GB VRAM, at most one retry per failed call.
- 2 submissions/day, 20 in total, choose 2 for the private board. Team max 4.
- Opens 2026-11-13 15:00Z; submissions close 2026-12-13 23:29Z. Top 10 give code (48 h;
  code that does not run is dropped); five go to Phase 2 (2026-12-25 to 2027-01-15), whose
  criteria are "provided when that phase launches".
- Prizes: US$2,500 / 1,500 / 1,000. Top 3 assign copyright in the winning solution to Zindi.
  Python only; provided data only; openly available pretrained models; no AutoML; "no paid
  services or free trials that require a credit card".

## Contradictions on the page (worth a forum question)

1. **Public/private split** is given as both ~30%/70% and ~20%/80%.
2. **Paid inference.** Phase 1 allows "US$20 maximum" all-in inference cost, but the rules
   forbid "paid services". The page never says whether a hosted LLM API is allowed.
3. **Data sharing** is listed as "No sharing permitted" in the summary, while the rules
   text allows sharing under CC-BY-SA 4.0.
4. **Filled `do_not_predict` cells.** The page says leave them blank, and also that fields
   with no reference are not evaluated. Whether a filled one counts as a false positive is
   not stated.

## What the metric rewards (arithmetic)

**1. When to fill a structured value: confidence above F/2.** For one structured field,
let N = 2TP and D = 2TP + FP + FN over the whole test set, so F1 = N/D. Add one candidate
value that is correct (matches an unmatched reference value) with probability p:

- correct: TP +1, FN -1 -> N + 2, D + 2 - 1 = D + 1
- wrong: FP +1 -> N, D + 1

Expected new F1 = (N + 2p)/(D + 1), which beats N/D exactly when **p > N/(2D) = F1/2**.
This is the known result that the F1-optimal threshold is half the achievable F1
(Lipton, Elkan and Narayanaswamy, "Optimal Thresholding of Classifiers to Maximize F1
Measure", ECML PKDD 2014). Pooling across products is what makes it apply here.

Worked example: TP 50, FP 20, FN 50 gives F1 = 100/170 = 0.5882. A candidate with
p = 0.35 gives (100.7)/(171) = 0.5889 (better); one with p = 0.25 gives 100.5/171 = 0.5877
(worse). The break-even is 0.5882/2 = 0.294.

So for a field where your system reaches F1 around 0.6, a value that is right only one
time in three is still worth emitting. "Leave blank if unverified" is the content
guideline; the metric itself pays for any value above F1/2. Extras that are "harmless,
compatible" cost nothing, which lowers the real break-even further. Two cautions: the
guardrail PDF may define "unacceptable" more strictly than this suggests, and the rule
needs calibrated confidences, which brings us to point 3.

**2. Blank text fields are probably expensive.** Text scores are averaged over products
with a reference, and the lowest grade is 0.00. If a blank scores 0.00 (the page does not
say), each of the three text fields should be filled for every product unless its
`do_not_predict` list says otherwise. The three text fields are 30% of the overall score
(each of the ten fields weighs 10%).

**3. There are almost no labels.** Only 14 template records carry expected outputs; the
13,864 `unlabelled_data.csv` records have none. A local held-out set is therefore 14
records unless you build one from the unlabelled data yourself (and the page warns it is
"not ... a verified answer source for a test record"). Calibrating the F1/2 threshold
from 14 examples is weak, so the 20 public-board submissions are most of the feedback.
Spend some on threshold sweeps for the structured fields.

**4. Public-board noise.** The public part is about 231 products (20%) or 347 (30%). For a
text field with a per-product score spread of about 0.3 (assumed), the standard error of
the field mean is about 0.3/sqrt(231) = 0.020 or 0.3/sqrt(347) = 0.016. On the overall mean
of ten fields the noise is smaller, but leaderboard gaps under about 0.01 on the
public board should not decide your two final picks.

**5. Time budget.** 3 hours for 1,157 records is 10,800 s / 1,157 = **9.3 s per record**,
including image handling. Generating the three text fields one record at a time with a
7-8B vision-language model on a 24 GB GPU is tight at that rate. Batched inference (for
example vLLM) or a text-only pass for most fields, with images only where the text is
missing, leaves room.

## Status

MV2 has no Zindi account yet, so he has not downloaded the data or entered. These notes
will be updated if the page changes or the organisers resolve the contradictions above.

MV2, Munim, Inc., mv2@munimtech.com. Made with AI agents working in MV2's name.
