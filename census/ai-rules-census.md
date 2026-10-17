# AI-assistance rules across ML competition platforms (checked 2026-10-17)

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
| [NeurIPS 2026 EEG/EMG Foundation Challenge](https://neural-interfaces26.github.io/rules.html) | page fetched | none | none | not addressed | **yes**: "Industry, academia, students, and independents are all eligible" | none stated | "Participants retain the intellectual property rights"; open release "entirely the participant's choice" | "The top three per track must replay within ±2σ."; training re-run from committed config |
| [Wunder Fund Alfa Connectome](https://wundernn.io/docs/rules) | saved copy (2026-10-16) re-read | none | none | not addressed; sandbox has no network | not addressed | not addressed | code + 2-8 page report + code-review call | no public or private sharing before the end |
| [ThinkOnward](https://thinkonward.com/app/c/challenges/patch-the-planet/rules) | page fetched | none | none | not addressed; no GPL/LGPL code | **yes**: "you" may mean "Your Organization on whose behalf you are acting" | 18+ or majority; restricted jurisdictions listed | non-exclusive, perpetual, royalty-free licence "for any purpose whatsoever" | documents + one interview |
| [bitgrit (AI Immune System Challenge)](https://bitgrit.com/competition/27) | page fetched | none | none | **forbidden**: "commercial or proprietary APIs (e.g., OpenAI GPT series, Claude, Gemini API) is strictly prohibited" | individuals only; no teams | none stated | README to reproduce end to end; exact model weights or version link | "fix all random seeds and set the inference temperature to 0" |

Not covered this time: Solafune (terms page 404), Numerai (rules page 404; ToS not read),
CrunchDAO (rules behind sign-up; earlier reading: KYC, one account per natural person), Signate
(not found), Tianchi (snippet only: one 2025 challenge forbids "commercial LLM API calls"),
EvalAI (not searched).

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

## Prior art checked (2026-10-17)

mlcontests.com reports 2023 and 2024 (how winners used LLMs; no rules census);
mlcontests.com/platforms (feature matrix, no AI-policy column); Nasios, arXiv:2604.08001
(ecosystem survey, no AI-tool rules); "Ethical guidelines for machine learning competitions",
AI and Ethics 2026 (compares Kaggle, AIcrowd, DrivenData rules; paywalled, not read, may overlap).
