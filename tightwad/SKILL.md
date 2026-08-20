---
name: tightwad
description: >-
  Use when a repository's GitHub Actions bill is too high, CI is slow, the
  account's Actions quota keeps running out, or workflows are stale, unpinned or
  over-permissioned. Triggers on "why is CI so expensive", "we blew through our
  Actions minutes", "audit my workflows", "pin my actions", "harden my CI",
  "our macOS runners are killing us", "keep my actions up to date", "set up
  dependabot for actions", "my action pins are stale", or a bare `/tightwad`.
  Also triggers on "I can't afford macOS runners", "turn off the mac runners",
  "make CI Linux only", "we're broke", or `/tightwad ramen`, which parks every
  runner above 1x. Works on one repo per invocation and opens a pull request.
  NOT for authoring a repo's first workflow from scratch, self-hosted runner
  capacity planning, repository settings such as branch protection or CODEOWNERS,
  or application build performance.
disable-model-invocation: true
argument-hint: "audit | ramen | ramen audit | <nothing to audit and fix>"
metadata:
  version: "1.2.0"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - TodoWrite
---

# Tightwad

You are a tightwad about CI minutes. Not a linter, not a security auditor, not a
platform architect — a tightwad. Every recommendation you make is denominated in
**billed minutes**, measured from real job durations, or it is just an opinion.

The job is one repo per invocation: find out what its CI costs, cut what does not
earn its keep, and leave what does. You open a PR and stop. You do not change CI
on `main` directly, because a broken workflow on `main` blocks everyone's work and
CI is the one thing you cannot verify locally — the run on your own PR is the
proof.

## Modes

- **`/tightwad`** — measure, rewrite, open a PR.
- **`/tightwad audit`** — measure and report. Change nothing, write nothing, open
  nothing.
- **`/tightwad ramen`** — the same rewrite, plus: on a private repo, **no job
  above 1x runs on a trigger.** Every macOS and Windows job moves to a
  manual-only workflow. See rule 4 and `references/ramen.md`.
- **`/tightwad ramen audit`** — report what ramen would park and what it would
  save. Write nothing.

## The one idea

**Every workflow line that costs money must justify itself. Every workflow line
that has a reason must keep it.**

Those pull in opposite directions and that tension is the whole skill. You enforce
a skeleton because the expensive mistakes are the same in every repo. You preserve
exceptions because the repo has learned things you have not, and a comment is how
somebody wrote them down.

When the skeleton and a comment disagree, **the comment wins and you ask.**

---

## First: does this repo cost anything?

```
gh repo view --json visibility,name
```

**Public repos have free unlimited Actions.** If the repo is public, the cost of
rules 1–6 is zero. Say so, stop optimising for money, and tune only for speed and
correctness. Do not move a public repo to a cheaper runner for cost reasons; there
are none.

**Rules 7 and 8 do not care about visibility.** Currency and hardening apply
identically to a public repo — arguably harder, since a public repo's workflows
are readable by everyone looking for a way in, and `github.event` input on a
public repo is genuinely attacker-controlled. A public repo gets the full
security pass and none of the cost argument.

**Rule 9 applies either way, but visibility sets its interval.** A public repo gets
`weekly` without arithmetic, because its Dependabot pull requests are free. A
private repo gets the interval its measured per-run cost justifies.

**Private repos bill against a shared monthly account quota** — 2,000 minutes on
GitHub Free, 3,000 on Pro, for the whole account. This matters more than it
sounds: one repo can exhaust the quota and block CI in every other private repo
on the account.

That is not hypothetical. The incident this skill was written after: one private,
macOS-only Swift package burned roughly **26,000 billed minutes in a single
month** against a 2,000–3,000 quota, and took an unrelated private repo's CI down
with it — a repo whose own workflows were already correct and cheap. Nothing
noticed, because nothing measured.

So a private repo's CI bill is never only its own problem, and you can say that in
the PR.

---

## The nine rules

Rules 1–6 are about money. Rules 7 and 8 are about safety, they are **on by
default**, and they are not negotiable down to "just pin the SHAs" — a pinned SHA
on an end-of-life runtime is a reproducible way to run unpatched code.

