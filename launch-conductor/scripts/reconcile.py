#!/usr/bin/env python3
"""
reconcile.py — deterministic reconciliation for a launch-conductor vault.

The model must not eyeball checkbox counts. This script is the single source
of truth for the computed fields: it counts real checkboxes per workstream
note, recomputes `percent_to_release`, infers `phase` from which phase
sections are complete, rewrites each note's frontmatter in place, and prints
an authoritative board table to stdout for the model to drop into
`Launch Dashboard.md`.

The model still authors the prose: `blocked_by`, `next_action`, and the
"Do this next" call (judgment). This script never touches those — it carries
them forward unchanged.

Usage:
    python3 reconcile.py /path/to/vault

Exit status is non-zero only on a usage/IO error, not on vault content.

Output: a JSON object on stdout:
    {
      "workstreams": [
        {"file": "Tally.md", "workstream": "Tally", "phase": "app-review",
         "percent_to_release": 64, "done": 9, "total": 14,
         "blocked_by": null, "next_action": "..."}
      ],
      "board_markdown": "| Workstream | Phase | % | Blocked by | Next action |\n..."
    }
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
from pathlib import Path

# Phase section headings, in launch order. A workstream's phase is the
# earliest section that still has an open item; all-checked -> last phase.
APP_PHASES = ["wiring", "internal-testing", "testflight", "app-review", "released"]
SITE_PHASES = ["building", "staging", "live"]

CHECK_OPEN = re.compile(r"^\s*-\s\[ \]\s")
CHECK_DONE = re.compile(r"^\s*-\s\[[xX]\]\s")
HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
DASHBOARD_NAME = "Launch Dashboard.md"


def split_frontmatter(text: str) -> tuple[dict[str, str], str, str]:
    """Return (fields, raw_frontmatter_block, body). Frontmatter is the
    leading --- ... --- block. Values are kept as raw strings; we only
    rewrite three known scalar fields so a full YAML parser isn't needed."""
    if not text.startswith("---"):
        return {}, "", text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, "", text
    block = text[: end + 4]
    body = text[end + 4 :]
    fields: dict[str, str] = {}
    for line in block.splitlines()[1:-1]:
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return fields, block, body


def phase_for(body: str, phases: list[str]) -> tuple[str, int, int]:
    """Count - [ ]/- [x] items and infer the current phase from which
    phase-named heading sections still contain an open item."""
    current_section: str | None = None
    open_by_section: dict[str, int] = {}
    done = open_count = 0
    for line in body.splitlines():
        h = HEADING.match(line)
        if h:
            name = h.group(1).strip().lower()
            current_section = name if name in phases else current_section
            continue
        if CHECK_OPEN.match(line):
            open_count += 1
            if current_section:
                open_by_section[current_section] = open_by_section.get(current_section, 0) + 1
        elif CHECK_DONE.match(line):
            done += 1
    total = done + open_count

    if total == 0:
        return phases[0], 0, 0
    for ph in phases:
        if open_by_section.get(ph, 0) > 0:
            return ph, done, total
    return phases[-1], done, total


def set_field(block: str, key: str, value: str) -> str:
    """Replace `key: ...` inside the frontmatter block, or insert before the
    closing ---. Quote strings that need it; numbers/None pass through."""
    line = f"{key}: {value}"
    pat = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if pat.search(block):
        return pat.sub(line, block, count=1)
    return block[:-4] + f"{line}\n---\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: reconcile.py /path/to/vault", file=sys.stderr)
        return 2
    vault = Path(argv[1])
    if not vault.is_dir():
        print(f"not a directory: {vault}", file=sys.stderr)
        return 2

    today = _dt.date.today().isoformat()
    rows: list[dict] = []

    for md in sorted(vault.glob("*.md")):
        if md.name == DASHBOARD_NAME:
            continue
        text = md.read_text(encoding="utf-8")
        fields, block, body = split_frontmatter(text)
        if not block:
            continue  # not a workstream note
        is_site = "website" in md.stem.lower() or fields.get("workstream", "").lower() == "website"
        phases = SITE_PHASES if is_site else APP_PHASES
        phase, done, total = phase_for(body, phases)
        pct = round(100 * done / total) if total else 0

        new_block = block
        new_block = set_field(new_block, "phase", phase)
        new_block = set_field(new_block, "percent_to_release", str(pct))
        new_block = set_field(new_block, "updated", today)
        if new_block != block:
            md.write_text(new_block + body, encoding="utf-8")

        blocked = fields.get("blocked_by", "null")
        blocked_disp = "—" if blocked in ("null", "", "~") else blocked.strip('"')
        nxt = fields.get("next_action", "").strip('"')
        rows.append(
            {
                "file": md.name,
                "workstream": fields.get("workstream", md.stem),
                "phase": phase,
                "percent_to_release": pct,
                "done": done,
                "total": total,
                "blocked_by": None if blocked in ("null", "", "~") else blocked.strip('"'),
                "next_action": nxt,
                "_blocked_disp": blocked_disp,
            }
        )

    header = "| Workstream | Phase | % | Blocked by | Next action |\n|---|---|---|---|---|"
    lines = [
        f"| [[{r['workstream']}]] | {r['phase']} | {r['percent_to_release']}% | "
        f"{r['_blocked_disp']} | {r['next_action']} |"
        for r in rows
    ]
    board = "\n".join([header, *lines])
    for r in rows:
        r.pop("_blocked_disp", None)
    print(json.dumps({"workstreams": rows, "board_markdown": board}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
