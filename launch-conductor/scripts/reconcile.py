#!/usr/bin/env python3
"""
reconcile.py — deterministic reconciliation for a launch-conductor vault.

The model must not eyeball checkbox counts. This script is the single source
of truth for the computed fields. On each run it first **harvests** the
existing dashboard — any `- [x]` the user ticked under a `### [[Workstream]]`
lane is flipped into its twin `- [ ]` in that workstream's note — then counts
real checkboxes per note, recomputes `percent_to_release`, infers `phase` from
which phase sections are complete, rewrites each note's frontmatter in place,
and prints an authoritative board table to stdout for the model to drop into
`Launch Dashboard.md`.

Run order is load-bearing: the model must run this script **before**
overwriting `Launch Dashboard.md`, or the harvest reads a freshly regenerated
board with the user's ticks already gone.

The model still authors the prose: `blocked_by`, `next_action`, `next_actor`,
`human_blocked_until`, and the "Do this next" call (judgment). This script
never touches those — it carries them forward unchanged.

Usage:
    python3 reconcile.py /path/to/vault

Exit status is non-zero only on a usage/IO error, not on vault content.

Output: a JSON object on stdout:
    {
      "workstreams": [
        {"file": "Tally.md", "workstream": "Tally", "phase": "app-review",
         "percent_to_release": 64, "done": 9, "total": 14,
         "blocked_by": null, "next_action": "...",
         "next_actor": "agent", "human_blocked_until": null,
         "human_blocked": false,
         "phase_open_items": ["Store listing + screenshots", "..."],
         "repo_path": null, "repo": null}
      ],
      "board_markdown": "| Workstream | Phase | % | Actor | Blocked by |\n...",
      "harvested": [{"workstream": "Edict", "item": "...", "file": "Edict.md"}],
      "harvest_unmatched": [{"workstream": "Edict", "item": "...",
                             "reason": "no matching open item in note"}]
    }

`harvested` is the dashboard ticks this run flipped into notes (report them so
the user sees the sync happened). `harvest_unmatched` is ticks with no twin —
text was edited on the board, or the workstream is unknown; surface these, do
not silently drop them.

`phase_open_items` is the open `- [ ]` checkbox texts in the workstream's
computed phase section — the live work front. The dashboard mirrors the first
3 of these under each agent workstream as two-way `- [ ]` checkboxes (the
harvest above syncs ticks back); the Next action column is gone from the table
because the items now carry that detail.

`repo_path` (local path) and `repo` (GitHub owner/repo slug) are optional
authored fields, carried forward untouched like `blocked_by`. They let the
model read a project's actual code to propose which checklist items are
already done — see SKILL.md "Code-grounded audit".

`next_actor` defaults to "agent" when absent (pre-existing vaults degrade to
dispatchable). `human_blocked_until` is None unless authored; when it parses as
an ISO date strictly after today, `human_blocked` is true (intraday/free-text
values like "tonight" stay advisory text, `human_blocked` false).
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
# A dashboard agent-task lane heading: `### [[Workstream]]`. Only wiki-link
# headings scope a harvest; `### Sign the Operating Agreement…` (Manual steps)
# deliberately doesn't, so prose lanes never feed the two-way sync.
WIKILINK_HEADING = re.compile(r"^#{1,6}\s+\[\[([^\]]+)\]\]\s*$")
DASHBOARD_NAME = "Launch Dashboard.md"


def _opt(raw: str) -> str | None:
    """A frontmatter scalar, or None for an absent/null/empty value."""
    return None if raw in ("null", "", "~") else raw.strip('"')


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


def phase_for(
    body: str, phases: list[str]
) -> tuple[str, int, int, list[str]]:
    """Count - [ ]/- [x] items and infer the current phase from which
    phase-named heading sections still contain an open item. Also returns
    the open item texts in the computed phase's section (the live work
    front the dashboard mirrors)."""
    current_section: str | None = None
    open_by_section: dict[str, int] = {}
    open_text_by_section: dict[str, list[str]] = {}
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
                text = CHECK_OPEN.sub("", line, count=1).strip()
                open_text_by_section.setdefault(current_section, []).append(text)
        elif CHECK_DONE.match(line):
            done += 1
    total = done + open_count

    if total == 0:
        return phases[0], 0, 0, []
    for ph in phases:
        if open_by_section.get(ph, 0) > 0:
            return ph, done, total, open_text_by_section.get(ph, [])
    return phases[-1], done, total, []


def _note_index(vault: Path) -> dict[str, Path]:
    """Map workstream name → note path (frontmatter `workstream`, else stem).
    Used to route a ticked dashboard item back to its owning note."""
    idx: dict[str, Path] = {}
    for md in sorted(vault.glob("*.md")):
        if md.name == DASHBOARD_NAME:
            continue
        try:
            fields, block, _ = split_frontmatter(md.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not block:
            continue
        name = fields.get("workstream", md.stem).strip().strip('"')
        idx.setdefault(name, md)
        idx.setdefault(md.stem, md)
    return idx


def harvest_dashboard(vault: Path) -> tuple[list[dict], list[dict]]:
    """Two-way checkbox sync, run *before* counting.

    Parse the existing `Launch Dashboard.md`, and for every `- [x]` the user
    ticked under a `### [[Workstream]]` lane, flip its twin `- [ ]` to `- [x]`
    in that workstream's note. Matching is exact stripped-text equality scoped
    to the owning note — the board renders this script's own `phase_open_items`
    text, so the round-trip is identical by construction.

    Returns (harvested, unmatched). A tick whose text is already `- [x]` in
    the note is a satisfied no-op (not unmatched). A tick with no matching
    line, or for an unknown workstream, is unmatched and reported so the model
    can surface it — never silently dropped.
    """
    dash = vault / DASHBOARD_NAME
    if not dash.is_file():
        return [], []
    try:
        dash_text = dash.read_text(encoding="utf-8")
    except OSError:
        return [], []

    # workstream -> ordered unique ticked item texts
    ticked: dict[str, list[str]] = {}
    current: str | None = None
    for line in dash_text.splitlines():
        wl = WIKILINK_HEADING.match(line)
        if wl:
            current = wl.group(1).strip()
            continue
        if HEADING.match(line):  # any non-wiki heading ends the lane scope
            current = None
            continue
        if current and CHECK_DONE.match(line):
            text = CHECK_DONE.sub("", line, count=1).strip()
            bucket = ticked.setdefault(current, [])
            if text not in bucket:
                bucket.append(text)

    if not ticked:
        return [], []

    notes = _note_index(vault)
    harvested: list[dict] = []
    unmatched: list[dict] = []

    for workstream, items in ticked.items():
        note = notes.get(workstream)
        if note is None:
            unmatched.extend(
                {"workstream": workstream, "item": it, "reason": "no note for workstream"}
                for it in items
            )
            continue
        text = note.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        changed = False
        for it in items:
            done_already = False
            flipped = False
            for i, ln in enumerate(lines):
                if CHECK_OPEN.match(ln) and CHECK_OPEN.sub("", ln, count=1).strip() == it:
                    lines[i] = ln.replace("[ ]", "[x]", 1)
                    flipped = changed = True
                    break
                if CHECK_DONE.match(ln) and CHECK_DONE.sub("", ln, count=1).strip() == it:
                    done_already = True
                    break
            if flipped:
                harvested.append({"workstream": workstream, "item": it, "file": note.name})
            elif not done_already:
                unmatched.append(
                    {"workstream": workstream, "item": it, "file": note.name,
                     "reason": "no matching open item in note"}
                )
        if changed:
            note.write_text("".join(lines), encoding="utf-8")

    return harvested, unmatched


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
    # Two-way checkbox sync runs first: ticks the user made on the dashboard
    # are flipped into the notes before anything is counted, so the count
    # below already reflects them.
    harvested, harvest_unmatched = harvest_dashboard(vault)
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
        phase, done, total, phase_open_items = phase_for(body, phases)
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

        actor = fields.get("next_actor", "agent").strip('"').strip().lower()
        if actor not in ("agent", "human"):
            actor = "agent"
        actor_disp = "🧑" if actor == "human" else "🤖"

        hbu_raw = fields.get("human_blocked_until", "null")
        hbu = None if hbu_raw in ("null", "", "~") else hbu_raw.strip('"')
        human_blocked = False
        if hbu:
            try:
                human_blocked = _dt.date.fromisoformat(hbu) > _dt.date.today()
            except ValueError:
                human_blocked = False  # intraday/free-text: advisory only

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
                "next_actor": actor,
                "human_blocked_until": hbu,
                "human_blocked": human_blocked,
                "phase_open_items": phase_open_items,
                "repo_path": _opt(fields.get("repo_path", "null")),
                "repo": _opt(fields.get("repo", "null")),
                "_blocked_disp": blocked_disp,
                "_actor_disp": actor_disp,
            }
        )

    header = (
        "| Workstream | Phase | % | Actor | Blocked by |\n"
        "|---|---|---|---|---|"
    )
    lines = [
        f"| [[{r['workstream']}]] | {r['phase']} | {r['percent_to_release']}% | "
        f"{r['_actor_disp']} | {r['_blocked_disp']} |"
        for r in rows
    ]
    board = "\n".join([header, *lines])
    for r in rows:
        r.pop("_blocked_disp", None)
        r.pop("_actor_disp", None)
    print(
        json.dumps(
            {
                "workstreams": rows,
                "board_markdown": board,
                "harvested": harvested,
                "harvest_unmatched": harvest_unmatched,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
