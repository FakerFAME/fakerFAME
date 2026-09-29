#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_json() -> None:
    contrib_path = ROOT / "data" / "contributions.json"
    profile_path = ROOT / "data" / "profile.json"

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    for key in ["name", "username", "location", "role", "stack", "links", "projects"]:
        require(key in profile, f"profile.json missing required field: {key}")

    contrib = json.loads(contrib_path.read_text(encoding="utf-8"))
    for key in ["total_contributions", "active_days", "current_streak", "longest_streak", "best_day", "monthly_totals", "days"]:
        require(key in contrib, f"contributions.json missing required field: {key}")
    require(isinstance(contrib["days"], list) and len(contrib["days"]) > 0, "contributions.json days must be non-empty list")


def validate_svgs() -> None:
    required = [
        "assets/fame-ascii.svg",
        "assets/info-card.svg",
        "assets/contrib-heatmap.svg",
        "assets/stats.svg",
        "assets/wordmark.svg",
    ]
    for rel in required:
        path = ROOT / rel
        require(path.exists(), f"Missing SVG asset: {rel}")
        ET.fromstring(path.read_text(encoding="utf-8"))


def validate_readme_refs() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    refs = re.findall(r"assets/[A-Za-z0-9_.\-/]+", readme)
    require(refs, "README does not reference assets")
    for ref in refs:
        require((ROOT / ref).exists(), f"README references missing asset: {ref}")


def validate_python_syntax() -> None:
    for py_file in (ROOT / "scripts").glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        compile(source, str(py_file), "exec")


def main() -> int:
    validate_json()
    validate_svgs()
    validate_readme_refs()
    validate_python_syntax()
    print("[ok] Validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(1)
