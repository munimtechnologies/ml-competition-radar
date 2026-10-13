#!/usr/bin/env python3
"""ml-competition-radar: list open machine-learning and data competitions
that pay cash, sorted by prize and deadline.

Data source: the community-maintained competitions.json behind mlcontests.com
(https://github.com/mlcontests/mlcontests.github.io, GPL-3.0). This tool reads
that file at run time and does not redistribute it.

Standard library only. Python 3.9+.

Usage:
    python radar.py                      # open competitions, markdown table
    python radar.py --json               # same, as JSON
    python radar.py --days 45 --min-prize 5000
    python radar.py --tags tabular,nlp
    python radar.py --input competitions.json --today 2026-10-13   # offline

Made by MV2 of Munim, Inc. with AI agents working in his name.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.request

SOURCE_URL = (
    "https://raw.githubusercontent.com/mlcontests/mlcontests.github.io/"
    "master/competitions.json"
)

_MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}

_DATE_RE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{4})\s*$")
_TRACKING_RE = re.compile(r"[?&](ref|utm_[a-z]+)=[^&#]*")


def parse_date(value) -> dt.date | None:
    """Parse the 'D MMM YYYY' format used by competitions.json.

    Returns None for null, malformed or impossible dates (the file has a few).
    """
    if not isinstance(value, str):
        return None
    m = _DATE_RE.match(value)
    if not m:
        return None
    day, mon, year = int(m.group(1)), _MONTHS.get(m.group(2).lower()), int(m.group(3))
    if mon is None:
        return None
    try:
        return dt.date(year, mon, day)
    except ValueError:
        return None


def parse_prize(value) -> int:
    """Turn '$52,000' (or a number) into an integer USD amount; unknown -> 0."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else 0


def clean_url(url) -> str:
    """Drop ref/utm tracking parameters so the link is the plain competition URL."""
    if not isinstance(url, str):
        return ""
    url = _TRACKING_RE.sub("", url)
    # a leading '&' left behind after removing the first parameter
    url = re.sub(r"\?&", "?", url)
    return url.rstrip("?&")


def normalize(entry: dict) -> dict:
    return {
        "name": str(entry.get("name") or ""),
        "url": clean_url(entry.get("url")),
        "platform": str(entry.get("platform") or ""),
        "sponsor": str(entry.get("sponsor") or ""),
        "prize_usd": parse_prize(entry.get("prize")),
        "deadline": parse_date(entry.get("deadline")),
        "registration_deadline": parse_date(entry.get("registration-deadline")),
        "tags": [str(t) for t in (entry.get("tags") or [])],
    }


def select(entries, today: dt.date, days: int | None = None,
           min_prize: int = 1, tags=None) -> list[dict]:
    """Keep competitions still open on `today`, then filter and sort.

    min_prize=1 (default) drops entries with no listed cash prize; pass 0 to keep them.
    """
    wanted = set(t.strip().lower() for t in (tags or []) if t.strip())
    rows = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        n = normalize(entry)
        if n["deadline"] is None or n["deadline"] < today:
            continue
        if days is not None and (n["deadline"] - today).days > days:
            continue
        if n["prize_usd"] < min_prize:
            continue
        if wanted and not wanted & set(t.lower() for t in n["tags"]):
            continue
        rows.append(n)
    rows.sort(key=lambda r: (-r["prize_usd"], r["deadline"], r["name"]))
    return rows


def render_markdown(rows, today: dt.date) -> str:
    lines = [
        f"# Open ML competitions with cash prizes (as of {today.isoformat()})",
        "",
        "| Prize (USD) | Deadline | Days left | Competition | Platform | Tags |",
        "|---:|---|---:|---|---|---|",
    ]
    for r in rows:
        left = (r["deadline"] - today).days
        name = r["name"].replace("|", "\\|")
        link = f"[{name}]({r['url']})" if r["url"] else name
        lines.append(
            f"| {r['prize_usd']:,} | {r['deadline'].isoformat()} | {left} | {link} "
            f"| {r['platform']} | {', '.join(r['tags'])} |"
        )
    if not rows:
        lines.append("| - | - | - | (none match) | - | - |")
    lines.append("")
    lines.append(f"Source: {SOURCE_URL}")
    return "\n".join(lines) + "\n"


def to_jsonable(rows) -> list[dict]:
    out = []
    for r in rows:
        d = dict(r)
        d["deadline"] = r["deadline"].isoformat()
        d["registration_deadline"] = (
            r["registration_deadline"].isoformat() if r["registration_deadline"] else None
        )
        out.append(d)
    return out


def load_entries(path: str | None, url: str = SOURCE_URL, timeout: int = 30):
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "ml-competition-radar/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, dict):
        # tolerate a wrapper object such as {"competitions": [...]}
        for v in data.values():
            if isinstance(v, list):
                return v
        return []
    return data if isinstance(data, list) else []


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="List open ML competitions with cash prizes.")
    p.add_argument("--input", help="read a local competitions.json instead of fetching")
    p.add_argument("--today", help="YYYY-MM-DD (default: today, UTC)")
    p.add_argument("--days", type=int, help="only deadlines within N days")
    p.add_argument("--min-prize", type=int, default=1, help="minimum USD prize (default 1)")
    p.add_argument("--tags", help="comma-separated tags; keep rows with any of them")
    p.add_argument("--json", action="store_true", help="output JSON instead of markdown")
    args = p.parse_args(argv)

    today = (dt.date.fromisoformat(args.today) if args.today
             else dt.datetime.now(dt.timezone.utc).date())
    tags = args.tags.split(",") if args.tags else None
    try:
        entries = load_entries(args.input)
    except Exception as exc:  # network or parse failure
        print(f"error: could not load competitions: {exc}", file=sys.stderr)
        return 2
    rows = select(entries, today, days=args.days, min_prize=args.min_prize, tags=tags)
    if args.json:
        print(json.dumps(to_jsonable(rows), indent=2))
    else:
        sys.stdout.write(render_markdown(rows, today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
