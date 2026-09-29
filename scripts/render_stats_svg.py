#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "profile.json"
CONTRIB = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "stats.svg"


def fetch_user(username: str) -> dict:
    url = f"https://api.github.com/users/{username}"
    res = requests.get(url, timeout=30, headers={"User-Agent": "profile-readme-generator"})
    if res.ok:
        return res.json()
    return {}


def scrape_user_summary(username: str) -> dict[str, int]:
    url = f"https://github.com/{username}"
    res = requests.get(url, timeout=30, headers={"User-Agent": "profile-readme-generator"})
    if not res.ok:
        return {}
    soup = BeautifulSoup(res.text, "html.parser")
    values: dict[str, int] = {}
    selectors = {
        "public_repos": "a[href$='?tab=repositories'] span.Counter",
        "followers": "a[href$='?tab=followers'] span.text-bold",
        "following": "a[href$='?tab=following'] span.text-bold",
    }
    for key, selector in selectors.items():
        node = soup.select_one(selector)
        if not node:
            continue
        raw = node.get_text(strip=True).replace(",", "")
        if raw.isdigit():
            values[key] = int(raw)
    return values


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def metric(x: int, y: int, label: str, value: str, delay: float) -> str:
    return (
        f"<g transform='translate({x},{y})' opacity='0'>"
        f"<rect width='195' height='72' rx='8' fill='#0f172a' stroke='#1f2937'/>"
        f"<text x='12' y='28' fill='#7dd3fc' font-size='12'>{esc(label)}</text>"
        f"<text x='12' y='54' fill='#39d353' font-size='22' font-weight='700'>{esc(value)}</text>"
        f"<animate attributeName='opacity' values='0;1' dur='0.25s' begin='{delay:.2f}s' fill='freeze'/>"
        "</g>"
    )


def main() -> int:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    username = profile.get("username", "FakerFAME")
    contrib = json.loads(CONTRIB.read_text(encoding="utf-8")) if CONTRIB.exists() else {}

    user = fetch_user(username)
    scraped = scrape_user_summary(username)

    def take(metric: str) -> str | None:
        if metric in user and isinstance(user[metric], int):
            return str(user[metric])
        if metric in scraped and isinstance(scraped[metric], int):
            return str(scraped[metric])
        return None

    metrics = []
    for label, key in [("public repos", "public_repos"), ("followers", "followers"), ("following", "following"), ("public gists", "public_gists")]:
        value = take(key)
        if value is not None:
            metrics.append((label, value))
    metrics.append(("calendar total", str(contrib.get("total_contributions", 0))))
    metrics.append(("current streak", str(contrib.get("current_streak", 0))))

    cards = []
    for i, (label, value) in enumerate(metrics):
        col = i % 3
        row = i // 3
        cards.append(metric(20 + col * 210, 48 + row * 92, label, value, 0.08 * i))

    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='670' height='250' viewBox='0 0 670 250' role='img' aria-label='GitHub profile stats'>
  <rect x='0.5' y='0.5' width='669' height='249' rx='12' fill='#090b0d' stroke='#1f2937'/>
  <text x='20' y='28' fill='#39d353' font-family='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' font-size='14'>fame@github ~ $ ./stats.sh</text>
  <g font-family='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'>
    {''.join(cards)}
  </g>
  <text x='20' y='236' fill='#94a3b8' font-family='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' font-size='11'>updated: {stamp}</text>
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"[ok] Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
