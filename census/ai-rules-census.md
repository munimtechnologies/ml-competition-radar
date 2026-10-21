# AI-assistance rules across ML competition platforms (version 0.3.1, platform terms checked 2026-10-17; EvalAI live check 2026-10-18; Zindi competitions, ARC Prize 2026 and DOE GEMS Prize checked 2026-10-21)

CC BY 4.0. MV2 of Munim, Inc., with AI agents working in his name. Quotes are verbatim
fragments of at most 125 characters; the URL carries the full text. "none" means the page has
no such clause, not that the thing is allowed.

| Platform / contest | Read how | AI-assisted code clause | AutoML | Commercial LLM API inside solution | Entity entrants | Age / sanctions | Winner code terms | Reproducibility |
|---|---|---|---|---|---|---|---|---|
| [Zindi](https://zindi.world/rules) | page fetched (re-fetched 2026-10-21) + JSON of all 7 open competitions, 2026-10-21 | none platform-wide; **1 of 7 open competitions permits it** (Bias Bounty, item 9) | "Automated machine learning tools such as AutoML are not permitted." | forbidden indirectly: "no paid services or free trials that require a credit card"; "publicly-available, open-source packages only" | not addressed; individuals or teams of up to four; prizes to individuals or team leader | none stated | top 3 assign copyright to Zindi unless rules say otherwise; ID, residence, bank letter | code from top 10 within 48 h; "If your code does not run you will be dropped from the top 20."; "Always set the seed." |
| [AIcrowd](https://www.aicrowd.com/participation_terms) | page fetched | none | none | not addressed; "(i) the Challenge Rules; (ii) these Participation Terms; (iii) the ToU" | not restricted: "Any User having opened an Account as Participant will have the right to participate" | none stated | entrant picks licence; default "the MIT open source license" | per challenge |
| [DrivenData](https://www.drivendata.org/competitions/297/whats-up-docs/rules/) (standard template) | page fetched | none | none | not addressed | **no** (template default; GEMS overrides it): "Legal entities and organizations are not eligible for entry." | 18+ and age of majority; not under U.S. sanctions; Russian Federation residents cannot win | "Winning solutions need to be made available under the MIT License" | documentation template; "Privately sharing code or data outside of teams is not permitted." |
| [Kaggle](https://www.kaggle.com/competitions/abstraction-and-reasoning-challenge/rules) (Foundational Rules) | search snippets only (JS page) | none | per competition: "permits the use of automated machine learning tool(s) ("AMLT")" | not addressed; external tools must be "reasonably accessible to all" | **no** in practice: "Each Team member must be a single individual with a separate Kaggle account." | Crimea, DNR, LNR, Cuba, Iran, Syria, North Korea, U.S. sanctions excluded | per competition | per competition; code competitions run in Notebooks |
| [Codabench](https://github.com/codalab/codabench/blob/master/documentation/PRIVACY.md) | page fetched | none | none | not addressed; organiser terms govern | not addressed | none; French law | organiser property "unless otherwise stated in the competition's terms of use" | per competition |
| [EvalAI](https://evalai.readthedocs.io/en/latest/configuration.html) (host docs; no platform-wide terms) | page fetched + starter template + live challenge list (18 challenges, 2026-10-18) | none | none | set by each host | per challenge; hosts may filter by e-mail domain: "Leave blank if everyone is allowed to participate." | none at platform level | per challenge | host's "Python script which will decide how to evaluate submissions" |
| [NeurIPS 2026 EEG/EMG Foundation Challenge](https://neural-interfaces26.github.io/rules.html) | page fetched | none | none | not addressed | **yes**: "Industry, academia, students, and independents are all eligible" | none stated | "Participants retain the intellectual property rights"; open release "entirely the participant's choice" | "The top three per track must replay within ±2σ."; training re-run from committed config |
| [Wunder Fund Alfa Connectome](https://wundernn.io/docs/rules) | saved copy (2026-10-16) re-read | none | none | not addressed; sandbox has no network | not addressed | not addressed | code + 2-8 page report + code-review call | no public or private sharing before the end |
| [ThinkOnward](https://thinkonward.com/app/c/challenges/patch-the-planet/rules) | page fetched | none | none | not addressed; no GPL/LGPL code | **yes**: "you" may mean "Your Organization on whose behalf you are acting" | 18+ or majority; restricted jurisdictions listed | non-exclusive, perpetual, royalty-free licence "for any purpose whatsoever" | documents + one interview |
| [bitgrit (AI Immune System Challenge)](https://bitgrit.com/competition/27) | page fetched | none | none | **forbidden**: "commercial or proprietary APIs (e.g., OpenAI GPT series, Claude, Gemini API) is strictly prohibited" | individuals only; no teams | none stated | README to reproduce end to end; exact model weights or version link | "fix all random seeds and set the inference temperature to 0" |
| [CrunchDAO](https://docs.crunchdao.com/) (docs landing page only) | page fetched | none | none | not addressed on this page | not addressed as such: "Everyone. Crunch is open and permissionless." | not addressed on this page | "rewarded in USDC"; licence in per-competition rules (not read) | not addressed on this page |
| [ARC Prize 2026](https://arcprize.org/competitions/2026/) (overview page; submitted on Kaggle) | page fetched 2026-10-21 | none | none | **not possible**: "Internet access is not available during Kaggle evaluation (no API-based systems like GPT/Claude/etc.)" | not addressed on this page; Kaggle admits individual accounts only | not addressed on this page | "all code and methods authored by the submitter must be made open source" (CC0 or MIT-0) | "All prizes require reproducible, open-source submissions" |
| [U.S. DOE GEMS Prize](https://docs.nlr.gov/docs/fy26osti/96647.pdf) (official rules, September 2026; hosted on [DrivenData](https://www.drivendata.org/competitions/306/competition-doe-gems/)) | PDF text extracted by code, 2026-10-21 (19 pages) | **permits it, disclosure required** (item 11): "Using generative AI technology in the development of your prize submission is allowed." | none | not addressed | **yes, U.S.-based**: "Private entities must be incorporated in and maintain a primary place of business in the United States." | individuals: U.S. citizen or permanent resident, 18+; FFRDCs, federal employees, debarred parties, foreign-talent-program members excluded | complete code assets and documentation; public parts under "an unlimited license to display publicly and to use"; no open-source licence required | "should be able to sufficiently reproduce the winning results and generate predictions on new data samples" |

Not covered (with the reason, all 2026-10-17): Solafune (terms page HTTP 404), Numerai (terms
page JS-only; rules page HTTP 404), Signate (terms URL redirects to a JS-only page), Topcoder
(terms page JS-only), HeroX (terms page HTTP 404), Tianchi (search snippets only).

## Zindi competition-level check (new in 0.3.0, 2026-10-21)

Zindi's public API listed 515 competitions, 7 of them open. The JSON of all 7 open ones and 2
recently closed ones was searched for LLM coding tools, development assistants, AI tools,
generative AI, ChatGPT, AutoML, paid APIs, proprietary model services and disclosure of AI use.

| Competition (slug) | Open | Reward | Rules updated | LLM coding-assistant clause |
|---|---|---|---|---|
| bias-bounty-mapping-equity-challenge | yes | $10 000 USD | 2026-10-06 | **yes (permits)** |
| french-embassy-underwater-vessel-noise-challenge | yes | $5 000 USD | 2026-10-20 | no |
| google-mumbai-data-challenge | yes | $6 000 USD | 2026-10-14 | no |
| eswatini-indabax-hack | yes | 50 000 SZL | 2026-09-28 | no |
| climate-risk-health-prediction-challenge-miva | yes | 500 Points | 2026-08-26 | no (read to 100,000 chars) |
| ghana-indigenous-intel-challenge-cameroon-community-hack | yes | 5 0000 fcfa | 2026-10-09 | no (read to 100,000 chars) |
| google-waxal-asr-challenge-october-study-jam | yes | 500 Points | 2026-09-30 | no (read to 100,000 chars) |
| telco-troubleshooting-agentic-challenge | closed | €40 000 EUR | 2026-04-01 | no; base model fixed: "The entire competition uses Qwen3.5-35B-A3B as the base model." |
| road-barbados-historic-handwriting-challenge | closed | $25 000 USD | 2026-06-26 | no |

The other 8 all carry Zindi's standard text: "You may only use open-source languages and tools in
building models for this challenge." and "The solution must use publicly-available, open-source
packages only."

## Reading

1. (Narrowed in 0.3.0) No platform-wide terms address AI-written code. The nearest clauses are
   Zindi's AutoML ban and Kaggle's per-competition AMLT permission, both written for AutoML
   products. Clauses about AI tools exist only in individual competitions (items 8, 9 and 11).
2. (Updated in 0.3.1) The two largest platforms (Kaggle, DrivenData) admit only natural persons
   by default. A company that builds entries with AI agents needs a named person as entrant there,
   while ThinkOnward and the NeurIPS EEG/EMG challenge accept the company itself. On DrivenData
   the rule is the standard template's, not the platform's: the DOE GEMS Prize, also on DrivenData,
   admits U.S.-incorporated companies (item 12).
3. Where a commercial LLM is banned, the ban is on running it inside the solution (Zindi via
   "no paid services", bitgrit explicitly, ARC Prize 2026 by having no internet during
   evaluation), for reproducibility and fairness. Only two rules (items 9 and 11) speak to how the
   code was written, and both allow AI help.
4. Every platform with prizes re-runs or inspects winning code. An AI-made pipeline is held to
   the same bar: scripted, seeded, documented.
5. (Updated in 0.2.1) EvalAI has no platform-wide participation terms at all: each host writes
   its own terms HTML, and on 2026-10-17 the terms file in the official EvalAI-Starters template
   was Lorem ipsum placeholder text. On 2026-10-18 all 18 challenges in EvalAI's public list of
   running challenges (`/api/challenges/challenge/present/approved/public`; the upcoming list was
   empty) were searched for "Lorem", "ipsum", "consectetur" and "dolor sit" in every field: no
   hits. Every live host had replaced the placeholder. None of the 18 terms fields mentions AI
   tools; one challenge's description does (item 8).
6. (New in 0.2.0) Platform terms are increasingly unreadable without a browser: Numerai,
   Signate, Topcoder and Kaggle all render their terms with JavaScript, and Solafune and HeroX
   returned 404 at their terms URLs. A census like this one can only quote what a plain fetch
   returns, so those four plus two stay listed as not covered rather than guessed.
7. (New in 0.2.1) On EvalAI, a challenge's machine-readable prize flag can disagree with its own
   text. All 18 running challenges had `"has_prize": false` on 2026-10-18. One of them, the CVPR
   2026 Roboflow-20VL Few-Shot Object Detection Challenge (id 2672), says in its description
   "Overall Track Winner: $500" and "Many thanks to Roboflow for sponsoring prizes!", while
   its terms say "There are no prizes." Its description also gives "The submission period for this
   challenge will end on May 31st, 2026 at 11:59 PM EST.", but its API `end_date` is
   2099-06-01. A tool that lists prize competitions from platform metadata alone would get
   both the prize and the deadline wrong here, so read the challenge text.
8. (New in 0.2.1) The first AI-tool clause this census found sits in one challenge, not on a
   platform: the eBay 2026 University Machine Learning Competition - Canada on EvalAI
   (id 2680; students at Canadian universities only) has a "Use of AI" section and the FAQ
   question "Can I use AI tools?". Its answer restricts the data and the output licence, not the
   authorship: "eBay data MUST NOT be inputted into third party hosted platforms (including
   Generative AI tools, such as ChatGPT, Claude" (the sentence goes on), and "if AI tools are used,
   the resulting code, data, or other generated content MUST NOT limit commercial use" (it goes
   on).
9. (New in 0.3.0; reworded in 0.3.1) The first explicit **permission** for AI-assisted code that
   this census found is in one Zindi competition, the Bias Bounty Mapping Equity Challenge
   ($10,000; rules updated 2026-10-06), under "Datasets, packages and general principles":
   "General-purpose development assistants such as commercial LLM coding tools may be used for
   code drafting, debugging, testing" (the sentence goes on to add documentation), "provided they
   are not required to execute or reproduce the submitted solution." It continues: "Participants
   remain responsible for reviewing and validating all submitted work." The same section keeps the
   ban on commercial services inside the solution, which "must use publicly available, open-source
   packages and must not depend on paid APIs, proprietary model services" (it goes on). It does not
   ask for AI use to be disclosed. So the line this census drew in item 3 (what runs inside a
   solution versus how it was written) is now written into a rule. It was found first, not written
   first: the GEMS rules of item 11 are dated September 2026.
10. (New in 0.3.0) The other 6 open Zindi competitions, and 2 recent closed ones, carry no such
   clause. Their standard sentence "You may only use open-source languages and tools in building
   models for this challenge." does not separate a coding assistant from a modelling tool. Read
   literally it could reach a commercial coding assistant used while building a model; read as
   Zindi's other rules suggest, it is about what the solution runs on. The census does not know
   which reading Zindi applies. Only the Bias Bounty text settles it, so an entrant in any other
   Zindi competition who uses a commercial coding assistant should ask the organisers first.
11. (New in 0.3.1) The U.S. Department of Energy's GEMS Prize (Geologic Enhanced Mapping System;
   $300,000; on DrivenData; official rules "SEPTEMBER 2026", section 3.2) has the only **disclosure
   duty** found so far. "Using generative AI technology in the development of your prize submission
   is allowed." But "you must indicate in the narrative (not included in the word count)" "the
   extent to which, if any, you used generative AI technology and how you used it to develop your
   submission", "including all submission elements described in this official rules document",
   which takes in the code finalists hand over. "You are responsible for the accuracy,
   authenticity, and authorship representations of your submission", and "Relying on generative
   AI may introduce significant risks" (it names research misconduct). Two gaps: the word
   "narrative" appears nowhere else in the 19 pages (section 3.5 "What To Submit" asks for
   predictions, code and documentation), and the competition's DrivenData pages ask for no
   narrative or write-up, so where to put the disclosure is not defined. The wording follows the
   National Science Foundation's 2023 notice to grant proposers, which only "encouraged" it.
12. (New in 0.3.1) GEMS also shows that a contest's own rules can reverse a platform's default
   and that its dates need reading twice. Its rules admit "Institutions, companies, nonprofit
   organizations, and individuals based in the United States (U.S.) are eligible to compete"
   (DrivenData's standard template: "Legal entities and organizations are not eligible for
   entry."). Its site gives "Dec. 3, 2026, 11:59 p.m. UTC" as the deadline, while the rules
   require entries "by 5:00 p.m. ET on the prize submission deadline date", about two hours
   earlier. Its prize goals, apparently shared DOE American-Made text, ask that a submission
   confirm the "intent to commercialize early-stage technology and establish a viable U.S.-based
   business in the near future", which is an unusual bar for a leaderboard competition.

## Prior art checked (2026-10-17; searches repeated 2026-10-21)

mlcontests.com reports 2023 and 2024 (how winners used LLMs; no rules census);
mlcontests.com/platforms (feature matrix, no AI-policy column); Nasios, arXiv:2604.08001
(ecosystem survey, no AI-tool rules); "Ethical guidelines for machine learning competitions",
AI and Ethics 2026 (compares Kaggle, AIcrowd, DrivenData rules; paywalled, not read, may overlap).
On 2026-10-21 no page quoting the Zindi Bias Bounty clause or the GEMS clause was found; a Kaggle
forum thread on AI-generated code shows users disagreeing with no official rule cited. The GEMS
clause echoes the NSF notice of 2023-12-14: "Proposers are encouraged to indicate in the project
description the extent to which, if any, generative AI technology was" (it goes on).
