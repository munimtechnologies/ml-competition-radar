# AI-rules census of ML competition platforms

A dated census of what machine-learning and data-competition platforms actually say
about AI-assisted entries, with verbatim quotes and the URL each quote came from.

Version 0.3.1, platform terms checked 2026-10-17 (EvalAI live challenges 2026-10-18; Zindi
competitions, ARC Prize 2026 and the U.S. DOE GEMS Prize checked 2026-10-21). Made by MV2 of
Munim, Inc. with AI agents working in his name. Text and data: CC BY 4.0. Code in this
repository: Apache-2.0.

## The finding

Of 13 platforms or contests whose primary texts were read, **no platform-wide terms have a
clause about AI-assisted or AI-generated code**. Clauses about AI tools exist only inside
single competitions, and three have been found:

- **Permission with a duty to disclose:** the U.S. Department of Energy's GEMS Prize ($300,000,
  on DrivenData; official rules dated September 2026) says "Using generative AI technology in the
  development of your prize submission is allowed." Entrants must state "the extent to which, if
  any, you used generative AI technology and how you used it to develop your submission". It is
  the only rule in this census that requires AI use to be disclosed. The rules say the disclosure
  goes "in the narrative", but no narrative is defined anywhere else in the 19-page rules or on
  the competition's DrivenData pages.
- **Permission without disclosure:** Zindi's Bias Bounty Mapping Equity Challenge ($10,000; rules
  updated 2026-10-06) says "General-purpose development assistants such as commercial LLM coding
  tools may be used for code drafting, debugging, testing" (and documentation), "provided they are
  not required to execute or reproduce the submitted solution." It is 1 of the 7 open Zindi
  competitions on 2026-10-21. The other 6 use Zindi's standard text, which allows only
  open-source "languages and tools in building models" and does not say whether a coding
  assistant counts.
- **A data and licence rule:** the eBay 2026 University ML Competition - Canada (EvalAI) keeps
  eBay data out of hosted AI tools and says AI output "MUST NOT limit commercial use".

What otherwise binds an entry made with AI is indirect:

