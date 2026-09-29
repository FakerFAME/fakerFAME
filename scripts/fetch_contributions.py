#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "contributions.json"
PROFILE_PATH = ROOT / "data" / "profile.json"
CONTRIB_URL_TEMPLATE = "https://github.com/users/{username}/contributions"


@dataclass
class DayContribution:
    day: date
    count: int
    level: int


def _parse_count(raw: str | None) -> int:
    if not raw:
        return 0
    text = raw.strip().lower()
    if "no contribution" in text:
        return 0
    match = re.search(r"(\d+)\s+contributions?", text)
    if not match and text.isdigit():
        return int(text)
    if not match:
        match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else 0


def _parse_level(raw: str | None, count: int) -> int:
    if raw and raw.isdigit():
        return int(raw)
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def _calc_streaks(days: list[DayContribution]) -> tuple[int, int]:
    longest = 0
    current = 0
    run = 0
    previous: date | None = None

    for item in sorted(days, key=lambda d: d.day):
        if previous and (item.day - previous).days > 1:
            run = 0
        if item.count > 0:
            run = run + 1 if previous and (item.day - previous).days == 1 else 1
            longest = max(longest, run)
        else:
            run = 0
        previous = item.day

    for item in sorted(days, key=lambda d: d.day, reverse=True):
        if item.count > 0:
            current += 1
        else:
            break

    return current, longest


def _load_username() -> str:
    if PROFILE_PATH.exists():
        try:
            profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            username = profile.get("username")
            if isinstance(username, str) and username.strip():
                return username.strip()
        except json.JSONDecodeError:
            pass
    return "FakerFAME"


def fetch() -> dict[str, Any]:
    username = _load_username()
    url = CONTRIB_URL_TEMPLATE.format(username=username)
    response = requests.get(url, timeout=30, headers={"User-Agent": "profile-readme-generator"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("rect.ContributionCalendar-day, td.ContributionCalendar-day, td[data-date][data-level]")
    if not cells:
        raise ValueError("No contribution cells found in GitHub contribution calendar HTML")

    tooltip_counts: dict[str, int] = {}
    for tip in soup.select("tool-tip[for]"):
        ref = tip.get("for")
        if not ref:
            continue
        tooltip_counts[ref] = _parse_count(tip.get_text(" ", strip=True))

    days: list[DayContribution] = []
    for cell in cells:
        day_raw = cell.get("data-date")
        if not day_raw:
            continue
        try:
            day = datetime.strptime(day_raw, "%Y-%m-%d").date()
        except ValueError:
            continue
        count = _parse_count(cell.get("data-count") or cell.get("aria-label"))
        if count == 0:
            cell_id = cell.get("id")
            if cell_id and cell_id in tooltip_counts:
                count = tooltip_counts[cell_id]
        level = _parse_level(cell.get("data-level"), count)
        days.append(DayContribution(day=day, count=count, level=level))

    if not days:
        raise ValueError("Parsed contribution calendar but found no valid dated cells")

    total = sum(item.count for item in days)
    active_days = sum(1 for item in days if item.count > 0)
    current_streak, longest_streak = _calc_streaks(days)
    best = max(days, key=lambda item: item.count)

    monthly_totals: dict[str, int] = defaultdict(int)
    for item in days:
        key = f"{item.day.year:04d}-{item.day.month:02d}"
        monthly_totals[key] += item.count

    title = soup.select_one("h2")
    summary_total = None
    if title:
        summary_total = _parse_count(title.get_text(strip=True))

    payload: dict[str, Any] = {
        "username": username,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": url,
        "total_contributions": summary_total if summary_total and summary_total >= total else total,
        "calendar_total": total,
        "active_days": active_days,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best.day.isoformat(), "count": best.count, "level": best.level},
        "monthly_totals": dict(sorted(monthly_totals.items())),
        "days": [
            {"date": item.day.isoformat(), "count": item.count, "level": item.level}
            for item in sorted(days, key=lambda d: d.day)
        ],
    }
    return payload


def main() -> int:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DATA_PATH.read_text(encoding="utf-8") if DATA_PATH.exists() else None

    try:
        payload = fetch()
    except Exception as exc:  # noqa: BLE001
        print(f"[error] Failed to fetch contributions: {exc}", file=sys.stderr)
        if existing:
            print("[info] Existing data/contributions.json preserved", file=sys.stderr)
        return 1

    DATA_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote {DATA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
