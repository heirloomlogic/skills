# Vault Templates

Exact markdown for the vault files. Read this when scaffolding a vault or
regenerating the dashboard. The dashboard is computed output; the per-workstream
notes are human-edited (you only touch frontmatter + checkbox state). Wording in
the note template is generic — adapt it to the user's stack.

---

## `Launch Dashboard.md` (computed — regenerate every invocation)

````markdown
---
vault_path: /absolute/path/to/this/vault
updated: 2026-05-16
---

> [!warning] launch-conductor regenerates this file every run. You **may** tick
> the checkboxes below — they sync back into the per-workstream notes on the
> next run. Don't edit item *text* here or rewrite the prose lanes; only the
> notes' wording survives, and the tick-sync matches on exact text.

# 🛬 Launch Board

| Workstream | Phase | % | Actor | Blocked by |
| --- | --- | --- | --- | --- |
| [[Adagio]] | wiring | 41% | 🤖 | — |
| [[Edict]] | wiring | 38% | 🤖 | — |
| [[Fallow]] | wiring | 22% | 🤖 | — |
| [[Heirloom Logic LLC]] | wiring | 27% | 🧑 | — |
| [[Website]] | building | 31% | 🤖 | — |

# 🤖 Agent tasks

These don't wait on each other — each runs in its own worktree. No idle
worktree while an agent line is unfed. None is gated by the LLC signatures
(that gate is on TestFlight/App Review, not on wiring), so all should run now.
Each lane is the **next 3** open items; the full checklist is in the note.

### [[Adagio]]
- [ ] Separate prod/debug config selected by build configuration
- [ ] Analytics initialized in release builds; launch funnel instrumented
- [ ] Remote killswitch / forced-update path verified

### [[Edict]]
- [ ] Purchase + restore wired and verified on device (sandbox)
- [ ] Every paid feature gated behind the entitlement check
- [ ] Production keys/endpoints separated from debug by build config

### [[Fallow]]
- [ ] Purchase + restore wired and verified on device (sandbox)
- [ ] Every paid feature gated behind the entitlement check
- [ ] Analytics initialized in release builds; launch funnel instrumented

### [[Website]]
- [ ] Site shell + Fallow teaser page
- [ ] Privacy policy + terms reachable at stable URLs
- [ ] Deployed to staging, reviewed mobile + desktop

# 👲 Manual steps

### Sign the Operating Agreement + Founder IP Assignment (Heirloom Logic LLC)

Not blocked — a ~1-day paperwork task you can do today. It's the true long
pole: no app reaches `testflight` or `app-review` until the Apple Developer Org
chain completes, and that chain is stalled here at signatures. It also fixes IP
ownership for all five apps. Signing now lets the business Apple ID + bank
steps proceed in parallel during the DUNS wait.

# 🧟‍♂️ Blocked for now

- **DUNS verification** (Heirloom Logic LLC) — pending D&B virtual inspection,
  external clock. Monitor, no action.

---

_Re-derived 2026-05-16. Synced 2 items you ticked on the board. Percentages
and phases computed from checkboxes by `reconcile.py`._
````

Assembly:

- **Table** = `board_markdown` verbatim. It carries the Actor column
  (🤖 = `next_actor: agent`, 🧑 = `human`); `%`/Phase show whatever
  `reconcile.py` computed. No Next-action column — the detail moved into the
  Agent tasks lane.
- **`# 🤖 Agent tasks`** — model-authored intro sentence(s) stating they
  parallelize plus any cross-workstream gating, then one `### [[Workstream]]`
  per non-blocked `next_actor: agent` row, with the **first 3** of that row's
  `phase_open_items` as `- [ ]` checkboxes, text verbatim (never reword — the
  harvest matches on exact text; never more than three — the note holds the
  rest). Two-way: `reconcile.py` harvests ticks here back into the notes before
  it counts. A fill, not a ranked pick.
- **`# 👲 Manual steps`** — one `### <step>` per `next_actor: human`
  workstream the user can act on now (not `human_blocked`, no `blocked_by`),
  each with reasoning prose. No single star; list them all.
