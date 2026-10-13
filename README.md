# ml-competition-radar

Version: ml-competition-radar 0.1.0

A small command-line tool that lists the machine-learning and data-science
competitions that are open right now and pay cash, sorted by prize and
deadline. Standard library only, no API keys, Python 3.9+.

```
python radar.py                              # markdown table of open cash competitions
python radar.py --json                       # same as JSON
python radar.py --days 45 --min-prize 5000   # closing within 45 days, at least $5,000
python radar.py --tags tabular,nlp           # only competitions tagged tabular or nlp
python radar.py --input competitions.json --today 2026-10-13   # offline / reproducible
```

Example output (13 Oct 2026, abridged):

| Prize (USD) | Deadline | Days left | Competition | Platform |
|---:|---|---:|---|---|
| 850,000 | 2026-11-02 | 20 | ARC Prize 2026 - ARC-AGI-3 | Kaggle |
| 700,000 | 2026-11-02 | 20 | ARC Prize 2026 - ARC-AGI-2 | Kaggle |
| 100,000 | 2027-01-06 | 85 | NFL Big Data Bowl 2027 | Kaggle |
| 65,000 | 2026-12-02 | 50 | Build Coding Agents with Gemma 4 | Kaggle |
| 54,000 | 2026-10-25 | 12 | Generative Modeling of Mouse Embryo Development | Independent |
| 52,000 | 2026-12-31 | 79 | Predict Cross-sectional Equity Returns | CrunchDAO |
| 50,000 | 2026-12-14 | 62 | Predict 2D Chemical Structures From Mass Spectra | Kaggle |

## Where the data comes from

The tool reads `competitions.json` from the community-maintained
[mlcontests/mlcontests.github.io](https://github.com/mlcontests/mlcontests.github.io)
repository (GPL-3.0) at run time. It does not bundle or redistribute that data.
If you spot a missing competition, add it there so everyone benefits.

Tracking parameters (`ref=`, `utm_*`) are stripped from links. Entries with a
missing or malformed deadline are skipped. `--min-prize 0` also shows
competitions without a listed cash prize.

## Tests

```
python -m unittest test_radar.py
```

The tests are offline and use a small fixture.

## Why

Prize competitions are one lane in which work made in the open can earn money.
This radar is what MV2 of Munim, Inc. uses to pick which ones to enter. Entries
made in MV2's name are made with AI agents and say so wherever a competition
asks.

## License

MIT. Made by MV2 of Munim, Inc. with AI agents working in his name.
