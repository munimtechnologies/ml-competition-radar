# ml-competition-radar

Version: ml-competition-radar 0.2.0

A small command-line tool that lists the machine-learning and data-science
competitions that are open right now and pay cash, sorted by prize and
deadline. Standard library only, no API keys, Python 3.9+.

```
python radar.py                              # markdown table of open cash competitions
python radar.py --json                       # same as JSON
python radar.py --days 45 --min-prize 5000   # closing within 45 days, at least $5,000
python radar.py --tags tabular,nlp           # only competitions tagged tabular or nlp
python radar.py --sources zindi              # one source only (mlcontests, zindi)
python radar.py --include-restricted         # also invite-only / code-gated challenges
python radar.py --input competitions.json --today 2026-10-13   # offline / reproducible
python radar.py --input competitions.json --zindi-input zindi.json  # offline, both sources
```

Example output (14 Oct 2026, abridged):

| Prize (USD) | Deadline | Days left | Competition | Platform |
|---:|---|---:|---|---|
| 850,000 | 2026-11-02 | 19 | ARC Prize 2026 - ARC-AGI-3 | Kaggle |
| 52,000 | 2026-12-31 | 78 | Predict Cross-sectional Equity Returns | CrunchDAO |
| 14,925 | 2026-11-15 | 32 | Optimise LLM Operators & Inference Across AI Chips | Independent |
| 10,000 | 2026-10-31 | 17 | Bias Bounty Mapping Equity Challenge | Zindi |
| R25 000 ZAR | 2026-10-18 | 4 | Sasol Customer Value Recruitment Challenge | Zindi |

## Where the data comes from

- **mlcontests**: `competitions.json` from the community-maintained
  [mlcontests/mlcontests.github.io](https://github.com/mlcontests/mlcontests.github.io)
  repository (GPL-3.0). If you spot a missing competition, add it there so everyone benefits.
- **zindi** (new in 0.2.0): Zindi's public competition listing at
  `https://api.zindi.world/v1/competitions`. On 14 Oct 2026 it carried a
  $10,000 challenge (Bias Bounty Mapping Equity) that mlcontests did not list.

Both are read at run time; nothing is bundled or redistributed. If one source
fails, the radar prints a warning and lists the other.

Tracking parameters (`ref=`, `utm_*`) are stripped from links. Entries with a
missing or malformed deadline are skipped. Competitions listed by both
sources appear once. `--min-prize 0` also shows competitions without a cash
prize (for example Zindi points-only challenges).

Prizes in other currencies are shown in that currency (no exchange rate is
guessed). They count as "has a cash prize" for the default filter. A USD
threshold such as `--min-prize 1000` leaves them out.

Zindi challenges that are invite-only or need a secret code (university or
company hackathons) are hidden unless you pass `--include-restricted`.

## Tests

```
python -m unittest test_radar.py
```

The tests are offline and use small fixtures shaped like both sources.

## Why

Prize competitions are one lane in which work made in the open can earn money.
MV2 of Munim, Inc. uses this radar to pick which ones to enter. Entries
made in MV2's name are made with AI agents and say so wherever a competition
asks.

## Changelog

- 0.2.0: Zindi source; non-USD cash prizes; `--sources`, `--zindi-input`,
  `--include-restricted`, `--version`; cross-source de-duplication; one failing
  source no longer stops the run.
- 0.1.0: first release (mlcontests source).

## License

Apache-2.0. Made by MV2 of Munim, Inc. with AI agents working in his name.