- **`# 🧟‍♂️ Blocked for now`** — external-clock items only: any `blocked_by`,
  `app-review`/Apple waits, and `human_blocked: true` items. One line each,
  "monitor, no action".
- **Footer** — `_Re-derived <date>. <what changed: "Synced N items you ticked
  on the board" from `harvested`, or "Nothing checked since last run —
  percentages unchanged">. Percentages and phases computed from checkboxes by
  `reconcile.py`._` If `harvest_unmatched` is non-empty, name those items in
  chat (not the footer) so the user can re-tick them in the note.
- Omit any empty lane.

**Single-app vault collapses** to the table plus a single `# ▶ Do this next`
block (closeness heuristic, one call) — no Agent tasks / Manual steps / Blocked
lanes when there is only one workstream and nothing to parallelize.

---

## Per-app note — e.g. `App One.md`

````markdown
---
workstream: App One
phase: wiring
percent_to_release: 60
blocked_by: null
next_action: "Wire and entitlement-gate the paywall"
next_actor: agent
human_blocked_until: null
repo_path: null      # optional: local path to this app's repo
repo: null           # optional: GitHub owner/repo slug
updated: 2026-05-16
---

# App One

Bundle ID: `com.example.appone` · Platforms: iOS, macOS
One-liner: <what this app is>

## Notes

Free-text scratch space for the human. The conductor does not rewrite this.

## Launch checklist

> Decomposed from `launch-conductor/references/launch-checklist.md`. Sections
> map to phases; a phase is done when its section is fully checked. Wording is
> generic — adapt it to this app's actual stack; delete items it doesn't need.

### wiring
- [ ] Purchase + restore wired and tested on device (sandbox)
  - Real sandbox purchase unlocks entitlement; restore works on fresh install.
- [ ] Every paid feature gated behind the entitlement check
  - Nothing paid is reachable for free, verified walking the app un-entitled.
- [ ] Analytics initialized in release builds; launch funnel instrumented
  - First-run/activation/paywall/purchase events appear in the provider live view.
- [ ] Remote killswitch / forced-update path verified
  - A test config triggers the block UI; offline fallback degrades sanely.
- [ ] Production keys/endpoints separated from debug by build config
  - Release uses prod; no secret in plaintext in the built binary.
- [ ] Lint/format clean; Release archive builds clean

### internal-testing
- [ ] Runs clean on a physical device
- [ ] Core flows dogfooded end to end
- [ ] Icon / launch screen / version + build number set
- [ ] Privacy usage strings + privacy manifest complete

### testflight
- [ ] App Store Connect record created; signing resolves
- [ ] Build uploaded and processed; export compliance answered
- [ ] External testers have the build

### app-review
- [ ] Store listing + screenshots complete
- [ ] App privacy nutrition label answered
- [ ] Submitted for review

### released
- [ ] Released to the App Store
- [ ] Production smoke test from public build

## Post-launch parking lot

Scope deferred to keep the launch moving. Not lost, not now.

- (e.g. settings screen polish — parked 2026-05-16)
````

Pull the full item set and acceptance criteria from
`references/launch-checklist.md`; the block above is the shape, not the
complete list. Adapt wording to the app's real stack and delete inapplicable
items so the percentage stays honest.

---

## Optional non-app workstream — e.g. `Marketing Site.md`

Create this **only if the user has a non-app workstream that gates or
accompanies the launch** (a marketing/teaser site, a press kit). Don't scaffold
it by default. One sub-item per launching app so the count tracks real progress.

````markdown
---
workstream: Marketing Site
phase: building
percent_to_release: 30
blocked_by: null
next_action: "Build the App One page"
next_actor: agent
human_blocked_until: null
updated: 2026-05-16
---

# Marketing Site

Domain: <domain> · Stack: <static host / framework>

## Launch checklist

### building
- [ ] Site shell + content
- [ ] App One page
- [ ] Privacy policy + terms live
  - App Store Connect needs the privacy-policy URL — this can block an app's app-review.

