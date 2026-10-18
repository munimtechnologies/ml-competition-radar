# AI-assistance rules across ML competition platforms (version 0.2.1, checked 2026-10-17; EvalAI live check 2026-10-18)

CC BY 4.0. MV2 of Munim, Inc., with AI agents working in his name. Quotes are verbatim
fragments of at most 125 characters; the URL carries the full text. "none" means the page has
no such clause, not that the thing is allowed.

| Platform / contest | Read how | AI-assisted code clause | AutoML | Commercial LLM API inside solution | Entity entrants | Age / sanctions | Winner code terms | Reproducibility |
|---|---|---|---|---|---|---|---|---|
| [Zindi](https://zindi.world/rules) | page fetched | none | "Automated machine learning tools such as AutoML are not permitted." | forbidden indirectly: "no paid services or free trials that require a credit card"; "publicly-available, open-source packages only" | not addressed; individuals or teams of up to four; prizes to individuals or team leader | none stated | top 3 assign copyright to Zindi unless rules say otherwise; ID, residence, bank letter | code from top 10 within 48 h; "If your code does not run you will be dropped from the top 20."; "Always set the seed." |
| [AIcrowd](https://www.aicrowd.com/participation_terms) | page fetched | none | none | not addressed; "(i) the Challenge Rules; (ii) these Participation Terms; (iii) the ToU" | not restricted: "Any User having opened an Account as Participant will have the right to participate" | none stated | entrant picks licence; default "the MIT open source license" | per challenge |
| [DrivenData](https://www.drivendata.org/competitions/297/whats-up-docs/rules/) (standard template) | page fetched | none | none | not addressed | **no**: "Legal entities and organizations are not eligible for entry." | 18+ and age of majority; not under U.S. sanctions; Russian Federation residents cannot win | "Winning solutions need to be made available under the MIT License" | documentation template; "Privately sharing code or data outside of teams is not permitted." |
| [Kaggle](https://www.kaggle.com/competitions/abstraction-and-reasoning-challenge/rules) (Foundational Rules) | search snippets only (JS page) | none | per competition: "permits the use of automated machine learning tool(s) ("AMLT")" | not addressed; external tools must be "reasonably accessible to all" | **no** in practice: "Each Team member must be a single individual with a separate Kaggle account." | Crimea, DNR, LNR, Cuba, Iran, Syria, North Korea, U.S. sanctions excluded | per competition | per competition; code competitions run in Notebooks |
| [Codabench](https://github.com/codalab/codabench/blob/master/documentation/PRIVACY.md) | page fetched | none | none | not addressed; organiser terms govern | not addressed | none; French law | organiser property "unless otherwise stated in the competition's terms of use" | per competition |
| [EvalAI](https://evalai.readthedocs.io/en/latest/configuration.html) (host docs; no platform-wide terms) | page fetched + starter template + live challenge list (18 challenges, 2026-10-18) | none | none | set by each host | per challenge; hosts may filter by e-mail domain: "Leave blank if everyone is allowed to participate." | none at platform level | per challenge | host's "Python script which will decide how to evaluate submissions" |
| [NeurIPS 2026 EEG/EMG Foundation Challenge](https://neural-interfaces26.github.io/rules.html) | page fetched | none | none | not addressed | **yes**: "Industry, academia, students, and independents are all eligible" | none stated | "Participants retain the intellectual property rights"; open release "entirely the participant's choice" | "The top three per track must replay within ±2σ."; training re-run from committed config |
| [Wunder Fund Alfa Connectome](https://wundernn.io/docs/rules) | saved copy (2026-10-16) re-read | none | none | not addressed; sandbox has no network | not addressed | not addressed | code + 2-8 page report + code-review call | no public or private sharing before the end |
| [ThinkOnward](https://thinkonward.com/app/c/challenges/patch-the-planet/rules) | page fetched | none | none | not addressed; no GPL/LGPL code | **yes**: "you" may mean "Your Organization on whose behalf you are acting" | 18+ or majority; restricted jurisdictions listed | non-exclusive, perpetual, royalty-free licence "for any purpose whatsoever" | documents + one interview |
| [bitgrit (AI Immune System Challenge)](https://bitgrit.com/competition/27) | page fetched | none | none | **forbidden**: "commercial or proprietary APIs (e.g., OpenAI GPT series, Claude, Gemini API) is strictly prohibited" | individuals only; no teams | none stated | README to reproduce end to end; exact model weights or version link | "fix all random seeds and set the inference temperature to 0" |
| [CrunchDAO](https://docs.crunchdao.com/) (docs landing page only) | page fetched | none | none | not addressed on this page | not addressed as such: "Everyone. Crunch is open and permissionless." | not addressed on this page | "rewarded in USDC"; licence in per-competition rules (not read) | not addressed on this page |

Not covered (with the reason, all 2026-10-17): Solafune (terms page HTTP 404), Numerai (terms
page JS-only; rules page HTTP 404), Signate (terms URL redirects to a JS-only page), Topcoder
(terms page JS-only), HeroX (terms page HTTP 404), Tianchi (search snippets only).

## Reading

1. No platform addresses AI-written code. The nearest clauses are Zindi's AutoML ban and
   Kaggle's per-competition AMLT permission, both written for AutoML products.
2. The two largest platforms (Kaggle, DrivenData) admit only natural persons. A company that
   builds entries with AI agents needs a named person as entrant there, while ThinkOnward and the
   NeurIPS EEG/EMG challenge accept the company itself.
3. Where a commercial LLM is banned, the ban is on running it inside the solution (Zindi via
   "no paid services", bitgrit explicitly), for reproducibility and fairness. None of the pages
   restricts how the code was written.
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
8. (New in 0.2.1) The first explicit AI-tool clause this census has found sits in one challenge,
   not on a platform: the eBay 2026 University Machine Learning Competition - Canada on EvalAI
   (id 2680; students at Canadian universities only) has a "Use of AI" section and the FAQ
   question "Can I use AI tools?". Its answer restricts the data and the output licence, not the
   authorship: "eBay data MUST NOT be inputted into third party hosted platforms (including
   Generative AI tools, such as ChatGPT, Claude" (the sentence goes on), and "if AI tools are used,
   the resulting code, data, or other generated content MUST NOT limit commercial use" (it goes
   on). So item 1 still holds for platform-wide terms. Challenge-level rules can carry AI clauses,
   and this one is about data leakage and licensing, not about who wrote the code.

## Prior art checked (2026-10-17)

mlcontests.com reports 2023 and 2024 (how winners used LLMs; no rules census);
mlcontests.com/platforms (feature matrix, no AI-policy column); Nasios, arXiv:2604.08001
(ecosystem survey, no AI-tool rules); "Ethical guidelines for machine learning competitions",
AI and Ethics 2026 (compares Kaggle, AIcrowd, DrivenData rules; paywalled, not read, may overlap).
