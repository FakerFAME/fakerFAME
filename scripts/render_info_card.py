#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "profile.json"
OUT = ROOT / "assets" / "info-card.svg"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    stack = profile.get("stack", {})
    selected = [
        *stack.get("languages", [])[:3],
        *stack.get("frontend", [])[:2],
        *stack.get("aiml", [])[:2],
    ]

    lines = [
        "fame@github:~$ whoami",
        f"> {profile.get('name', '')}",
        "fame@github:~$ status",
        f"> {profile.get('terminal', {}).get('status', '')}",
        f"NAME       {profile.get('name', '')}",
        f"USERNAME   {profile.get('username', '')}",
        f"ROLE       {profile.get('role', '')}",
        f"LOCATION   {profile.get('location', '')}",
        f"SKILLS     {', '.join(selected)}",
    ]

    text_nodes = []
    for i, line in enumerate(lines):
        y = 38 + i * 24
        color = "#39d353" if line.startswith("fame@") else ("#7dd3fc" if line.startswith(">") else "#c9d1d9")
        text_nodes.append(
            f"<text x='24' y='{y}' fill='{color}' opacity='0'>{esc(line)}"
            f"<animate attributeName='opacity' values='0;1' dur='0.2s' begin='{0.08 * i:.2f}s' fill='freeze'/></text>"
        )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='900' height='280' viewBox='0 0 900 280' role='img' aria-label='Terminal profile card'>
  <rect x='0.5' y='0.5' width='899' height='279' rx='12' fill='#090b0d' stroke='#1f2937'/>
  <g font-size='16' font-family='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'>
    {''.join(text_nodes)}
    <text x='24' y='260' fill='#39d353'>▋<animate attributeName='opacity' values='1;0;1' dur='1s' repeatCount='indefinite'/></text>
  </g>
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"[ok] Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
