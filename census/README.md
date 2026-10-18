# AI-rules census of ML competition platforms

A dated census of what machine-learning and data-competition platforms actually say
about AI-assisted entries, with verbatim quotes and the URL each quote came from.

Version 0.2.1, checked 2026-10-17 (EvalAI live challenges 2026-10-18). Made by MV2 of Munim,
Inc. with AI agents working in his name. Text and data: CC BY 4.0. Code in this repository:
Apache-2.0.

## The finding

Of 11 platforms or contests whose primary texts were read on 2026-10-17, **none has a clause
about AI-assisted or AI-generated code**. Not one permits it, forbids it, or asks for it to be
disclosed. What actually binds an entry made with AI is indirect:

| Gate | Where it appears | Effect on an AI-made entry |
|---|---|---|
| Natural persons only | DrivenData ("Legal entities and organizations are not eligible for entry."), Kaggle ("Each Team member must be a single individual") | A company cannot be the entrant; a person must hold the account |
| Open-source / no paid services | Zindi ("no paid services or free trials that require a credit card"), bitgrit ("commercial or proprietary APIs ... strictly prohibited") | A commercial LLM API cannot run *inside* the solution; nothing is said about AI used to *write* it |
| AutoML ban | Zindi ("Automated machine learning tools such as AutoML are not permitted.") | Written for AutoML products; does not mention coding assistants or agents |
| Reproducibility audit | NeurIPS EEG/EMG 2026 (re-run training, ±2σ), bitgrit (fixed seeds), Zindi (code must run, "Always set the seed.") | An AI-made pipeline must be scripted and seeded like any other |
| Organisations welcome | ThinkOnward ("you" may mean "Your Organization"), NeurIPS EEG/EMG 2026 ("Industry, academia, students, and independents are all eligible") | A company can enter as itself |
| No platform terms at all | EvalAI (each host writes its own terms; the official starter template's terms file was Lorem ipsum on 2026-10-17, but none of the 18 running challenges still used it on 2026-10-18) | Read each challenge's own terms; there is nothing above them |

The practical rule for anyone entering with AI help in 2026: check eligibility (person or
entity), keep every model and package open and reproducible, and disclose AI use in the
method write-up even though no platform asks, because every platform reserves the right to
disqualify entries that break "the spirit of the Competition".

## Files

- `ai-rules-census.json`: one record per platform with the quotes by topic, how the page was
  read (direct fetch, saved copy, or search snippet only), the platforms not covered and why,
  the prior art checked, and a change log. The EvalAI record carries the 2026-10-18 live check
  under `live_challenges_2026_10_18`.
- `ai-rules-census.md`: the same as a readable table.

## What changed in 0.2.1

All 18 challenges in EvalAI's public list of running challenges were checked on 2026-10-18
(the upcoming list was empty):

- **No placeholder terms.** None contains the starter template's Lorem ipsum text in any
  field. The question left open in 0.2.0 is answered: live hosts replace it.
- **The first explicit AI-tool clause, at challenge level.** The eBay 2026 University Machine
  Learning Competition - Canada (id 2680, Canadian university students only) asks "Can I use AI
  tools?" and answers with a data and licence rule, not an authorship rule: eBay data must not go
  into hosted generative AI tools that keep it, and AI-generated output "MUST NOT limit commercial
  use". No platform-wide terms mention AI tools, and none of the 18 terms fields does either.
- **Prize metadata can be wrong.** All 18 have `has_prize: false`. One of them (id 2672,
  CVPR 2026 Roboflow-20VL) lists $1,500 in cash prizes in its description, while its terms
  say "There are no prizes." Its API end date (2099) also disagrees with the deadline in its text
  (May 31, 2026). A radar built on platform metadata alone would get both wrong.

## What changed in 0.2.0

- Added EvalAI (host configuration docs and the official EvalAI-Starters template) and
  CrunchDAO (documentation landing page; its per-competition rules sit behind sign-up).
- Re-tried Numerai, Signate, Topcoder and HeroX. Their terms pages were JS-only, redirected to
  a JS-only page, or returned 404, so they stay under "not covered" with the reason, rather
  than being filled in from memory or snippets.

## Why it is new

Searches on 2026-10-17 found no cross-platform tabulation of AI-assistance rules. The
mlcontests.com yearly reports describe how *winners* used LLMs; the mlcontests platform
matrix compares evaluation features; Nasios (arXiv:2604.08001, April 2026) surveys the
ecosystem without touching AI-tool rules. One paywalled paper ("Ethical guidelines for machine
learning competitions", AI and Ethics, 2026) compares Kaggle, AIcrowd and DrivenData rules and
could not be read, so it may overlap; that is the main limit of this claim.

## Limits

- One date for the platform terms, one more for EvalAI's live list. Per-competition rules can
  override every platform-wide term quoted here.
- Kaggle's rules pages are JS-rendered; its quotes come from search-result snippets.
- The EvalAI and CrunchDAO records rest on documentation pages, not binding terms.
- The EvalAI live check covers only public, approved, running challenges.
- Quotes are fragments of at most 125 characters each; the URL carries the full text.
- "Not addressed" never means "allowed".

## How to update

Fetch each URL in `ai-rules-census.json`, search it for the same topics, replace the quotes,
bump `checked_utc` and the version, and add a line to `changes`. Add a platform by adding a
record with the same keys.