### staging
- [ ] Deployed to staging, reviewed mobile + desktop
- [ ] Links / capture / analytics verified

### live
- [ ] Live on production domain (DNS/TLS)
- [ ] App One page → real App Store link
````

---

## Reconciliation rules

`scripts/reconcile.py` implements all of the counting. The rules below are what
it does — they're documented so you can trust its output, not so you can redo
it by hand. **Run the script every invocation, _before_ you regenerate
`Launch Dashboard.md`; never hand-count.** The run order matters: the harvest
in step 1 reads the *existing* dashboard, so if you overwrite it first the
user's board ticks are gone before the script can sync them.

```
python3 <skill>/scripts/reconcile.py <vault>
```

What it does, and why each rule holds:

0. **Harvests** the existing `Launch Dashboard.md` first: for every `- [x]`
   under a `### [[Workstream]]` lane, it flips the twin `- [ ]` in that
   workstream's note (exact stripped-text match, scoped to that note). A tick
   whose text is already `- [x]` in the note is a satisfied no-op. A tick with
   no matching open item (text edited on the board, unknown workstream) is left
   alone and reported in `harvest_unmatched` — never silently dropped. Only
   wiki-link headings scope a lane, so Manual-steps prose headings never feed
   the sync.
1. **Reads** every `*.md` in the vault except `Launch Dashboard.md`. A file
   with no `---` frontmatter block is skipped (not a workstream note).
2. **Counts** `- [x]` (done) vs `- [ ]` (open) lines only. Indented sub-bullet
   acceptance criteria are *not* `- [ ]` lines, so they don't count as units —
   that's intentional, the criterion describes the item, it isn't its own task.
3. **`percent_to_release = round(100 * done / total)`**; zero items → `0`.
4. **`phase`** = the earliest phase-named section (`### wiring` …) that still
   has an open item. All checked → last phase (`released` / `live`). Website
   notes use the `building`/`staging`/`live` ladder automatically. The open
   `- [ ]` texts in that computed phase section become `phase_open_items` (the
   live work front the Agent tasks lane mirrors; later phases excluded).
5. **Rewrites** `percent_to_release`, `phase`, `updated` in each note's
   frontmatter in place. Carries `blocked_by`, `next_action`, `next_actor`,
   `human_blocked_until`, `repo_path`, `repo`, `workstream` forward untouched —
   those are authored, not computed. (`next_actor` defaults to `agent` when
   absent; `human_blocked_until`, `repo_path`, `repo` to `null`.)
6. **Prints** JSON to stdout: `workstreams` (per-note rows including
   `next_actor`, `human_blocked_until`, the derived `human_blocked` boolean —
   true when `human_blocked_until` is a future ISO date — `phase_open_items`,
   and `repo_path`/`repo` for the code-grounded audit), `board_markdown` (the
   table: `Workstream | Phase | % | Actor | Blocked by`, Actor 🤖 agent / 🧑
   human, **no Next-action column**), `harvested` (board ticks flipped into
   notes this run — drive the footer's "Synced N" from this), and
   `harvest_unmatched` (ticks with no twin — surface each in chat). Use them
   verbatim.

Before running it, apply any conversational "X is done" by checking that box in
the note body — then the script picks it up. A checkbox the user ticked
**anywhere** — the note in Obsidian or the dashboard lane — always wins,
because the harvest folds board ticks into the notes and every computed field
is then derived from the boxes; there is no competing stored state. The script
never lowers a percentage or reverts a phase unless the boxes actually changed.

You still own the prose: after dropping in the `board_markdown` table, build
the `# 🤖 Agent tasks` (mirror each non-blocked agent row's `phase_open_items`
plus an intro sentence), `# 👲 Manual steps` (each actionable human step with
reasoning), and `# 🧟‍♂️ Blocked for now` (external-clock items) lanes per the
prioritization rules in `SKILL.md`. For a single-app vault this collapses to
one `# ▶ Do this next`. The script gives you true numbers, the actor split,
and the work front; the routing and prose are your judgment.
