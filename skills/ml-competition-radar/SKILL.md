---
name: ml-competition-radar
description: List open machine-learning and data-science competitions that pay cash prizes (from mlcontests.com's public list and Zindi's public API), sorted by prize and deadline. Use when someone asks which ML, data-science or AI competitions are open now, which ones close soon, or which pay at least a given amount. Read-only, no keys, Python standard library only.
---

# ml-competition-radar

A single-file, read-only Python script by MV2 of Munim, Inc. (made with AI agents working in his
name; Apache-2.0). It fetches two public lists and prints the competitions that are still open,
with prize, deadline and link:

- mlcontests.com's competitions.json (read at run time from
  raw.githubusercontent.com/mlcontests/mlcontests.github.io; that data is GPL-3.0 and is not copied)
- Zindi's public competitions API (api.zindi.world/v1/competitions)

It sends plain unauthenticated GET requests and writes nothing to disk.

## When to use it

- "What ML / Kaggle-style / data-science competitions are open right now?"
- "Which AI competitions with prize money close in the next 30 days?"
- "Find open competitions paying at least $10,000" or "...tagged NLP / vision / forecasting".

Don't use it to register, accept rules, download competition data or submit anything. Those steps
belong to the user, on the competition's own site.

## How to run it

```bash
curl -fsSLO https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/main/radar.py
python3 radar.py --json --days 30 --min-prize 1000
```

Python 3.9 or newer. Useful flags (version 0.2.0):

| Flag | Meaning |
|---|---|
| `--json` | JSON list instead of a Markdown table (use this when you will process the output) |
| `--days N` | only deadlines within N days of today (UTC) |
| `--min-prize N` | minimum prize in USD (default 1; `0` also keeps unpaid contests) |
| `--tags a,b` | keep rows having any of these tags (case-insensitive) |
| `--sources mlcontests,zindi` | choose sources (default: both) |
| `--include-restricted` | also list invite-only or code-gated contests (hidden by default) |
| `--today YYYY-MM-DD` | pretend today is another date |
| `--input FILE` / `--zindi-input FILE` | read saved copies instead of fetching |

If one source fails, it prints a warning and continues with the other; if every source fails, or a
`--sources` name is unknown, it exits with code 2.

## Reading the output

Each JSON row has `name`, `url`, `platform`, `sponsor`, `prize_usd`, `prize_text`, `cash`,
`deadline` (ISO date), `registration_deadline` (ISO date or null), `tags`, `restricted`, `source`.
Rows are sorted by prize (highest first), then deadline.

- `prize_usd` is 0 for cash prizes in other currencies (no conversion is attempted); read
  `prize_text` for those.
- `deadline` is the final submission date as the source lists it. Platforms move deadlines, and
  entry or team-merger deadlines often come earlier: check `registration_deadline` and the
  competition's own page.
- Zindi rows carry only the competition kind as their tag.

## Before you recommend a competition

Tell the user to confirm these on the organiser's own rules page. The radar does not check them:

1. Eligibility: country, age, student-only, and whether companies may win prizes.
2. Whether the rules allow AI-assisted or AI-written entries, and how the entry must disclose AI.
3. Account steps, such as an identity or phone check, that have to be done before the first
   submission.
4. How the prize is paid (cash, credits, crypto) and whether winners must publish their code.

Present the list as a starting point, not as advice that a contest is worth entering.

## Source

https://github.com/munimtechnologies/ml-competition-radar (Apache-2.0). Issues and corrections are
welcome there.
