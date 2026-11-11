# Google's Agent Harness on Physical-Engineering's Last Exam (Kaggle): dated notes

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name. Text is CC BY 4.0. Everything
here comes from public pages read on 2026-11-11 between 03:45 and 04:30 UTC. Kaggle's own Overview and Rules
tabs did not render for our reader, so eligibility, team size and the winner licence are **not yet confirmed**
here. The rules may change.

## The contest in one paragraph

Entrants build an agent **harness** (a WebSocket server that drives a model through a task), pair it with one
of eight Google-sponsored models, and are ranked on 56 hidden engineering tasks from the PLE benchmark
(structural, civil, electrical and mechanical work: calculation packages, design reviews, drawings, memos).
Prizes: 1st $250,000, 2nd $100,000, 3rd $50,000. Dates: 9 November 2026 to 5 January 2027.

## Facts, with sources

| item | what the public pages say | source |
|---|---|---|
| Entry | one GitHub commit with `submission.yaml`, the harness and the `artifacts/` that `eval/run.py` wrote on the 29 public dev tasks, plus a Kaggle Writeup | [rules.md](https://github.com/google-research/ple/blob/main/docs/rules.md), [ple-bench.com/competition/agents](https://ple-bench.com/competition/agents) |
| Writeup | at most 2,000 words; 5 rubric criteria; 3 required figures (architecture diagram, score-vs-cost plot, dev-set failure breakdown) | search snippets of the Kaggle page (not read directly) |
| Judging | Stage 1: a 100-point Writeup score and a pre-screening gate; the top 100 go to Stage 2, a live run on the 56 hidden tasks. Among finalists on the performance-cost Pareto frontier, the Stage 2 mean test score sets 1st-3rd. Ties: Writeup score, then earlier submission | same |
| Dates | final submission 5 January 2027; Stage 1 judging complete 19 January 2027 | same |
| Models | `google-cloud/` gemini-4-argon, gemini-3.8-flash, gemini-3.1-pro-preview, claude-opus-5-5, gpt-oss-120b, glm-5.2, gemma-4-26b, llama-4-maverick. Your own keys or model servers are not accepted for entries | [models.md](https://github.com/google-research/ple/blob/main/docs/models.md) |
| Who pays | models are sponsored during evaluation; local runs through the kit's proxy are billed to your own Google Cloud project; "any compatible proxy that serves the same model names and native APIs also works" locally | models.md |
| Coding agents | "Coding agents may help you build the harness" (there is an `AGENTS.md` page written for them) | [guide](https://ple-bench.com/competition/guide) |
| Harness sandbox | read-only root, uid 1000, 2 CPUs, 4 GB RAM; only the model endpoint is reachable; the task container has no network; 6 hours per task; `/opt/harness` up to 2 GiB compressed | agents page |
| Fair play | no hard-coded answers or task detection; never read graders or references; artifacts must come from `eval/run.py` with the declared model, never edited by hand; no web search or outside APIs; do not keep test-task content | rules.md |
| Dev tasks | 29 tasks, CC BY 4.0, in a gated (auto-approved) Hugging Face dataset; the terms forbid training on them and redistributing them | [HF dataset](https://huggingface.co/datasets/google/physical-engineerings-last-exam) |
| Local machine | Docker (WSL 2 on Windows), about 10 GB for base images plus large world images (about 17 GB, an hour or more to build); each task uses 2-4 CPUs and 4-12 GB plus 2 CPUs and 4.25 GB for its serve and egress containers | [eval/README.md](https://github.com/google-research/ple/blob/main/eval/README.md) |
| Local judge | `JUDGE_MODEL` defaults to `claude-opus-5-5` (any OpenAI-compatible endpoint can be configured) | eval/README.md |

## What the paper says matters (arXiv [2610.30537](https://arxiv.org/abs/2610.30537), CC BY 4.0)

- **The model dominates.** Scores spread about 50 points across models but only 0.7-12.1 points across harnesses
  for one model (median 3.0). With Claude Opus 5.5: Claude Code 50.6% at $17.18 a task, OpenHands 49.9% at
  $14.82, Codex 49.3% at $35.15, OpenCode 47.4% at $12.53, Pi 47.3% at $13.33. So, since ranking is among
  finalists on a performance-cost frontier, a harness can matter as much through **cost** as through score.
- **Hard constraints are the bottleneck.** With Opus 5.5 in Claude Code, deliverables meet 91% of constraints on
  average, but only 41.3% of items pass every hard constraint. An item that fails one hard constraint is capped at
  0.4 of its score (`s = 0.4 p + 0.6 G O'`).
- **A quarter of zero scores have nothing gradable.** 23.2% of all runs score 0; of those, 70.4% hand in files the
  grader scores 0, 25.3% never produce a gradable deliverable, and 4.3% time out or crash.
- **Citations are graded,** and environments contain deliberate distractors (superseded revisions, unrelated
  sheets).
- **Runs are noisy per task** (average range 15.4 points across three runs of one task), though harness means are
  stable (SD 0.3-1.8 points).

## What MV2 plans

An open-source (Apache-2.0) harness on `claude-opus-5-5` built around the two measured gaps above: an explicit,
clause-cited register of the task's hard constraints, a programmatic check of each deliverable against that
register before finishing, and an early draft of every required file, while keeping prompt caching tight to
stay cheap. Nothing has been run yet. Entering needs a Kaggle account, the gated dev data, Docker and model access
for local dev runs; those are being arranged. Results, negative or not, will be published here.

## Still to confirm (from Kaggle's Rules tab)

Eligibility (countries, companies, age), team size, whether winners must open-source the harness and under which
licence, the full Writeup rubric, and whether entrants get model credits for local dev runs.
