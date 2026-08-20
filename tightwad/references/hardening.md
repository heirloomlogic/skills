# Currency and hardening

Rules 1–6 make CI cheaper. Rules 7 and 8 make it safe. **Rule 9 is the only rule
that spends money** — it buys rule 7 a future, because a pinned SHA nobody
maintains is a snapshot of a decision somebody stopped making.

All three parts are **on by default**, for the same practical reason: you already
have the file open. Applying them later means opening every workflow a second
time.

Keep the kinds of claim apart when you report. **Cost is measured; hardening is
categorical.** Do not blend them into one number. Rule 9's recurring cost is
measured, so it goes in the minutes table with the rest of the money.

---

# Part 1 — Actions must be current *and* pinned

A pinned SHA answers "did this change under me". It does not answer "is this still
maintained". Both matter, and only one of them is in the usual advice.

## Why stale is a security problem, not just an old number

A JavaScript action declares its Node runtime in `action.yml`. Measured on
2026-08-19:

- `actions/checkout@v4.3.1` → `using: node20`
- `actions/checkout@v7.0.1` → `using: node24`

**Node 20 reached end of life on 2026-04-30.** An action on it gets no runtime
security patches, and GitHub eventually deprecates and then breaks EOL runtimes —
which arrives as a red build with no diff to explain it. This is the same story
that killed `node12` and `node16` before it.

Stale also means the action's own fixes are missing. `actions/checkout` v4 → v7 is
three majors of changes you do not have.

## Finding the truth

Latest stable release:

```
gh api repos/actions/checkout/releases/latest --jq '.tag_name'
```

The SHA for that exact tag — **never the major tag**, which moves:

```
gh api repos/actions/checkout/git/refs/tags/v7.0.1 --jq '.object.sha'
```

The runtime that tag actually ships:

```
gh api "repos/actions/checkout/contents/action.yml?ref=v7.0.1" --jq '.content' | base64 -d | grep "using:"
```

`node16` or `node20` → stale, and say so as a runtime finding rather than a version
finding. `node24` → current. `docker` or `composite` → no runtime concern; judge it
on maintenance alone.

## Measure the repo's own drift

Do this once, at the start of Phase 3, and let the output drive the currency pass.
It reaches into local composite actions too, which is where a stale
`actions/setup-node` most often hides:

```bash
grep -rhoE '^\s*-?\s*uses:\s*\S+' .github/workflows .github/actions 2>/dev/null \
  | sed -E 's/.*uses:[[:space:]]*//' \
  | grep -v '^\./' \
  | sort -u \
  | while IFS= read -r ref; do
      action="${ref%@*}"
      latest=$(gh api "repos/$action/releases/latest" --jq '.tag_name' 2>/dev/null || echo '?')
      printf '%-60s %s\n' "$ref" "$latest"
    done
```

Read the output for three things, worst first:

1. **A floating major tag that is also several majors behind** — `checkout@v4`
   when latest is v7.0.1. It gives neither reproducibility nor currency, and it is
   the worst cell there is.
2. **A floating tag** — `@v4`, `@v2`, `@main`. Reproducibility is missing.
3. **A pinned SHA several majors behind.** Reproducible, unmaintained.

Also check whether two workflows in the same repo pin different versions of the
same action. Converge them on the latest; a repo that disagrees with itself is a
repo where nobody is watching.

## A major bump is a behaviour change

Do **not** bump blind. `checkout@v4 → v7` crosses three majors, and majors exist
because something broke.

Read the release notes for every major you skip. If one describes a change that
touches how this repo uses the action — a changed default, a removed input, a new
required permission — that is a **conflict**, and it goes to the user through the
same machinery as a load-bearing comment (`exceptions.md`): quote the note, name
the risk, ask.

A version bump that turns a green build red is a worse outcome than a stale
action, and it is the failure this rule is most likely to cause.

---

# Part 2 — The hardening baseline

Applied to every workflow, every run, unless something below says ask.

## 1. A `permissions:` block on every workflow

```yaml
permissions:
  contents: read
```

At workflow level, with any job needing more declaring it at job level — a docs
deploy needing `pages: write` and `id-token: write`, a release needing
`contents: write`.

**Be honest about the severity.** Check the repo-level default first:

```
gh api repos/<owner>/<repo>/actions/permissions/workflow --jq '.default_workflow_permissions'
```