| Gate | Where it appears | Effect on an AI-made entry |
|---|---|---|
| Natural persons only | DrivenData's standard template ("Legal entities and organizations are not eligible for entry."), Kaggle ("Each Team member must be a single individual") | A company cannot be the entrant; a person must hold the account. Contest rules can lift this: the DOE GEMS Prize on DrivenData admits U.S.-incorporated companies |
| Open-source / no paid services / no internet | Zindi ("no paid services or free trials that require a credit card"), bitgrit ("commercial or proprietary APIs ... strictly prohibited"), ARC Prize 2026 ("no API-based systems like GPT/Claude/etc.") | A commercial LLM API cannot run *inside* the solution; only Zindi's Bias Bounty and the DOE GEMS Prize say anything about AI used to *write* it, and both allow it |
| AutoML ban | Zindi ("Automated machine learning tools such as AutoML are not permitted.") | Written for AutoML products; does not mention coding assistants or agents |
| Reproducibility audit | NeurIPS EEG/EMG 2026 (re-run training, ±2σ), bitgrit (fixed seeds), Zindi (code must run, "Always set the seed."), ARC Prize 2026 (open source before private scores), DOE GEMS (finalists' code must reproduce the winning results) | An AI-made pipeline must be scripted and seeded like any other |
| Organisations welcome | ThinkOnward ("you" may mean "Your Organization"), NeurIPS EEG/EMG 2026 ("Industry, academia, students, and independents are all eligible"), DOE GEMS (U.S.-based companies, institutions and nonprofits) | A company can enter as itself |
| No platform terms at all | EvalAI (each host writes its own terms; the official starter template's terms file was Lorem ipsum on 2026-10-17, but none of the 18 running challenges still used it on 2026-10-18) | Read each challenge's own terms; there is nothing above them |

The practical rule for anyone entering with AI help in 2026: read the competition's own rules,
not only the platform's; check eligibility (person or entity); keep every model and package open
and reproducible; and disclose AI use in the method write-up even where no rule asks, because
every platform reserves the right to disqualify entries that break "the spirit of the
Competition", and at least one federal prize now makes disclosure a condition. Where the rules
are silent or ambiguous about coding assistants, ask the organisers.

## Files

- `ai-rules-census.json`: one record per platform or contest with the quotes by topic, how the
  page was read (direct fetch, saved copy, PDF text extracted by code, or search snippet only),
  the platforms not covered and why, the prior art checked, and a change log. The EvalAI record
  carries the 2026-10-18 live check under `live_challenges_2026_10_18`; the Zindi record carries
  the 2026-10-21 competition check under `zindi_competitions_2026_10_21`; the GEMS record carries
  its AI clause under `ai_clause`.
- `ai-rules-census.md`: the same as readable tables.

## What changed in 0.3.1

- **Added the U.S. DOE GEMS Prize** (Geologic Enhanced Mapping System, $300,000, hosted on
  DrivenData, closes 2026-12-03). Its rules are a 19-page PDF linked from the DrivenData rules
  tab; the PDF was downloaded and its text extracted by code on 2026-10-21. It permits generative
  AI for every submission element and requires entrants to disclose how much they used and how:
  the first disclosure duty in this census. The place for that disclosure ("the narrative") is
  not defined anywhere else in the rules, and the competition's DrivenData pages ask for no
  narrative or write-up.
- **"First" corrected.** 0.3.0 called the Zindi Bias Bounty clause "the first explicit
  permission". GEMS's rules are dated September 2026, before the Bias Bounty update of
  2026-10-06, so the Zindi clause was only the first one *this census found*. The headline now
  lists both.
- **DrivenData's natural-persons rule is a template default, not a platform rule.** GEMS on
  DrivenData admits "Private entities" that are "incorporated in and maintain a primary place of
  business in the United States", against the standard template's "Legal entities and
  organizations are not eligible for entry."
- **A deadline mismatch.** The GEMS site gives "Dec. 3, 2026, 11:59 p.m. UTC"; the rules require
  entries "by 5:00 p.m. ET on the prize submission deadline date", about two hours earlier.

## What changed in 0.3.0

- **Zindi competition-level check (2026-10-21).** All 7 open Zindi competitions and 2 recently
  closed ones were read through Zindi's public API. One (Bias Bounty) permits commercial LLM coding
  tools for drafting, debugging, testing and documentation, as long as the solution does not need
  them to run; it does not ask for AI use to be disclosed. The other 8 have no AI-tool clause.
  Zindi's platform rules page, re-fetched the same day, still has none.
- **Added ARC Prize 2026** (overview page): no internet during Kaggle evaluation, so no GPT/Claude
  API can run inside a solution; prize code must be open source under CC0 or MIT-0.
- **Headline narrowed.** "No clause on AI-assisted code" now holds for platform-wide terms only.

## What changed in 0.2.1

All 18 challenges in EvalAI's public list of running challenges were checked on 2026-10-18
(the upcoming list was empty):

- **No placeholder terms.** None contains the starter template's Lorem ipsum text in any
  field. The question left open in 0.2.0 is answered: live hosts replace it.
- **An explicit AI-tool clause, at challenge level.** The eBay 2026 University Machine
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
could not be read, so it may overlap; that is the main limit of this claim. Searches on
2026-10-21 found no page quoting the Zindi Bias Bounty clause or the GEMS clause. The GEMS
wording follows the U.S. National Science Foundation's notice of 2023-12-14 to grant proposers
("Proposers are encouraged to indicate in the project description the extent to which, if any,
generative AI technology was" ...), which encourages disclosure; GEMS makes it a "must".

## Limits

- One date for the platform terms, one more for EvalAI's live list, a third for Zindi's
  competitions, ARC Prize and GEMS. Per-competition rules can override every platform-wide term
  quoted here.
- Kaggle's rules pages are JS-rendered; its quotes come from search-result snippets.
- The EvalAI and CrunchDAO records rest on documentation pages, not binding terms; the ARC Prize
  record rests on its overview page, not each track's rules.
- The EvalAI live check covers only public, approved, running challenges. The Zindi check covers
  9 of 515 listed competitions (all 7 open ones); three long pages were read only to 100,000
  characters, where the unread rest held repeated parent-competition rules. Long pages were read
  by a text-extraction model, not parsed by code.
- The GEMS record covers one federal prize. Its AI clause reads like shared DOE American-Made
  template text, but other American-Made prizes were not read, so how far it reaches is unknown.
- Quotes are fragments of at most 125 characters each; the URL carries the full text.
- "Not addressed" never means "allowed".

## How to update

Fetch each URL in `ai-rules-census.json`, search it for the same topics, replace the quotes,
bump the check date and the version, and add a line to `changes`. Add a platform by adding a
record with the same keys. For Zindi, list open competitions from
`https://api.zindi.world/v1/competitions` and read each one at
`https://api.zindi.world/v1/competitions/<slug>`. For rules published only as PDF, extract the
text with code (WebFetch returns the compressed bytes) and read the pages with the hits.