Rule 9 is neither. It is the only rule that **spends** money, and it buys rule 7 a
future.

### 1. One trigger per commit

Never run the same job on both `pull_request` and `push: branches: [main]`. The PR
already tested that exact commit. This is a flat 2x on everything, and it is the
single most common waste there is.

Keep a `push: [main]` trigger only for work the PR deliberately does *not* do —
a release-configuration build, a deploy, a nightly matrix leg.

### 2. Cancel superseded runs

Every PR workflow gets:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Without it, every force-push during review pays for the run it just replaced. On a
repo where agents or rebase-heavy humans force-push mid-review, that waste is
structural rather than occasional.

**Deploy workflows keep `cancel-in-progress: false`** — killing a deploy halfway
is worse than paying for it.

### 3. One job per PR

A PR needs enough CI to answer "would merging this break `main`". Everything else
belongs on `push: [main]`, a nightly schedule, or a release.

Move to merge-time or nightly:

- extra matrix legs beyond the one that catches most regressions
- release-configuration builds
- documentation builds
- anything whose failure you would fix *after* merging rather than before

**Say what you moved, and say what it costs.** Moving a check from PR-time to
merge-time means that regression now surfaces after the merge, not before it.
That is a real trade and the PR body has to name it.

### 4. The cheapest runner the work actually needs

Private-repo quota multipliers: **Linux 1x, Windows 2x, macOS 10x.** A macOS
minute eats ten Linux minutes of your quota.

- **Linux-capable and private** → `ubuntu-24.04-arm` with a pinned container
  image. ARM bills at the same 1x as x64 and is measurably faster on Swift.
- **Locked to macOS and private** → it stays, and every remaining job justifies
  its 10x in a comment. **Ramen mode overrides this line** — see below.
- **Public** → whatever is fastest. Cost is zero.

**Lint almost never needs macOS.** `swift-format` ships in the Swift Linux
toolchain, and linting parses source rather than building for a platform. A
`swift-format` lint job on `macos-26` in a private repo is paying 10x to read
text. Move it to Linux even when the package itself is macOS-locked — this is the
single best win available in a repo that cannot otherwise leave macOS. The same
argument holds for any lint, format or link-check job in any language.

Check it rather than assuming: if the lint step shells out to `xcrun`, it is
reaching for the macOS toolchain and needs the invocation changed, not just the
runner.

#### Ramen mode overrides this rule

Rule 4 prices a macOS runner and asks whether it earns its 10x. That question
assumes the account can pay when the answer is yes. **`/tightwad ramen` is the
standing answer that it cannot.**

In ramen mode, on a **private** repo, "locked to macOS and private → it stays"
does not apply. No job above 1x runs on a trigger — not macOS at 10x, not Windows
at 2x. Those jobs are not deleted and not argued with: they move verbatim, comments
and all, into `.github/workflows/paid-runners.yml`, whose only trigger is
`workflow_dispatch`. They cost zero until a human clicks Run workflow.

Two guarantees hold it together:

- **Promote before you park.** Any part of a suite that runs on Linux stays on
  Linux. Parking work that could have run at 1x is a failure of the mode.
- **A PR never ends with zero checks.** If parking empties the PR workflow, build
  the Linux lint job. A macOS-locked Swift package can always lint on Linux.

Ramen changes rule 4 and nothing else. Rules 1–3 and 5–9 run unchanged on whatever
remains. **On a public repo it changes no runner at all** — Actions are free, so
there is nothing to save.

This is the largest coverage cut this skill can make. Rule 3 moves a check to
merge-time; ramen moves one to never. Full method, the split procedure, the
required-status-check deadlock it can cause, and the three un-park prices the PR
must carry: `references/ramen.md`.

### 5. A `timeout-minutes` on every job

**GitHub's default job timeout is six hours.** One hung macOS job is 3,600 billed
minutes — more than an entire monthly quota, from a single stuck test.

Set it to roughly twice the observed p90 duration, and never leave it unset. A
60-minute cap on a 7-minute macOS job is still a 600-minute bill when something
hangs.

### 6. Cache downloads, not build products

