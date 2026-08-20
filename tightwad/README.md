# Tightwad

A skill that argues with your GitHub Actions config in billed minutes.

Run `/tightwad` inside one repo. It measures what that repo's CI actually costs
from real job durations, tightens it, brings every action current and pinned,
hardens permissions and credentials, and opens a pull request that leads with the
number.

## Why it exists

A private, macOS-only Swift package burned roughly **26,000 billed minutes in one
month** against an account-wide quota of 2,000–3,000 — and took an unrelated
repo's CI down with it, even though that repo's own workflows were already correct
and cheap. Nothing noticed, because nothing measured.

## The measurement is the point

Every recommendation is denominated in billed minutes read from real job
durations, never estimated. From that package's last successful run:

| Job | Duration | Billed |
|---|---|---|
| `swift-format lint (strict)` | 34s | 1 |
| `Build & Test (TZ=Asia/Tokyo)` | 6m43s | 7 |
| `Build & Test (TZ=UTC)` | 6m48s | 7 |

GitHub rounds each job up to the whole minute **individually**, so that is 15
minutes; the macOS 10x multiplier makes it 150. The workflow triggered on both
`pull_request` and `push: [main]`, so a merged PR ran it twice: **300 billed
minutes per merged PR.** Thirteen merged PRs exhaust a month. It merged 87.

## The nine rules

1. One trigger per commit
2. Cancel superseded runs (`concurrency` + `cancel-in-progress`)
3. One job per PR
4. The cheapest runner the work actually needs
5. A `timeout-minutes` on every job
6. Cache downloads, not build products
7. Actions current *and* pinned to a SHA
8. Harden by default — `permissions:`, `persist-credentials: false`, no untrusted
   input in `run:`
9. Keep them current without you — a priced, grouped Dependabot config

Two are worth pulling out.

**Rule 5.** GitHub's default job timeout is **six hours**. One hung macOS job
bills 3,600 minutes — more than an entire monthly quota, from one stuck test.

**Rule 4, applied to lint.** `swift-format` ships in the Swift Linux toolchain and
lints by *parsing source*, so it does not need Darwin. A lint job on `macos-26` in
a private repo is paying 10x to read text. This is the best win available in a
repo that cannot otherwise leave macOS.

## Preserving the exceptions

The skeleton is confident and often wrong about one line in a file.
[`references/exceptions.md`](references/exceptions.md) is the counterweight: **a
workflow line carrying an explanatory comment is load-bearing until proven
otherwise**, and survives the rewrite verbatim.

A 40-line comment characterising a SwiftPM prebuilt-linking bug, naming the exact
symbol the build dies on. A two-timezone test matrix whose divergence is the
detector that caught a date-line bug. Both look like noise to a template. Both are
the most valuable lines in their file. Where the skeleton disagrees with a
comment, the skill **asks** — quoting the reason and pricing the choice in billed
minutes — rather than deleting.

## Rule 7 creates the debt, so rule 9 pays it

Rule 7 pins every action to an exact 40-character SHA. Nobody bumps those by hand,
so without a bot the currency pass is the last one the repo ever gets — and rule
7's own argument, that a pinned SHA on an end-of-life runtime is a reproducible way
to run unpatched code, becomes a description of what the skill just built.

So every run writes `.github/dependabot.yml`. **It is the only rule that spends
money rather than saving it**, which is exactly why this skill should be the one to
configure it: every Dependabot pull request triggers CI, and a daily ungrouped
updater on a macOS repo can outspend everything rules 1–6 saved. The interval is
priced against the measured per-run cost — weekly by default, monthly when four
PRs a month would exceed 10% of the account quota — and the updates are grouped so
N action bumps open one pull request instead of N.

The repo's own ecosystem (`npm`, `swift`, `cargo`) is offered as a separate priced
question, never added silently. Auto-merge and `cooldown:` get named in the PR and
left off, the same call the skill already makes about `harden-runner`.

## Two rules that keep it honest rather than merely cheap

- **Never touch `main` directly.** CI cannot be verified locally; the run on its
  own PR is the only proof.
- **Report what moved later, in the same breath as the saving.** A check that went
  from PR-time to nightly means that regression now surfaces after the merge. That
  is a trade, not a free win, and a PR reporting only the minutes saved is lying
  by omission.

## Public repos short-circuit the money

Visibility is checked first. Public repos have free unlimited Actions, so the
skill says so and tunes only for speed. Rules 7 and 8 run regardless — a public
repo's workflows are readable by everyone looking for a way in, and its
`github.event` input is genuinely attacker-controlled.

## Modes

- `/tightwad` — measure, rewrite, open a PR.
- `/tightwad audit` — measure and report. Changes nothing.

## Files

- [`SKILL.md`](SKILL.md) — the flow, the nine rules, the two modes, the PR format
- [`references/cost-model.md`](references/cost-model.md) — multipliers, the
  account-wide quota, how to pull real durations, the formula, the public-repo
  short-circuit
- [`references/archetypes.md`](references/archetypes.md) — four repo shapes with
  complete workflow skeletons, the `dependabot.yml` every shape gets, and the test
  for whether a package is really locked to macOS
- [`references/exceptions.md`](references/exceptions.md) — load-bearing vs cruft,
  and how to put a conflict to the user
- [`references/hardening.md`](references/hardening.md) — rules 7, 8 and 9 in full,
  including a one-liner that measures a repo's action drift and how to price the
  Dependabot interval

## Installation

```bash
gh skill install heirloomlogic/skills tightwad --agent claude-code --force --scope user --upstream
```

Or copy the directory into your agent's skills directory:

```bash
cp -r tightwad/ ~/.claude/skills/tightwad/
```

## Known limits

- **Pinned versions in the skeletons go stale.** The action SHAs and the Swift
  container tag in `references/archetypes.md` were current on 2026-08-19. The
  skill tells you to re-resolve them before use; nothing enforces it.
- **Not yet proven by a measured before/after.** The cost model and the rules are
  derived from real runs, but the skill has not published a completed
  before/after on a repo it tightened itself.
- **A bit-identical test corpus is out of scope for the runner change.** Moving a
  package between Darwin and swift-corelibs Foundation can move dates, formatting
  and floating-point results. The skill requires a corpus diff before proposing
  that move, and will not do the diff for you.
- **Rule 9 inherits Dependabot's own bugs.** A SHA pin can be bumped to an
  untagged branch HEAD, which leaves the version comment stale and pointing at a
  release the SHA is not
  ([dependabot-core#13466](https://github.com/dependabot/dependabot-core/issues/13466),
  [#14716](https://github.com/dependabot/dependabot-core/issues/14716)). The next
  run of this skill catches it; nothing catches it in between.

## Version history

- **1.1.0** — Dependabot brought in scope as rule 9. Previously the skill
  contradicted itself and adopted it or declined it at random.
- **1.0.0** — Initial public release.
