# Archetypes

Four repo shapes. Detect the shape from the repo, not from its name — read
`Package.swift`, `package.json`, `Cargo.toml`, or the absence of all three.

Each skeleton below is the *starting* file. Merge the repo's load-bearing
exceptions into it (`exceptions.md`) rather than shipping it bare.

Every skeleton already carries the rule 7 and 8 baseline — a `permissions:` block,
`persist-credentials: false`, and actions at their latest stable release pinned by
SHA. **Re-resolve the versions before you use these** (`hardening.md`); the tags
and SHAs written below were current on 2026-08-19 and will not stay that way. The
same goes for the container image tag.

---

## Is this package really locked to macOS?

The answer is a fact about the code, not about the config, so derive it every time
rather than trusting a list.

**Locked to macOS** if the package or its dependencies import an Apple-only
framework, or link an Apple-only SDK:

```
grep -rnE '^import (SwiftUI|AppKit|UIKit|CoreLocation|CoreData|AVFoundation|StoreKit|WidgetKit|MapKit|Combine)' Sources/
grep -nE 'platforms:|\.iOS\(|\.macOS\(|\.watchOS\(|\.tvOS\(' Package.swift
```

A hit in `Sources/` for a target that ships in the product means the package
cannot build on Linux. A `platforms:` line alone means nothing — it declares
minimum versions, not exclusivity.

Check the dependencies too. A package that imports nothing Apple-only but depends
on a vendor SDK distributed as an `.xcframework` is just as locked.

**Locked to macOS is not the same as every job locked to macOS.** A macOS-locked
Swift package still lints on Linux — `swift-format` ships in the Swift Linux
toolchain and lints by parsing source. In a private repo that one move takes the
lint job from 10x to 1x for free. Check whether the lint step shells out to
`xcrun`; if it does, drop the `xcrun` prefix rather than keeping the runner.

Where you *do* keep a macOS job, the corollary is rule 4's comment requirement:
say in the file which Apple framework forces it, so the next reader does not have
to re-derive this.

---

## 1. Compiled library, Linux-capable

Shown for Swift. The toolchain arrives as a pinned container image rather than a
scripted install: the compiler is pinned, which matters because macro plugins are
compiler-coupled, and it saves the setup step. The same shape works for Rust, Go
or anything else with an official image.

```yaml
name: Tests

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-24.04-arm
    container: swift:6.3.3-noble
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          # Nothing here pushes, so the token does not need to survive into
          # `.git/config` where every later step — including SwiftPM build
          # plugins — could read it.
          persist-credentials: false

      # The container runs as root over a checkout git considers foreign;
      # without this, git refuses ("dubious ownership") wherever SwiftPM or a
      # build step shells out to it.
      - name: Trust the workspace
        run: git config --global --add safe.directory "$GITHUB_WORKSPACE"

      # SwiftPM's shared cache only — dependency checkouts, content-addressed and
      # cheap to restore. Deliberately not `.build`: a stale hit there is a
      # debugging session, not a saved minute.
      - name: Cache SwiftPM downloads
        uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
        with:
          path: /root/.cache/org.swift.swiftpm
          key: swiftpm-${{ runner.os }}-${{ runner.arch }}-${{ hashFiles('Package.swift') }}
          restore-keys: |
            swiftpm-${{ runner.os }}-${{ runner.arch }}-

      - name: Test (Debug)
        run: swift test

      # Release guards against optimization-only regressions the Debug suite
      # passes through silently. It is the most expensive step, so it runs at
      # merge rather than on every PR: such a regression surfaces at merge, not
      # before it. Widen back to PRs if one ever slips through.
      - name: Test (Release)
        if: github.event_name == 'push'
        run: swift test -c release
```

Note the `push: [main]` trigger survives rule 1 here, because the `push` run does
something the PR run deliberately does not — the Release suite. That is the only
legitimate reason to keep it.

Lint folds into this job unless the repo needs it isolated. One runner spin-up
beats two.

## 2. App or UI framework, locked to macOS

Every job here costs 10x, so the job count *is* the optimisation.

```yaml
name: Tests

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # Lint does not need macOS. swift-format ships in the Swift Linux toolchain and
  # lints by parsing source, so this job runs at 1x instead of 10x.
  lint:
    runs-on: ubuntu-24.04-arm
    container: swift:6.3.3-noble
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - run: git config --global --add safe.directory "$GITHUB_WORKSPACE"
      - name: Lint (strict)
        run: swift-format lint --strict --parallel --recursive --configuration .swift-format Sources Tests

  # The only job that genuinely needs the platform: the package imports SwiftUI.
  test:
    runs-on: macos-26
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Test
        run: swift test
```

Then interrogate what is left, because at 10x each question is worth real money:

- **Does the PR need every matrix leg?** Keep the one that catches most
  regressions; move the rest to a nightly `schedule`.
- **Does the PR need a documentation build?** Almost never. Move it to `push`.
- **Does this need `push: [main]` at all?** Only if that run does something the
  PR run does not.

### 2a. The same repo under ramen mode

`/tightwad ramen` stops asking those questions and parks the answer. The skeleton
above becomes two files, because `workflow_dispatch` is a workflow-level trigger
and cannot gate one job. Method and caveats: `ramen.md`.

`.github/workflows/ci.yml` — everything that runs at 1x, on every PR:

```yaml
name: CI

on:
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-24.04-arm
    container: swift:6.3.3-noble
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - run: git config --global --add safe.directory "$GITHUB_WORKSPACE"
      - name: Lint (strict)
        run: swift-format lint --strict --parallel --recursive --configuration .swift-format Sources Tests

      # Promoted rather than parked: these suites import nothing Apple-only, so
      # they run at 1x. Only the SwiftUI-dependent suites went to paid-runners.yml.
      - name: Test (Linux-capable suites)
        run: swift test --filter 'ModelTests|ParserTests'
```

`.github/workflows/paid-runners.yml` — everything above 1x, on no trigger:

```yaml
# Jobs that bill above 1x. Parked here by tightwad ramen mode: nothing in this
# file runs on a trigger, so it costs zero billed minutes until someone runs it
# by hand from the Actions tab.
#
# TO UN-PARK: replace the `on:` block below with `pull_request:` and delete this
# comment. Measured at 70 billed minutes per merged PR — see the PR that created
# this file.
name: Paid runners

on:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # The only job that genuinely needs the platform: the package imports SwiftUI.
  test-macos:
    runs-on: macos-26
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Test
        run: swift test
```

Three things that skeleton is doing deliberately:

- **The `push: [main]` trigger is gone**, because nothing left needs it. Under
  ramen the Linux jobs are cheap enough that a merge-time tier buys little, and the
  expensive tier it used to protect is parked.
- **`timeout-minutes` survives into the parked file**, and matters more there. A
  manual run is unsupervised by definition.
- **The macOS job keeps its comment verbatim.** Ramen parks rather than deletes,
  which is how it satisfies the `exceptions.md` preserve rule without asking.

Archetypes 1, 3 and 4 are already all-1x, so ramen mode parks nothing in them.
Say that and run the ordinary flow.

## 3. Node / TypeScript

Already 1x, so this is about job count and duplication rather than runners.

```yaml
name: ci

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          # npm ci runs third-party postinstall scripts in this job. The token
          # has no business being readable by them.
          persist-credentials: false
      - uses: ./.github/actions/node-setup
      - run: npm run typecheck
      - run: npm test
```

A local `./.github/actions/node-setup` composite is the right pattern and stays —
but read it too. A composite action pins its own `uses:` lines, and a stale
`actions/setup-node` hides there just as well as in a workflow.

The common waste here is a **deploy workflow that re-runs the test suite** on a
commit the PR already tested. Drop the `needs: test` and call the deploy job
directly; the gate happened on the PR.

Deploy workflows keep `cancel-in-progress: false`. A half-killed deploy costs more
than the minutes.

## 4. No build

Docs, skills, shell. Lint and check links; do not spin a toolchain.

```yaml
name: Lint

on:
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Check markdown links
        run: <the repo's link checker>
```

If a repo of this shape has a macOS job, that is the finding. Report it and delete
it.

---

## The fifth file: `.github/dependabot.yml`

Every archetype gets this one, whatever its shape, because every archetype gets
rule 7's SHA pins and nobody bumps those by hand.

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    # "/" is the only value this ecosystem accepts. It already covers
    # .github/workflows, reusable workflows, and composite actions under
    # .github/actions — the ./.github/actions/node-setup composite in
    # archetype 3 needs no entry of its own.
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    # One PR per batch, not one per action.
    groups:
      actions:
        patterns: ["*"]
    open-pull-requests-limit: 3
    commit-message:
      prefix: "ci"
```

Two things to change before shipping it:

- **The interval is priced, not copied.** Default `weekly`; step down to `monthly`
  when four PRs a month exceeds 10% of the account quota. Archetype 2 usually
  lands on `monthly` — at 10x, four extra runs a month is real money.
- **The `groups:` comment should carry the repo's own measured per-run cost**, so
  the next reader can re-derive the interval without re-measuring.

The repo's own ecosystem — `npm` for archetype 3, `swift` for 1 and 2 — is a
second entry and a separate priced question for the user. It is never added
silently. `hardening.md` Part 3 has the question to ask.

Archetype 4 gets the file too. It has no build, so its updater is nearly free, and
it is the shape most likely to be forgotten.

---

## Getting the SHAs

Never invent one, and never carry one forward from these pages without checking.
Find the latest stable release, then resolve **that exact tag**:

```
gh api repos/actions/checkout/releases/latest --jq '.tag_name'
gh api repos/actions/checkout/git/refs/tags/v7.0.1 --jq '.object.sha'
```

Write it with the version in a trailing comment, so a human can read the intent
and a bot can bump it:

```yaml
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

Three rules that follow:

- **The version ends the comment.** Dependabot maintains that trailing version only
  when nothing follows it. Append a reason and the SHA still gets bumped while the
  comment silently does not, which leaves the file lying about which version it
  runs. Reasons go on their own line above the `uses:`.
- **One version of an action per repo.** If two workflows pin different SHAs for
  the same action, converge them on the latest rather than preserving the split.
  A repo that disagrees with itself is a repo where nobody is watching.
- **Resolving a major tag is not pinning.** `refs/tags/v7` moves. Resolve
  `refs/tags/v7.0.1`, the release, so the comment and the SHA describe the same
  thing a year from now.

`hardening.md` holds the rest: reading an action's Node runtime, why a major bump
needs its release notes read, and how to measure the repo's own drift.