If that already reads `read`, a missing `permissions:` block is defence in depth
and a durable statement of intent, not a live hole — say so in the PR. The value
is that the workflow file keeps being right if the repo-level default is ever
loosened, and that a reader can see what a job is allowed to do without leaving
the file. If it reads `write`, the finding is real and you can say that instead.

**Do not write `permissions: {}`.** A job that quietly needs `id-token` or
`packages` fails in a way that is genuinely hard to read.

## 2. `persist-credentials: false` on every checkout that does not push

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  with:
    persist-credentials: false
```

The default is **`true`, still, in v7.0.1** — verified in `action.yml`, not
assumed. So by default the `GITHUB_TOKEN` is written into `.git/config` and stays
readable by every later step in that job.

That is live rather than theoretical wherever a job runs third-party code after
the checkout: SwiftPM build-tool plugins, `npm ci` postinstall scripts, a Gradle
init script, a `pip install` from a lockfile. If any of those run in the job, the
token is inside their blast radius.

The exception is a step that genuinely pushes — a release, a docs deploy, a
changelog commit. Leave credentials on those and write a comment saying why, which
makes the line load-bearing for the next run of this skill.

## 3. Never `pull_request_target` plus a checkout of the PR head

That pairing hands fork-authored code the repo's secrets. It is the single worst
thing a workflow can do.

**This is a stop-and-ask, not an auto-fix.** Report it, explain the exposure, and
let the user decide the shape of the replacement. Do not quietly rewrite the
trigger — you may be removing the only thing that makes a needed workflow function.

## 4. No untrusted input interpolated into `run:`

```yaml
# Script injection: the title is attacker-controlled.
- run: echo "${{ github.event.pull_request.title }}"

# Correct: through the environment, where it is data rather than shell.
- run: echo "$TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

Anything from `github.event` — titles, bodies, branch names, author fields — is
attacker-controlled on a public repo and untrusted on a private one. The same
applies to anything derived from them, including a script or artifact name built
from a branch: pass it through `env:`, never onto the command line.

## 5. Secrets scoped to the job that needs them

Never a workflow-level `env:` block holding a secret. Pass it into the one job, or
the one step, that reads it.

## 6. Third-party actions pinned to a SHA, always

First-party `actions/*` too, but third-party is where the risk concentrates,
because a compromised tag there reaches your secrets with nobody watching the
repo. List them explicitly in the PR — an action outside `actions/` and outside
`github/` is one a reviewer should be told about by name.

## What is deliberately *not* in the baseline

- **Egress filtering** (`step-security/harden-runner` and similar). A real tool,
  but adding it puts a new third-party action into every workflow — which is a
  supply-chain decision the user should make deliberately, not a default this
  skill applies overnight. Mention it once in the PR if the repo handles deploy
  secrets; do not add it.
- **Required status checks, branch protection, CODEOWNERS.** Repo settings rather
  than workflow content. Out of scope; say so if they are obviously missing.
- **Dependabot's security-alert and code-scanning features.** Vulnerability
  scanning of the repo's application code is a different job. Rule 9 configures
  Dependabot's *version updates* only, because those are what keep rule 7's pins
  alive and those are what cost billed minutes.

---

# Part 3 — Keeping them current without you

Rule 7 pins every action to an exact SHA. That is a snapshot, and snapshots rot.
Nobody hand-bumps a 40-character hash, so without a bot the currency pass you just
did is the last one this repo ever gets — and rule 7's own argument, that a pinned
SHA on an end-of-life runtime is a reproducible way to run unpatched code, becomes
a description of what you just built.

**The skill creates the debt, so the skill ships the payer.** Every write-mode run
writes or amends `.github/dependabot.yml`.

## The default config

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    # "/" is the only value this ecosystem accepts. It already covers
    # .github/workflows, reusable workflows, and composite actions under
    # .github/actions — a local composite needs no second entry.
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    # One PR per batch, not one per action. At 150 billed minutes a run,
    # ungrouped bumps are the most expensive way to stay current.
    groups:
      actions:
        patterns: ["*"]
    open-pull-requests-limit: 3
    commit-message:
      prefix: "ci"
