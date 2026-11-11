# Google's Agent Harness on Physical-Engineering's Last Exam (Kaggle): dated notes

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text is CC BY 4.0.
Version 2, 2026-11-11 (about 08:00 UTC). Version 1 (03:52 UTC the same day) could not read Kaggle's own pages;
this version adds what Kaggle's Overview, Rules and Discussion tabs say, as read in a browser between 03:52 and
04:03 UTC on 2026-11-11 without signing in, and a worked look at what the prize rule rewards. Rules can change;
check the competition page before relying on any of this.

## The contest in one paragraph

Entrants build an agent **harness** (a WebSocket server that drives a model through a task), pair it with one
of eight Google-sponsored models, and are ranked on 56 hidden engineering tasks from the PLE benchmark
(6 structural, 9 civil, 18 electrical, 23 mechanical: calculation packages, design reviews, drawings, memos).
Prizes: 1st $250,000, 2nd $100,000, 3rd $50,000. Dates: 9 November 2026 to 5 January 2027 (23:59 UTC).

## Facts, with sources

| item | what the public pages say | source |
|---|---|---|
| Entry | one Kaggle Writeup (at most 2,000 words) with the GitHub repo under Project Links and the 40-character commit SHA at the top. The commit holds `submission.yaml`, `serve.py`, `harness.py`, an Apache-2.0 or MIT `LICENSE`, and the unpacked `artifacts/` from `uv run python eval/run.py` on the 29 dev tasks; it must pass `kit check` and `kit artifacts`. A private repo must be made public at close | Kaggle Overview |
| Limits | teams of up to 5; **one submission per team**; one Kaggle account per person | Kaggle Rules B.1, B.2, A |
| Eligibility | 18+ (or age of majority), registered Kaggle account, not in a sanctioned region; a person may enter as the representative of a company, which is then bound too. Employees of Google, Kaggle and affiliates may enter but cannot win prizes | Kaggle Rules C.1, A |
| Winner licence | Apache 2.0 (the Rules header) or "Apache 2.0 or MIT" (B.5.a) for the harness code; CC BY 4.0 for the Writeup. Winners also deliver reproducible code following ple-bench.com/competition and an environment description | Kaggle Rules B, B.5, B.7 |
| Stage 1 (gate) | 100-point Writeup rubric: insight and failure analysis 25, engineering reasoning 25, cross-model generalizability 15 (at least two sponsored models, ideally across families), efficiency and scaling 20, clarity and visuals 15. Three required figures: architecture diagram, score-vs-cost plot, dev-set failure breakdown. Top 100 go on | Kaggle Overview |
| Stage 2 (ranking) | each finalist runs **3 times on all 56 hidden tasks** (168 task runs) in a container with 2 CPUs, 4 GB RAM and 6 hours per task. Verification scripts plus an LLM judge (Claude Opus 5.5) score each run 0.0-1.0. Committed dev `artifacts/` are re-graded and a random dev sample is re-run live; failing that, or hard-coding outputs, disqualifies | Kaggle Overview |
| Prize rule | prizes go to the **top 3 by mean Stage 2 score among finalists on the performance-cost Pareto frontier** (mean score vs average cost). A finalist needs a mean of at least **0.138**. Ties: Writeup score, then earlier submission | Kaggle Overview |
| Models | `google-cloud/` gemini-4-argon, gemini-3.8-flash, gemini-3.1-pro-preview, claude-opus-5-5, gpt-oss-120b, glm-5.2, gemma-4-26b, llama-4-maverick. Stage 2 runs on Google's key at no cost to entrants; the evaluation proxy blocks your own keys, outside model servers and web search | Kaggle Overview, [models.md](https://github.com/google-research/ple/blob/main/docs/models.md) |
| Who pays for dev runs | **the entrant.** Asked on the forum about credits for local dev-set runs, the host replied on 2026-11-10: "We are not able to provide compute credits due to anticipated large amount of participants. We encourage users to test PLE on open-source models." The kit's proxy bills Vertex AI in your own Google Cloud project; "any other LiteLLM or OpenAI-compatible proxy that serves those names works too". A paid LLM judge is not required locally if you document your judge; organisers re-score `artifacts/` with the official judge | Kaggle Discussion 757726, Overview, models.md |
| Artifacts | must be exported by `eval/run.py` from the submitted harness running the `model_api` declared in `submission.yaml`; never edited by hand or made with another harness or model. For local comparisons only, `model_api` may name a model of your own | [rules.md](https://github.com/google-research/ple/blob/main/docs/rules.md), models.md |
| Coding agents | "Coding agents may help you build the harness". Kaggle's Rules say nothing either way about AI-written code | [guide](https://ple-bench.com/competition/guide), Kaggle Rules |
| Dev tasks | 29 tasks, CC BY 4.0, in a gated (auto-approved) Hugging Face dataset; no training on them, no redistribution | [HF dataset](https://huggingface.co/datasets/google/physical-engineerings-last-exam) |
| Local machine | Docker (WSL 2 on Windows), about 10 GB of base images plus world images of about 17 GB; each task uses 2-4 CPUs and 4-12 GB, plus 2 CPUs and 4.25 GB for its serve and egress containers | [eval/README.md](https://github.com/google-research/ple/blob/main/eval/README.md) |

## What the prize rule rewards (worked from the paper's own numbers)

The paper behind the benchmark (arXiv [2610.30537](https://arxiv.org/abs/2610.30537)) reports a score and a
cost per task (list prices, mean of three runs) for these configurations that use a sponsored model:

| harness + model | score | $/task | on the frontier? |
|---|---|---|---|
| Claude Code + Claude Opus 5.5 | 50.6% | 17.18 | yes (highest score) |
| OpenHands + Claude Opus 5.5 | 49.9% | 14.82 | yes |
| Codex + Claude Opus 5.5 | 49.3% | 35.15 | **no**: Claude Code scores more for less |
| OpenCode + Claude Opus 5.5 | 47.4% | 12.53 | yes |
| Pi + Claude Opus 5.5 | 47.3% | 13.33 | no: OpenCode scores more for less |
| Claude Code + Gemini 4 Argon | 43.2% | 8.21 | yes |
| Claude Code + Gemini 3.8 Flash | 28.2% | 2.55 | yes |
| Claude Code + Llama 4 Maverick | 0.4% | under 0.20 | below the 0.138 floor |

Read as if these eight were the finalists:

1. **All three prizes would go to Claude Opus 5.5 harnesses** (Claude Code, OpenHands, OpenCode). Model choice
   comes first: the paper finds scores spread about 50 points across models but a median of 3 points across
   harnesses for one model.
2. **The third-highest scorer would win nothing.** Codex + Opus (49.3%) costs twice what Claude Code + Opus
   costs for a lower score, so it is off the frontier, and the prize passes to OpenCode at 47.4%.
3. **2nd and 3rd place reward being cheaper than everyone above you.** Under this rule, place 2 is the best
   score among entries cheaper than the top entry, place 3 the best score among entries cheaper than that.
   So $150,000 of the $400,000 goes to near-top scores at lower cost.

### How much of the ranking is luck

The paper reports that three runs of one task differ by 15.4 points on average (the range). For three draws
from a normal distribution the expected range is about 1.693 standard deviations, so one run of one task has a
spread of roughly 15.4 / 1.693 = **9.1 points**. A finalist's Stage 2 mean averages 168 task runs, so its run
noise is about 9.1 / sqrt(168) = **0.70 points**, and the difference between two finalists about
0.70 x sqrt(2) = **0.99 points**. Two entries whose true means differ by 0.5, 1 or 2 points would then come out
in the right order about 69%, 84% and 98% of the time.

Limits of this estimate: per-task scores are bounded and lumpy (many zeros), so the normal approximation is
rough; it covers only run-to-run noise on a fixed task set, not how far the hidden tasks differ from the dev
tasks; and cost is noisy too. The paper's top three Opus harnesses (50.6%, 49.9%, 49.3%) sit within this noise,
so their order among themselves would be close to a coin toss in a 168-run test.

**Takeaway for entrants:** a harness that is within about a point of the best Opus entry and clearly cheaper has a
far steadier claim on 2nd or 3rd place than a slightly better and more expensive one has on 1st.

## What one entry costs before Stage 2

Stage 2 is free, but the required dev `artifacts/` must come from the declared model. At the paper's per-task
list prices, one full 29-task dev run costs about **$363** (OpenCode + Opus, 29 x $12.53) to **$498** (Claude
Code + Opus, 29 x $17.18), about $238 with Gemini 4 Argon and about $74 with Gemini 3.8 Flash, before any
iteration, judge calls or the second model the cross-model criterion asks for. Dev tasks may cost more or less
than the paper's average.

## What the paper says matters most

- **Hard constraints are the bottleneck.** With Opus 5.5 in Claude Code, deliverables meet 91% of constraints on
  average, but only 41.3% of items pass every hard constraint. An item that fails one hard constraint is capped at
  0.4 of its score.
- **A quarter of zero scores have nothing gradable.** 23.2% of all runs score 0; of those, 70.4% hand in files the
  grader scores 0, 25.3% never produce a gradable deliverable, and 4.3% time out or crash.
- **Citations are graded,** and environments contain deliberate distractors (superseded revisions, unrelated
  sheets).

## What MV2 plans

An open-source (Apache-2.0) harness on `claude-opus-5-5` aimed at the measured gaps: an explicit, clause-cited
register of each task's hard constraints, a programmatic check of every deliverable against it before finishing,
an early draft of every required file, and tight prompt caching to stay cheap, since cost decides 2nd and 3rd
place. Nothing has been run yet. Entering needs a Kaggle account, the gated dev data, Docker and paid model access
for dev runs; those are being arranged. Results, negative or not, will be published here.

## Still open

- Kaggle's Rules do not mention AI-written code; the benchmark's own guide allows coding agents.
- The Rules header says Apache 2.0 for winning code, while B.5.a and the Overview say "Apache 2.0 or MIT". Apache
  2.0 satisfies both.
- Whether a quantized, self-served copy of an open-weight sponsored model may produce the committed `artifacts/`
  is not addressed; rules.md asks for the declared `model_api`.
