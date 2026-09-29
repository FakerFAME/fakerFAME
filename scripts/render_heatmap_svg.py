#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contrib-heatmap.svg"

CELL = 10
GAP = 3
LEFT = 52
TOP = 40

PALETTE = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    days = data.get("days", [])
    if not days:
        raise SystemExit("No contribution day data found")

    parsed = [
        {
            "date": datetime.strptime(item["date"], "%Y-%m-%d"),
            "count": int(item.get("count", 0)),
            "level": min(4, max(0, int(item.get("level", 0)))),
        }
        for item in days
    ]

    start = parsed[0]["date"]
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    week_count = ((parsed[-1]["date"] - start).days // 7) + 1
    width = LEFT + week_count * (CELL + GAP) + 40
    height = 240

    month_marks = {}
    for item in parsed:
        month_idx = item["date"].month - 1
        week_idx = (item["date"] - start).days // 7
        month_marks.setdefault((item["date"].year, month_idx), week_idx)

    rects = []
    for idx, item in enumerate(parsed):
        week_idx = (item["date"] - start).days // 7
        day_idx = (item["date"].weekday() + 1) % 7
        x = LEFT + week_idx * (CELL + GAP)
        y = TOP + day_idx * (CELL + GAP)
        delay = idx * 0.006
        color = PALETTE[item["level"]]
        title = f"{item['date'].date().isoformat()} · {item['count']} contributions"
        rects.append(
            f"<g><rect x='{x}' y='{y}' width='{CELL}' height='{CELL}' rx='2' fill='{color}' opacity='0' transform='translate(0,-5)'>"
            f"<title>{esc(title)}</title>"
            f"<animate attributeName='opacity' values='0;1' dur='0.35s' begin='{delay:.3f}s' fill='freeze'/>"
            f"<animateTransform attributeName='transform' type='translate' values='0 -5;0 0' dur='0.35s' begin='{delay:.3f}s' fill='freeze'/></rect></g>"
        )

    month_labels = []
    for (year, month_idx), week_idx in sorted(month_marks.items(), key=lambda kv: kv[1]):
        x = LEFT + week_idx * (CELL + GAP)
        month_labels.append(f"<text x='{x}' y='28' class='month'>{MONTHS[month_idx]}</text>")

    legend_x = width - 190
    total = int(data.get("total_contributions", data.get("calendar_total", 0)))
    current = int(data.get("current_streak", 0))
    longest = int(data.get("longest_streak", 0))
    best = data.get("best_day", {})
    best_text = f"{best.get('date', 'n/a')} ({best.get('count', 0)})"

    legend_cells = []
    for i in range(5):
        x = legend_x + 68 + i * 14
        legend_cells.append(f"<rect x='{x}' y='200' width='10' height='10' rx='2' fill='{PALETTE[i]}'/>")

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}' role='img' aria-label='Animated contribution heatmap'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='0' y2='1'>
      <stop offset='0%' stop-color='#0b0f11'/>
      <stop offset='100%' stop-color='#090b0d'/>
    </linearGradient>
    <filter id='glow'>
      <feGaussianBlur stdDeviation='0.8' result='b'/>
      <feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge>
    </filter>
  </defs>
  <rect x='0.5' y='0.5' width='{width-1}' height='{height-1}' rx='12' fill='url(#bg)' stroke='#1f2937'/>
  <text x='20' y='24' class='title'>fame@github ~ $ ./contributions.sh</text>
  {''.join(month_labels)}
  <text x='20' y='56' class='axis'>Sun</text>
  <text x='20' y='{56 + 2*(CELL+GAP)}' class='axis'>Tue</text>
  <text x='20' y='{56 + 4*(CELL+GAP)}' class='axis'>Thu</text>
  <text x='20' y='{56 + 6*(CELL+GAP)}' class='axis'>Sat</text>
  <g filter='url(#glow)'>
    {''.join(rects)}
  </g>
  <text x='20' y='178' class='meta'>total: {total}   current streak: {current}d   longest streak: {longest}d</text>
  <text x='20' y='198' class='meta'>best day: {esc(best_text)}</text>
  <text x='{legend_x}' y='209' class='legend'>less</text>
  {''.join(legend_cells)}
  <text x='{legend_x + 145}' y='209' class='legend'>more</text>
  <style>
    .title {{ fill: #39d353; font: 700 13px 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .month,.axis,.legend {{ fill: #7dd3fc; font: 11px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .meta {{ fill: #c9d1d9; font: 12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
  </style>
</svg>
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"[ok] Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