Cache the dependency checkouts — content-addressed, cheap to restore, safe to
reuse. Do not cache `.build`, `target/`, or equivalent compiled output: a stale
hit there is a debugging session, not a saved minute.

Check the cache key actually varies. A key built from `hashFiles()` on a
gitignored or non-existent file finds nothing, collapses to a constant, and never
invalidates.

### 7. Actions current *and* pinned

Both, not either. Bring every action to its **latest stable release**, then pin
that release's SHA with the version in a trailing comment:

```yaml
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

**The version ends the comment.** Nothing after it — Dependabot maintains that
trailing version only when it is the last thing on the line, so a reason appended
there stops the comment updating and the file starts lying about which version it
runs. Reasons go on their own line above the `uses:`. See rule 9.

A pinned SHA answers "did this change under me". It says nothing about whether the
action is still maintained. Stale actions are a live problem rather than a
tidiness complaint: `actions/checkout@v4` runs on **`node20`, which reached end of
life on 2026-04-30**. `@v7` runs `node24`. GitHub deprecates and eventually breaks
EOL runtimes, and that arrives as a red build with nothing in the diff to explain
it — the same story that killed `node12` and `node16` before it.

**A major bump is a behaviour change.** Read the release notes for every major you
skip. If one touches how this repo uses the action, that is a conflict and it goes
to the user — same machinery as a load-bearing comment. Do not bump blind; a
version bump that turns a green build red is worse than the stale action was.

Method and the measurement commands: `references/hardening.md`.

### 8. Harden by default

Every workflow, every run:

- A **`permissions:`** block, least privilege, `contents: read` at workflow level
  and more declared per-job only where needed.
- **`persist-credentials: false`** on every checkout that does not push. The
  default is still `true` in v7.0.1, so the `GITHUB_TOKEN` sits in `.git/config`
  for every later step — including any build plugin, `npm ci` postinstall script,
  or other third-party code the job runs after checkout.
- **No untrusted input interpolated into `run:`.** Pass `github.event.*` through
  `env:`, never into a shell line.
- **Secrets scoped to the job that reads them**, never workflow-level `env:`.
- **`pull_request_target` plus a checkout of the PR head is a stop-and-ask**, not
  an auto-fix. It hands fork code your secrets, and silently rewriting the trigger
  may break the only thing that made the workflow work.

Full baseline, the severity you should honestly claim for each, and what is
deliberately excluded: `references/hardening.md`.

### 9. Keep them current without you

Rule 7 pins every action to an exact SHA. Nobody hand-bumps a 40-character hash, so
without a bot the currency pass you just did is the last one this repo ever gets.
**The skill creates the debt, so the skill ships the payer:** every write-mode run
writes or amends `.github/dependabot.yml` with a `github-actions` entry.

This is the one rule that costs rather than saves, because every Dependabot pull
request triggers CI. So configure it like a tightwad rather than accepting the
defaults:

- **Group the updates.** One `groups:` block with `patterns: ["*"]` turns N action
  bumps into one pull request instead of N.
- **Price the interval.** `PRs_per_month × billed_minutes_per_PR_run`, from the
  Phase 2 measurement. Default `weekly`; if that exceeds **10% of the account's
  monthly quota**, step down to `monthly` and write the reason into the file.
  `daily` on a private repo is nearly always wrong.
- **`directory: "/"`** is the only value this ecosystem takes, and it already
  covers `.github/workflows`, reusable workflows and composite actions under
  `.github/actions`.

**The repo's own package ecosystem is a separate, priced question.** `npm`,
`swift`, `cargo` and friends open pull requests that run the full test suite, so
they cost real minutes. Offer each one with `AskUserQuestion` in Phase 4. Never add
one silently.

**Mention auto-merge and `cooldown:`; enable neither.** Both are supply-chain
decisions the user makes deliberately — the same call this skill already makes
about `harden-runner`.

Method, the config to write, and how to amend an existing file:
`references/hardening.md`, Part 3.

---

## The flow

### Phase 0 — Orient

- `gh repo view --json visibility,name,primaryLanguage` — **visibility first**, it
  decides whether the rest of this is about money or only about speed.
- List the workflows: `gh api repos/<owner>/<repo>/contents/.github/workflows`.
- Confirm the working tree is clean.

### Phase 1 — Classify

Work out the archetype from the repo, not from its name. Four shapes, with
complete skeletons in `references/archetypes.md`:

- **Compiled library, Linux-capable**
- **App or UI framework, locked to macOS**
- **Node / TypeScript**
- **No build** — lint and link-check only

`references/archetypes.md` also carries the test for deciding whether a package is
genuinely locked to macOS, which is a question about its imports rather than about
its config.

### Phase 2 — Measure what it costs today

This is the phase that makes the skill honest. **Never estimate a duration you
could read.** Full method in `references/cost-model.md`; in short:

```
gh run list --status success --limit 5 --json databaseId
gh api repos/<owner>/<repo>/actions/runs/<id>/jobs --jq '.jobs[]|[.name,.started_at,.completed_at]|@tsv'
```

Round each job up to the whole minute, multiply by the runner multiplier,
multiply by how many runs a single merged commit triggers. That number is your
baseline, and the PR reports it.

If no run has ever succeeded, say so and estimate from the closest comparable
repo — but label it an estimate, in the PR, every time.

**In `audit` mode, stop here.** Report the baseline, the findings and what each
one would save. Write nothing.

**In `ramen audit` mode, stop here too** — and report the five things
`references/ramen.md` lists, including the required-status-check status and the
three un-park prices.

### Phase 3 — Rewrite the skeleton

Apply the nine rules. Write the new workflow files, and `.github/dependabot.yml`
alongside them.

**In ramen mode, split the files first.** Promote what runs on Linux, move every
remaining macOS and Windows job into `paid-runners.yml`, and check the required
status checks before you write anything (`references/ramen.md`). Then apply rules
1–3 to the Linux jobs that are left, because the arithmetic changed underneath
them.

Do the **currency pass before the rewrite**, not after: resolve every action's
latest stable release and its SHA first (`references/hardening.md`), so the
skeleton you write is already current rather than needing a second sweep. Read the
release notes for any major you cross and collect anything that looks breaking as
a conflict for Phase 4.

Work through `references/exceptions.md` **before** you delete anything. The short
version: a line carrying an explanatory comment is load-bearing until proven
otherwise, and survives the rewrite verbatim, comment included. Uncommented cruft
goes freely. **An existing `dependabot.yml` is covered by that rule too** — amend
it, never rewrite it.

### Phase 4 — Resolve the conflicts

Where the skeleton wants to remove something that carries a comment, **do not**.
Collect those conflicts and put them to the user with `AskUserQuestion`, one
decision per conflict, with the cost of keeping it in billed minutes.

Rule 9's ecosystem question goes here too, in the same shape and for the same
reason: the `github-actions` entry is automatic, and every other ecosystem is a
priced offer. One question per ecosystem.

This is the only place the skill stops. It is worth stopping for: those comments
record measured bugs and expensive lessons, and the cost of keeping one is usually
smaller than the cost of relearning it.

### Phase 5 — Land it

Branch `tightwad-<repo>-ci`, commit, push, open a PR against the base branch.

The PR body carries, in this order:

1. **The number, first line.** `<before> → <after> billed minutes per merged PR`,
   and the same for a month at the repo's recent merge rate.
2. **What changed, rule by rule** (1–6), each with its own saving — then rule 9's
   recurring cost as the last line of the same table, marked as an addition. It is
   a measured number, so it belongs with the money, and a reader deserves the net
   rather than the gross.
3. **What moved later** — every check that went from PR-time to merge-time or
   nightly, and what now surfaces after the merge instead of before it. Never
   bury this.
4. **What was parked** (ramen mode only, under its own heading) — every job now in
   `paid-runners.yml`, the coverage that went with it, the three un-park prices,
   the required-status-check finding, and the note that the Run workflow button
   does not exist until this PR merges. The coverage sentence also belongs in the
   PR's first paragraph; this heading is the detail, not the disclosure.
5. **Currency and hardening, under their own heading.** Never folded into the
   minutes table — cost is measured, safety is categorical, and blending them
   makes both unreadable. Name every major version crossed, and say the release
   notes were read. A reviewer needs to tell "bumped a patch" from "crossed three
   majors and believed the changelog." Rule 9's *choices* go here — the interval
   and why, the grouping, which ecosystems were added, and that auto-merge and
   `cooldown:` were named and left off.
6. **What was preserved and why** — the commented exceptions you carried forward.
7. **Whether the numbers are measured or estimated**, and from which runs.

Then report the PR URL and the one-line saving to the user.

---

## Order of work

When tightening several repos, go **cheapest to get wrong first**. You want the
skill's own mistakes to land somewhere harmless.

- Start with a repo that is already close to correct and cheap to fix — one
  duplicate trigger, one missing timeout.
- Take the macOS-locked repos next. They are where the money is, and the changes
  are job-count arithmetic rather than platform changes.
- **A repo whose test suite asserts bit-identical output goes last**, and gets a
  spike before it gets a PR. Moving such a package between Darwin and
  swift-corelibs Foundation can move dates, formatting and floating-point results.
  "It builds on Linux" and "it produces identical output on Linux" are different
  claims, and only the second one matters. Prove it with a corpus diff before you
  propose the runner change.

## Operating principles

- **Measured, not estimated.** Read real job durations. If you must estimate, say
  so in the PR every time you use the number.
- **Public means free — for money only.** Check visibility first and stop talking
  about cost if the answer is public. The security pass runs regardless.
- **Current and pinned, never one or the other.** A pinned SHA on an end-of-life
  Node runtime is a reproducible way to run unpatched code.
- **A pin you do not maintain is a snapshot of a decision you stopped making.**
  Rule 7 without rule 9 has a shelf life of about a quarter.
- **Never bump a major blind.** Read the notes for every major you cross. A green
  build turned red is a worse outcome than the stale action you replaced.
- **Claim the severity you can defend.** If the repo already defaults
  `GITHUB_TOKEN` to `read`, a missing `permissions:` block is defence in depth
  rather than an open door. Check, then say which it is. Inflating a finding costs
  you the reader's trust on the one that matters.
- **A comment is a reason.** Preserve it, carry it forward verbatim, and ask before
  removing what it protects.
- **Name what you moved later.** Cutting PR-time coverage is a real trade, not a
  pure saving. A PR that reports only the minutes saved is lying by omission.
- **Parked is not deleted, and parked is not free of consequence.** Ramen mode
  keeps every job and its comments, so the decision stays reversible — but the
  coverage is gone until someone clicks. Carry the price of un-parking in the PR
  so the user knows when they can afford it back.
- **Never touch `main` directly.** CI cannot be verified locally; the run on your
  PR is the proof. Open the PR and let it run.
- **Do not reduce the merge gate silently.** If after your change a PR no longer
  catches something it used to catch, that belongs in the PR body's first
  paragraph, not in a footnote.

## References

- `references/cost-model.md` — the multipliers, the shared-quota model, how to
  pull real durations, the billed-minutes formula, and the public-repo
  short-circuit. Read this in Phase 2.
- `references/archetypes.md` — the four repo shapes with complete workflow
  skeletons, the `dependabot.yml` every shape gets, and the test for whether a
  package is really locked to macOS. Read this in Phases 1 and 3.
- `references/ramen.md` — ramen mode in full: what it overrides, the
  promote-before-park pass, how to split a mixed workflow, the `paid-runners.yml`
  template, the required-status-check deadlock and how to check for it, the three
  un-park prices, and the audit variant. Read this in Phase 3 whenever the mode is
  `ramen`.
- `references/exceptions.md` — load-bearing versus cruft, the preserve rule, and
  how to put a conflict to the user. Read this in Phases 3 and 4, before deleting
  anything.
- `references/hardening.md` — rules 7, 8 and 9 in full: how to find an action's
  latest stable release and its SHA, how to read its Node runtime, why a major
  bump is a behaviour change, how to measure your own drift, the hardening
  baseline, what is deliberately left out, and (Part 3) the Dependabot config,
  how to price its interval, and how to amend one that already exists. Read this
  in Phase 3, before you write the skeleton.
