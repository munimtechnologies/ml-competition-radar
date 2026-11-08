#!/usr/bin/env python3
"""ml-competition-radar: list open machine-learning and data competitions
that pay cash, sorted by prize and deadline.

Data sources, read at run time and never redistributed:
  - mlcontests: the community-maintained competitions.json behind mlcontests.com
    (https://github.com/mlcontests/mlcontests.github.io, GPL-3.0)
  - zindi: Zindi's public competition listing (https://zindi.world), which
    carries Zindi challenges that mlcontests does not list

Standard library only. Python 3.9+.

Usage:
    python radar.py                      # open competitions, markdown table
    python radar.py --json               # same, as JSON
    python radar.py --days 45 --min-prize 5000
    python radar.py --tags tabular,nlp
    python radar.py --sources zindi      # one source only
    python radar.py --input competitions.json --today 2026-10-13   # offline
    python radar.py --input competitions.json --zindi-input zindi.json  # offline, both

Made by MV2 of Munim, Inc. with AI agents working in his name.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.request

__version__ = "0.2.0"

SOURCE_URL = (
    "https://raw.githubusercontent.com/mlcontests/mlcontests.github.io/"
    "master/competitions.json"
)
ZINDI_API_URL = "https://api.zindi.world/v1/competitions"
ZINDI_PAGE_URL = "https://zindi.world/competitions/"
SOURCES = ("mlcontests", "zindi")
USER_AGENT = f"ml-competition-radar/{__version__}"

_MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}

_DATE_RE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{4})\s*$")
_ISO_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})")
_TRACKING_RE = re.compile(r"[?&](ref|utm_[a-z]+)=[^&#]*")
_CURRENCY_RE = re.compile(r"\b([A-Z]{3})\s*$")
_POINTS_RE = re.compile(r"\bpoints?\b", re.IGNORECASE)


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


def parse_iso_date(value) -> dt.date | None:
    """Date part of an ISO timestamp such as '2026-10-31T23:59:00.000Z' (UTC)."""
    if not isinstance(value, str):
        return None
    m = _ISO_RE.match(value)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
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


def parse_reward(text) -> tuple[int, str | None, bool]:
    """Parse a Zindi reward string into (amount, currency, is_cash).

    '$10 000 USD' -> (10000, 'USD', True); 'R25 000 ZAR' -> (25000, 'ZAR', True);
    '500 Points' -> (500, None, False); anything unreadable -> (0, None, False).
    """
    if not isinstance(text, str) or not text.strip():
        return 0, None, False
    if _POINTS_RE.search(text):
        return parse_prize(text), None, False
    amount = parse_prize(text)
    m = _CURRENCY_RE.search(text.strip())
    currency = m.group(1) if m else ("USD" if "$" in text else None)
    if amount <= 0 or currency is None:
        return 0, None, False
    return amount, currency, True


def clean_url(url) -> str:
    """Drop ref/utm tracking parameters so the link is the plain competition URL."""
    if not isinstance(url, str):
        return ""
    url = _TRACKING_RE.sub("", url)
    # a leading '&' left behind after removing the first parameter
    url = re.sub(r"\?&", "?", url)
    return url.rstrip("?&")


def normalize(entry: dict) -> dict:
    """Normalise one mlcontests competitions.json entry."""
    prize_usd = parse_prize(entry.get("prize"))
    return {
        "name": str(entry.get("name") or ""),
        "url": clean_url(entry.get("url")),
        "platform": str(entry.get("platform") or ""),
        "sponsor": str(entry.get("sponsor") or ""),
        "prize_usd": prize_usd,
        "prize_text": str(entry.get("prize") or ""),
        "cash": prize_usd > 0,
        "deadline": parse_date(entry.get("deadline")),
        "registration_deadline": parse_date(entry.get("registration-deadline")),
        "tags": [str(t) for t in (entry.get("tags") or [])],
        "restricted": False,
        "source": "mlcontests",
    }


def _org_name(org) -> str:
    if isinstance(org, dict):
        return str(org.get("name") or org.get("title") or "")
    return str(org) if isinstance(org, str) else ""


def normalize_zindi(entry: dict) -> dict:
    """Normalise one object from Zindi's competition listing.

    Non-USD cash prizes keep prize_usd 0 and show their own amount in prize_text;
    no exchange rate is guessed.
    """
    amount, currency, cash = parse_reward(entry.get("reward"))
    slug = str(entry.get("id") or "")
    restricted = bool(entry.get("is_access_restricted")) or bool(entry.get("secret_code_required"))
    kind = str(entry.get("kind") or "")
    return {
        "name": str(entry.get("title") or slug),
        "url": ZINDI_PAGE_URL + slug if slug else "",
        "platform": "Zindi",
        "sponsor": _org_name(entry.get("organization")),
        "prize_usd": amount if cash and currency == "USD" else 0,
        "prize_text": str(entry.get("reward") or ""),
        "cash": cash,
        "deadline": parse_iso_date(entry.get("end_time")),
        "registration_deadline": parse_iso_date(entry.get("entries_close_at")),
        "tags": [kind] if kind else [],
        "restricted": restricted,
        "open": entry.get("open"),
        "source": "zindi",
    }


def _keep(row: dict, today: dt.date, days, min_prize: int, wanted, include_restricted: bool) -> bool:
    if row["deadline"] is None or row["deadline"] < today:
        return False
    if row.get("open") is False:
        return False
    if row.get("restricted") and not include_restricted:
        return False
    if days is not None and (row["deadline"] - today).days > days:
        return False
    if row["prize_usd"] < min_prize:
        # a cash prize in another currency counts as "has cash" for the default filter
        if not (row.get("cash") and row["prize_usd"] == 0 and min_prize <= 1):
            return False
    if wanted and not wanted & set(t.lower() for t in row["tags"]):
        return False
    return True


def select_rows(rows, today: dt.date, days: int | None = None, min_prize: int = 1,
                tags=None, include_restricted: bool = False) -> list[dict]:
    """Filter normalised rows from any source, drop duplicates, sort by prize then deadline."""
    wanted = set(t.strip().lower() for t in (tags or []) if t.strip())
    out, seen = [], set()
    for r in rows:
        if not _keep(r, today, days, min_prize, wanted, include_restricted):
            continue
        key = re.sub(r"[^a-z0-9]", "", r["name"].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    out.sort(key=lambda r: (-r["prize_usd"], r["deadline"], r["name"]))
    return out


def select(entries, today: dt.date, days: int | None = None,
           min_prize: int = 1, tags=None) -> list[dict]:
    """Keep mlcontests competitions still open on `today`, then filter and sort.

    min_prize=1 (default) drops entries with no listed cash prize; pass 0 to keep them.
    """
    rows = [normalize(e) for e in entries if isinstance(e, dict)]
    return select_rows(rows, today, days=days, min_prize=min_prize, tags=tags)


def _prize_cell(r) -> str:
    if r["prize_usd"] > 0:
        return f"{r['prize_usd']:,}"
    if r.get("cash") and r.get("prize_text"):
        return r["prize_text"].replace("|", "\\|")
    return "0"


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
            f"| {_prize_cell(r)} | {r['deadline'].isoformat()} | {left} | {link} "
            f"| {r['platform']} | {', '.join(r['tags'])} |"
        )
    if not rows:
        lines.append("| - | - | - | (none match) | - | - |")
    lines.append("")
    lines.append(f"Sources: {SOURCE_URL} ; {ZINDI_API_URL}")
    lines.append("Non-USD prizes are shown in their own currency.")
    return "\n".join(lines) + "\n"


def to_jsonable(rows) -> list[dict]:
    out = []
    for r in rows:
        d = dict(r)
        d.pop("open", None)
        d["deadline"] = r["deadline"].isoformat()
        d["registration_deadline"] = (
            r["registration_deadline"].isoformat() if r["registration_deadline"] else None
        )
        out.append(d)
    return out


def _fetch_json(url: str, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_entries(path: str | None, url: str = SOURCE_URL, timeout: int = 30):
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        data = _fetch_json(url, timeout)
    if isinstance(data, dict):
        # tolerate a wrapper object such as {"competitions": [...]}
        for v in data.values():
            if isinstance(v, list):
                return v
        return []
    return data if isinstance(data, list) else []


def zindi_items(payload) -> list[dict]:
    """Competition objects from one Zindi listing payload ({"data": [...], "meta": {...}})."""
    if isinstance(payload, dict):
        data = payload.get("data")
        return [d for d in data if isinstance(d, dict)] if isinstance(data, list) else []
    if isinstance(payload, list):
        return [d for d in payload if isinstance(d, dict)]
    return []


def load_zindi(path: str | None = None, url: str = ZINDI_API_URL, timeout: int = 30,
               max_pages: int = 10, fetch=None) -> list[dict]:
    """Zindi competitions; open ones come first in the listing.

    Pages are requested until every open competition counted in meta.open_count
    has been seen, a page repeats or comes back empty, or max_pages is reached.
    """
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return zindi_items(json.load(fh))
    fetch = fetch or (lambda u: _fetch_json(u, timeout))
    items, seen = [], set()
    for page in range(1, max_pages + 1):
        payload = fetch(url if page == 1 else f"{url}?page={page}")
        batch = [d for d in zindi_items(payload) if d.get("id") not in seen]
        if not batch:
            break
        for d in batch:
            seen.add(d.get("id"))
        items.extend(batch)
        meta = payload.get("meta") if isinstance(payload, dict) else None
        open_count = meta.get("open_count") if isinstance(meta, dict) else None
        n_open = sum(1 for d in items if d.get("open"))
        if open_count is not None and n_open >= open_count:
            break
        if open_count is None:
            break
    return items


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="List open ML competitions with cash prizes.")
    p.add_argument("--input", help="read a local mlcontests competitions.json instead of fetching")
    p.add_argument("--zindi-input", help="read a saved Zindi listing JSON instead of fetching")
    p.add_argument("--sources", default=None,
                   help="comma-separated: mlcontests,zindi (default: both; with --input only, mlcontests)")
    p.add_argument("--today", help="YYYY-MM-DD (default: today, UTC)")
    p.add_argument("--days", type=int, help="only deadlines within N days")
    p.add_argument("--min-prize", type=int, default=1, help="minimum USD prize (default 1)")
    p.add_argument("--tags", help="comma-separated tags; keep rows with any of them")
    p.add_argument("--include-restricted", action="store_true",
                   help="also list invite-only or code-gated competitions")
    p.add_argument("--json", action="store_true", help="output JSON instead of markdown")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)

    today = (dt.date.fromisoformat(args.today) if args.today
             else dt.datetime.now(dt.timezone.utc).date())
    tags = args.tags.split(",") if args.tags else None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    elif args.input and not args.zindi_input:
        sources = ["mlcontests"]  # offline run on one file stays offline
    else:
        sources = list(SOURCES)
    unknown = [s for s in sources if s not in SOURCES]
    if unknown:
        print(f"error: unknown source(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    rows, failures = [], 0
    for source in sources:
        try:
            if source == "mlcontests":
                rows += [normalize(e) for e in load_entries(args.input) if isinstance(e, dict)]
            else:
                rows += [normalize_zindi(e) for e in load_zindi(args.zindi_input)]
        except Exception as exc:  # network or parse failure: report, keep the other source
            failures += 1
            print(f"warning: could not load {source}: {exc}", file=sys.stderr)
    if failures == len(sources):
        print("error: could not load competitions from any source", file=sys.stderr)
        return 2

    rows = select_rows(rows, today, days=args.days, min_prize=args.min_prize, tags=tags,
                       include_restricted=args.include_restricted)
    if args.json:
        print(json.dumps(to_jsonable(rows), indent=2))
    else:
        sys.stdout.write(render_markdown(rows, today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