```

Replace the figure in that comment with the repo's own measured per-run cost from
Phase 2. A comment carrying a real number is load-bearing for the next run of this
skill; a comment carrying this page's number is furniture.

## Price the interval, do not pick it by taste

Every Dependabot pull request triggers CI, so the updater has a monthly bill. Reuse
the Phase 2 measured figure:

```
dependabot_minutes_per_month = PRs_per_month × billed_minutes_per_PR_run
```

Default to `weekly`, which is roughly four PRs a month. **If that exceeds 10% of
the account's monthly quota, step down to `monthly`** and write the reason into the
file.

Worked, on the macOS-locked private repo from `cost-model.md`: 150 billed minutes a
run × 4 = 600 minutes a month against a 2,000-minute quota, which is 30% of
everything the account has. Monthly instead is 150 minutes, or 7.5%. That repo gets
`monthly`.

`interval` also accepts `daily`, `quarterly`, `semiannually`, `yearly` and a `cron`
expression. **`daily` is nearly always the wrong answer** on a private repo, and
finding it in an existing config is a finding worth pricing.

**Public repos get `weekly` always.** Actions are free, so the interval is a
latency choice rather than a money one.

## The pin comment must end with the version

Dependabot updates the SHA *and* the trailing version comment — but only when the
version is the last thing in that comment. Anything after it and Dependabot leaves
the line alone, because it cannot tell a version tag from prose.

```yaml
# Correct — Dependabot maintains both halves of this line.
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

# Broken — the SHA still gets bumped, the comment silently does not, and the
# file starts lying about which version it runs.
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1, pinned for the fetch-depth fix
```

This collides with the "a comment is a reason" rule, and the resolution is
positional: **the reason goes on its own line above the `uses:`, the version ends
the trailing comment.** `exceptions.md` carries the same instruction where that
rule lives.

## Offer the repo's own ecosystem, never assume it

The `github-actions` entry is not negotiable — rule 7 created that debt. The repo's
own package ecosystem (`npm`, `swift`, `cargo`, `pip`, `bundler`) is a separate
question, because those pull requests run the full test suite rather than a
workflow re-parse, and they are where the real minutes are.

Put it to the user with `AskUserQuestion`, priced, exactly like a load-bearing
comment:

> `Package.swift` declares 6 dependencies. A grouped weekly SwiftPM updater would
> open roughly 2 PRs a month at **150 billed minutes each** — 300 minutes a month
> against a 2,000-minute quota.
> Add it weekly / add it monthly / actions only?

One question, one ecosystem. Do not batch several ecosystems into one price.

## Two things to mention and not do

- **Auto-merge.** Grouped patch bumps merging themselves after green CI is the
  thing that actually keeps pins current without human toil. It also means a
  compromised upstream release merges itself. Same precedent as
  `step-security/harden-runner` above: name it once in the PR, let the user decide,
  do not enable it.
- **`cooldown:`.** Its `default-days` sub-key delays adoption of a brand-new
  release, which blunts the window where a compromised version is published and
  later yanked. Real hedge, real latency. Offer it in the PR body — but **do not
  write it into the file commented out**, because `exceptions.md` classes
  commented-out configuration as cruft and the next run of this skill will delete
  it.

## An existing dependabot.yml is amended, never rewritten

It is a config file with comments, so the `exceptions.md` preserve rule governs it
in full. An `ignore:` entry or a `groups:` block carrying an explanation is
load-bearing and survives verbatim.

- **No file** → write the default above. This is an addition; no need to ask.
- **File exists, no `github-actions` entry** → add that one entry. Leave every
  other entry alone, including its schedule.
- **File exists with a `github-actions` entry** → change only what is priced.
  `daily` → `weekly` or `monthly`, and add a `groups:` block if there is none. An
  uncommented `open-pull-requests-limit` is fair game; a commented one is not.

## In audit mode

Report, price, write nothing. The four findings:

1. No `.github/dependabot.yml` — rule 7's pins have no maintainer.
2. A file with no `github-actions` entry.
3. `interval: daily` on a private repo.
4. No `groups:` block, so N action bumps open N pull requests.

Each one gets its cost or its saving in billed minutes a month, from the measured
per-run figure.

---

# Reporting all three parts

Currency and hardening get **a separate section of the PR body, under their own
heading, never mixed into the minutes table.** Two lines per finding: what was
open, what it is now.

Where a bump crosses a major, say which majors were crossed and that the release
notes were read. A reviewer needs to know the difference between "bumped a patch"
and "crossed three majors and believed the changelog."

**Rule 9 splits across both.** Its recurring cost is a measured number, so it goes
in the minutes table as a line item — an addition, not a saving. Its *choices* go
under the hardening heading: the interval and the arithmetic behind it, the
grouping, which ecosystems the user accepted, and that auto-merge and `cooldown:`
were named and left off.
