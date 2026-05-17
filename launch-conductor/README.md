# Launch Conductor

A product-manager skill for the **last 10%**: taking an iOS/macOS app whose
own functionality is already built the rest of the way to public App Store
release — without drifting back into the part you've already finished.

## What it is

You built the app. The fun 80–90% — the features you cared about — is done.
What's left is the launch tail: paywall/IAP, killswitch, feature flags,
analytics, release vs. debug config, TestFlight, App Store Connect. It's
finite and unglamorous, none of it ships itself, and it's exactly where
developers stall — polishing the built thing instead of closing the boring
gap to release.

This skill is the organizing principle. It keeps a plain-markdown **Obsidian
vault** as the single source of truth and, on every invocation, re-derives the
critical path and tells you the *one* thing to do next — before answering
whatever you asked. The board is unavoidable but cheap, so re-orientation
becomes a reflex instead of a chore you skip. Works for one app or several.

It does not build your app or care about your stack. It tracks *whether* the
launch-tail capabilities are done; it never tells you how to integrate a
specific SDK. Stack-agnostic — no dependency on any framework or vendor.

## How it works

- **Vault as source of truth.** A standalone Obsidian vault (separate from the
  app repos) holds a computed `Launch Dashboard.md` plus one note per
  workstream — one per app, plus any non-app workstream that gates the launch.
- **Frontmatter is canonical, checkboxes are the detail.** Each note carries
  `phase` / `percent_to_release` / `blocked_by` / `next_action`. You tick
  checkboxes in Obsidian; `scripts/reconcile.py` recomputes the frontmatter and
  regenerates the dashboard so the two never drift — the numbers are computed,
  never estimated.
- **One next action.** The board collapses the whole backlog to a single call,
  with the reasoning, using a closest-to-release-first heuristic.
- **Drift guards.** "I spent all day polishing the settings screen" gets a
  board and a redirect, not a thank-you.

## Scope

Drives each app through public App Store release. App Store Connect submission
steps are owned by this skill's own (generic) checklist; an
`apple-appstore-reviewer` skill, if present, is an optional deep-dive, not a
dependency. The launch-tail checklist names capabilities, not vendors — adapt
it to whatever stack the app uses.

## What it is NOT

Not for building the app's own features, writing implementation code, marketing
copy, or designing App Store screenshots. Not coupled to any particular
framework or third-party SDK. Not a Jira/issue-tracker integration — the vault
files are the system.

## Installation

```bash
gh skill install heirloomlogic/skills launch-conductor --agent claude-code --scope user
```

## The `ship` command (terminal launcher)

For a one-word way into the work: install the `ship` launcher. It opens Claude
in your vault with `--dangerously-skip-permissions`, auto-runs this skill to
reconcile the vault and print the board + the single next action, then hands
you an interactive session — so you go from terminal to "here's the one thing
to do" in one command.

Install it once, baking your vault as the default (use your real vault path in
place of `/path/to/vault`):

```bash
bash ~/.claude/skills/launch-conductor/scripts/install-launcher.sh /path/to/vault
```

This writes `~/.local/bin/ship` and saves the default vault to
`~/.config/launch-conductor/vault`. After that:

```bash
ship                 # open the default vault, refresh, start working
ship /path/to/vault  # use (and save as new default) a different vault
ship --help
```

`/path/to/vault` is the folder that holds `Launch Dashboard.md`. If
`~/.local/bin` isn't on your `PATH`, the installer prints the line to add.
Re-run the installer any time to repoint the default or refresh the script.

## Version history

- **1.1.0** — Added the `ship` terminal launcher and
  `scripts/install-launcher.sh`: one command opens Claude in the vault
  (`--dangerously-skip-permissions`), auto-runs the skill to reconcile and show
  the board, then drops to interactive. Default vault saved in
  `~/.config/launch-conductor/vault`.
- **1.0.0** — Initial release. The 90/10 launch-tail PM: Obsidian-vault source
  of truth (dashboard + per-workstream notes, frontmatter-canonical state with
  deterministic `scripts/reconcile.py` checkbox reconciliation), terse
  re-orientation board with a single next action, closest-to-release-first
  prioritization, drift guards, and a generic stack-agnostic launch checklist
  (paywall/IAP, killswitch, feature flags, analytics, release config,
  formatting/CI, TestFlight) with self-contained App Store Connect submission.
