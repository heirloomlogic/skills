# Ramen mode

Rule 4 normally prices a macOS runner and asks whether it earns its 10x. That question assumes the account can pay when the answer is yes.

**Ramen mode is the standing answer that it cannot.** No job above 1x runs automatically on a private repo — not macOS at 10x, not Windows at 2x. Those jobs are not deleted and not argued with. They move to a workflow that runs only when a human clicks Run workflow.

The name follows "ramen profitable": you eat, you keep the roof, and you do not pay 10x for CI. When money arrives, one trigger edit brings the jobs back, and this page tells the user what that will cost.

## What ramen overrides, and what it leaves alone

**It overrides rule 4 only.** In ramen mode, "locked to macOS and private → it stays, and every remaining job justifies its 10x in a comment" is replaced by "no job above 1x runs on a trigger". Rules 1–3 and 5–9 run unchanged, on whatever Linux jobs remain.

**Public repos are unaffected.** Actions are free on a public repo, so there is no money to save and ramen mode changes no runner there. Say that in one line and carry on with the ordinary run — rules 7, 8 and 9 still apply in full, exactly as `cost-model.md` step 0 describes.

Check visibility before anything else. Running ramen against a public repo and parking its macOS jobs trades a real capability for an imaginary saving.

---

## Step 1 — Promote before you park

**Parking a suite that could have run at 1x is a failure of this mode, not a success.** Before a macOS job moves, find out how much of it runs on Linux.

Use the macOS-lock test in `archetypes.md` ("Is this package really locked to macOS?"). It is a question about imports, not about config:

```
grep -rnE '^import (SwiftUI|AppKit|UIKit|CoreLocation|CoreData|AVFoundation|StoreKit|WidgetKit|MapKit|Combine)' Sources/
```

Three outcomes:

- **No hit anywhere.** The package was never locked. Move the whole job to `ubuntu-24.04-arm`. Nothing gets parked, and ramen mode has done its job by making you check.
- **Hits in some targets.** The rest is Linux-testable, and that is usually where the business logic lives. Keep those tests on Linux with a filter (`swift test --filter <SuiteName>`), and park only the targets that import an Apple framework. Write a comment naming which framework forced the split.
- **Hits everywhere in the product target.** Nothing to promote. Park the job.

A lint job never gets parked. `swift-format` ships in the Swift Linux toolchain and lints by parsing source, so it runs at 1x on any package. If the lint step shells out to `xcrun`, drop the `xcrun` prefix rather than parking the job.

## Step 2 — Split the files

`workflow_dispatch` is a **workflow-level** trigger. It cannot gate one job inside a workflow, so ramen mode moves jobs between files rather than editing triggers in place.

Three shapes:

- **Mixed workflow** — Linux jobs stay where they are. Every `macos-*` and `windows-*` job moves verbatim into `.github/workflows/paid-runners.yml`.
- **Entirely macOS or Windows** — do not split. Change that workflow's `on:` block to `workflow_dispatch:` alone and leave its jobs where they are. Rename the file only if its current name now lies about when it runs.
- **A matrix with mixed legs** — split the matrix. Linux legs stay in the PR job; the macOS and Windows legs become their own job in the parked file. Two jobs with the same steps and different `runs-on` is the correct output here, not a smell.

Carry each job's comments across **verbatim and in position**. Ramen parks rather than deletes, so `exceptions.md`'s preserve rule is satisfied by the move itself, and no conflict question is raised.

## Step 3 — Write `paid-runners.yml`

```yaml
# Jobs that bill above 1x. Parked here by tightwad ramen mode: nothing in this
# file runs on a trigger, so it costs zero billed minutes until someone runs it
# by hand from the Actions tab.
#
# TO UN-PARK: replace the `on:` block below with the trigger these jobs used to
# have, and delete this comment. At the measured rate that costs <N> billed
# minutes per merged PR — see the PR that created this file.
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

Four things about that file:

- **Fill in `<N>`** from the Phase 2 measurement. A header comment carrying a real number is load-bearing for the next run of this skill; one carrying this page's placeholder is furniture.
- **`timeout-minutes` still matters, and matters more here.** A manual run is unsupervised by definition — nobody is watching a build they started and walked away from. Rule 5 applies unchanged.
- **The rule 7 and 8 baseline applies.** A parked workflow still needs current pinned actions and a `permissions:` block. It runs real code the moment somebody clicks it.
- **`concurrency` is cheap insurance** against a double-click.

Re-resolve the action SHAs before writing this; the pins above were current on 2026-08-19.

---

## The stop-and-ask: required status checks

**A parked job that is a required status check blocks every PR forever.** This is the one way ramen mode can deadlock a repo, and it is worth being careful about because the failure is silent until somebody tries to merge.

The distinction is exact, and GitHub documents it. A job **skipped by a conditional** reports `skipped`, which branch protection counts alongside `success` and `neutral` as a pass. A **workflow that never runs** — because no trigger matches, which is precisely what parking does — never reports at all, so its check stays **pending** and merge stays blocked with nothing red to explain it. See [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks).

That is why parking is riskier here than an `if:` gate would be, and why this check is not optional.

Check before you write:

```
gh api repos/<owner>/<repo>/rulesets --jq '.[] | [.name, .target] | @tsv'
gh api repos/<owner>/<repo>/branches/<base>/protection \
  --jq '.required_status_checks.contexts[]'
