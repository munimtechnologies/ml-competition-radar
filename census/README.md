# AI-rules census of ML competition platforms

A dated census of what machine-learning and data-competition platforms actually say
about AI-assisted entries, with verbatim quotes and the URL each quote came from.
It sits next to ml-competition-radar, which lists the competitions; this folder records
the rules that decide whether an entry made with AI help may take part.

Version 0.1.0, checked 2026-10-17. Made by MV2 of Munim, Inc. with AI agents working in his
name. Text and data in this folder: CC BY 4.0. Code in the repository: Apache-2.0.

## The finding

Of 9 platforms or contests whose primary terms were read on 2026-10-17, **none has a clause
about AI-assisted or AI-generated code**. Not one permits it, forbids it, or asks for it to be
disclosed. What actually binds an entry made with AI is indirect:

| Gate | Where it appears | Effect on an AI-made entry |
|---|---|---|
| Natural persons only | DrivenData ("Legal entities and organizations are not eligible for entry."), Kaggle ("Each Team member must be a single individual") | A company cannot be the entrant; a person must hold the account |
| Open-source / no paid services | Zindi ("no paid services or free trials that require a credit card"), bitgrit ("commercial or proprietary APIs ... strictly prohibited") | A commercial LLM API cannot run *inside* the solution; nothing is said about AI used to *write* it |
| AutoML ban | Zindi ("Automated machine learning tools such as AutoML are not permitted.") | Written for AutoML products; does not mention coding assistants or agents |
| Reproducibility audit | NeurIPS EEG/EMG 2026 (re-run training, ±2σ), bitgrit (fixed seeds), Zindi (code must run, "Always set the seed.") | An AI-made pipeline must be scripted and seeded like any other |
| Organisations welcome | ThinkOnward ("you" may mean "Your Organization"), NeurIPS EEG/EMG 2026 ("Industry, academia, students, and independents are all eligible") | A company can enter as itself |

The practical rule for anyone entering with AI help in 2026: check eligibility (person or
entity), keep every model and package open and reproducible, and disclose AI use in the
method write-up even though no platform asks, because every platform reserves the right to
disqualify entries that break "the spirit of the Competition".

## Files

- `ai-rules-census.json`: one record per platform with the quotes by topic, how the page was
  read (direct fetch, saved copy, or search snippet only), the platforms not covered and why,
  and the prior art checked.
- `ai-rules-census.md`: the same as a readable table.

## Why it is new

Searches on 2026-10-17 found no cross-platform tabulation of AI-assistance rules. The
mlcontests.com yearly reports describe how *winners* used LLMs; the mlcontests platform
matrix compares evaluation features; Nasios (arXiv:2604.08001, April 2026) surveys the
ecosystem without touching AI-tool rules. One paywalled paper ("Ethical guidelines for machine
learning competitions", AI and Ethics, 2026) compares Kaggle, AIcrowd and DrivenData rules and
could not be read, so it may overlap; that is the main limit of this claim.

## Limits

- One date. Per-competition rules can override every platform-wide term quoted here.
- Kaggle's rules pages are JS-rendered; its quotes come from search-result snippets.
- Quotes are fragments of at most 125 characters each; the URL carries the full text.
- "Not addressed" never means "allowed".

## How to update

Fetch each URL in `ai-rules-census.json`, search it for the same topics, replace the quotes,
bump `checked_utc` and the version. Add a platform by adding a record with the same keys.
