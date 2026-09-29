#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / "source-photo.jpg"
OUT = ROOT / "assets" / "fame-ascii.svg"
CHARSET = "@%#*+=-:. "


def fallback_art() -> list[str]:
    return [
        "            .-''''-.            ",
        "         .-'  .-.   '-.         ",
        "       .'    /   \\    '.       ",
        "      /     |  _  |     \\      ",
        "     ;      | (_) |      ;      ",
        "     |   .--'---'--.     |      ",
        "     ;  /  .-===-.  \\    ;      ",
        "      \\ |  | TTY |  |   /       ",
        "       '.\\  '---'  / .'         ",
        "         '-._____.-'             ",
    ]


def image_to_ascii() -> list[str] | None:
    if not PHOTO.exists():
        return None
    try:
        from PIL import Image
    except ImportError:
        return None

    img = Image.open(PHOTO).convert("L")
    width = 46
    ratio = img.height / img.width
    height = max(12, int(width * ratio * 0.45))
    img = img.resize((width, height))

    rows: list[str] = []
    for y in range(height):
        chars = []
        for x in range(width):
            pixel = img.getpixel((x, y))
            idx = int(pixel / 255 * (len(CHARSET) - 1))
            chars.append(CHARSET[idx])
        rows.append("".join(chars))
    return rows


def main() -> int:
    rows = image_to_ascii() or fallback_art()
    width = 720
    line_height = 20
    height = 90 + len(rows) * line_height

    lines = []
    for i, row in enumerate(rows):
        y = 52 + (i + 1) * line_height
        delay = 0.12 + i * 0.03
        safe = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(
            f"<text x='28' y='{y}' opacity='0'>{safe}<animate attributeName='opacity' values='0;1' dur='0.2s' begin='{delay:.2f}s' fill='freeze'/></text>"
        )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}' role='img' aria-label='ASCII terminal portrait'>
  <rect x='0.5' y='0.5' width='{width-1}' height='{height-1}' rx='12' fill='#090b0d' stroke='#1f2937'/>
  <text x='24' y='28' fill='#39d353' font-size='14' font-family='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'>fame@github ~ $ ./portrait.sh</text>
  <g fill='#c9d1d9' font-size='14' font-family='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' xml:space='preserve'>
    {''.join(lines)}
  </g>
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"[ok] Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