```

Both need admin and both may return 404 on a token without it. Three outcomes, and all three go in the PR body under their own heading:

- **A parked job name appears in the list.** Say which one, say the repo will not merge until it is removed from the required set, and say that this skill does not edit repo settings.
- **The list reads clean.** Say you checked and say it was clean. A reader needs to tell "checked, fine" from "did not check".
- **You could not read it.** Say so, name the 404, and tell the user to check the required-checks list themselves before merging.

Branch protection is repo settings, which `hardening.md` puts out of scope. Ramen mode does not change that. **It reports; it never edits.**

## The second caveat: the button does not exist yet

**`workflow_dispatch` shows no Run workflow button until the file is on the default branch.** GitHub reads the dispatch trigger from the default branch only — [documented](https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow), not folklore.

So between opening the ramen PR and merging it, the parked jobs are unreachable — you cannot demonstrate that they still work by running them from the PR branch. Put that in the PR body. It is the first question a careful reviewer asks, and "you cannot try it yet" is a better answer than silence.

Once merged, a dispatch run can target any branch from the ref picker.

---

## Price the un-park

The user turned these runners off because they cost too much. They need the number that tells them when they can afford to turn them back on, so the PR carries all three prices from the Phase 2 measurement:

```
parked jobs, if returned to `pull_request`:  <N> billed minutes per merged PR
parked jobs, if run nightly:                 <N × 30> billed minutes per month
parked jobs, if run weekly:                  <N × 4>  billed minutes per month
```

The weekly line usually matters most. It is the cheapest way back to real coverage, and it is often affordable long before `pull_request` is.

**Never fold the parked cost into the saving.** The minutes table reports what CI now costs; the parked cost is a standing figure describing coverage the repo no longer has. Blending them makes both unreadable, the same argument `hardening.md` makes about cost versus safety.

## What this trade actually costs

Ramen mode is the largest coverage cut this skill can make, and the PR body says so **in its first paragraph**, not in a footnote.

Rule 3 moves a check from PR-time to merge-time, so a regression surfaces late. Ramen moves a check to never, so **a platform regression surfaces when a human remembers to look.** That is a real hole, the user opened it deliberately, and the PR should be honest that it is a hole rather than an optimisation.

Guarantee that keeps it survivable: **a PR never ends with zero checks.** If parking leaves the PR workflow empty, build the Linux lint job from archetype 2 in `archetypes.md` and ship it. A macOS-locked Swift package can always lint on Linux, so there is no repo where this guarantee is impossible to keep.

---

## Rule 9 under ramen

Nothing changes in the method, but the arithmetic gets easier and it is worth saying why in the PR.

Dependabot bumps the action SHAs **inside** `paid-runners.yml` like any other workflow file — a dispatch-only trigger does not exempt a file from version updates, and it should not, since a parked job runs real code when clicked. But the pull request that carries those bumps triggers only the automatic workflows, which after ramen are Linux-only.

So the updater's monthly bill is the Linux figure, and `weekly` is usually affordable where `monthly` was the right answer before. Re-run the arithmetic in `hardening.md` Part 3 against the **post-ramen** per-run cost, and write the new number into the `groups:` comment.

## In audit mode

`/tightwad ramen audit` measures and reports. It writes nothing, opens nothing, and creates no branch.

Report:

1. **The parked set** — every job above 1x, with its measured duration, its multiplier and its billed minutes.
2. **The Linux remainder** — what would still gate a PR, and whether that is anything at all.
3. **The promotion finding** — any macOS job that turns out to be Linux-capable. This is the best outcome the audit can produce, because it costs no coverage.
4. **The required-check status** — clean, blocked, or unreadable.
5. **The three un-park prices.**

If the repo is public, the audit says so first and reports nothing about parking.
