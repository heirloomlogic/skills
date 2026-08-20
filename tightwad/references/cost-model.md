# The cost model

Every claim this skill makes is a number. This is how you get the number.

## Step 0 — Is the repo public?

```
gh repo view --json visibility
```

**Public → Actions are free and unlimited.** Stop costing things. Report speed
improvements instead and say plainly in the PR that the minute figures are
informational.

**Rules 7 and 8 still run in full.** Currency, pinning and hardening are not cost
optimisations and do not care about visibility — if anything a public repo needs
them harder, because its workflows are readable by anyone looking for a way in and
its `github.event` input is genuinely attacker-controlled. A public repo gets the
whole security pass and none of the money argument.

Do not move a public repo off macOS to save money. There is none to save, and you
would be trading a real capability for an imaginary saving.

**This short-circuit outranks ramen mode.** `/tightwad ramen` parks no runner on a
public repo. Say so in one line and run the ordinary flow.

**Private → keep reading.**

## The quota

Private-repo Actions bill against a **monthly free quota shared by the whole
account**:

- GitHub Free — 2,000 minutes/month
- GitHub Pro — 3,000 minutes/month

Beyond that, minutes are billed per-minute at a rate that also scales with the
runner.

Two consequences worth stating in a PR:

- **The quota is account-wide, not per-repo.** One repo can exhaust it and block
  CI everywhere else on the account. This is a real failure mode, not a caution.
- **Reading the exact plan needs a `user` scope** most tokens do not carry
  (`gh api /users/<login>/settings/billing/actions` returns 404 without it). If
  you cannot read it, quote the range and say which you assumed.

## The multipliers

| Runner | Quota multiplier |
|---|---|
| Linux (`ubuntu-*`) | 1x |
| Windows (`windows-*`) | 2x |
| macOS (`macos-*`) | 10x |

**One macOS minute costs ten Linux minutes of quota.** Almost every finding this
skill produces is a restatement of that line.

These are the *quota consumption* multipliers, which is what matters while you are
inside the included minutes. Once you are paying cash the per-minute list prices
are not in exactly the same ratio — macOS is roughly 10x Linux, Windows roughly
1.7x rather than 2x. Use the quota multipliers; say so if a reader is going to
reconcile your figure against an invoice.

Linux ARM (`ubuntu-24.04-arm`) bills at the same 1x as x64 and is measurably
faster on Swift work — one Swift package measured its Debug suite at ~2m on ARM
against ~3m40s on x64. Measure your own; the gap varies by workload.

## The formula

```
billed_minutes_per_merged_PR
  = Σ over jobs ( ceil(job_duration_minutes) × runner_multiplier )
    × runs_triggered_per_merged_commit
```

Three things people get wrong:

1. **GitHub rounds each job up to the whole minute, individually.** A 34-second
   lint job bills one minute, not 0.57. Three short jobs cost three minutes
   before the multiplier.
2. **The multiplier applies to the rounded minutes**, so that 34-second macOS lint
   job bills **10 minutes**.
3. **`runs_triggered_per_merged_commit` is usually 2, not 1.** A workflow on both
   `pull_request` and `push: branches: [main]` runs once on the PR and again on
   the merge. Count the triggers before you count anything else.

## Reading real durations

Never estimate what you can read.

```
gh run list --status success --limit 5 --json databaseId,createdAt,name \
  --jq '.[]|[(.createdAt|split("T")[0]),.name,.databaseId]|@tsv'

gh api repos/<owner>/<repo>/actions/runs/<id>/jobs \
  --jq '.jobs[]|[.name,.started_at,.completed_at]|@tsv'
```

Take the **most recent successful** runs. Use three to five and take the slowest,
not the mean — you are sizing a bill and a timeout, and both want the tail.

**If CI is currently failing**, successful runs still exist further back. Ask for
`--status success` and reach as far as you need. A repo whose CI has been blocked
for weeks still has good data from before the block, and that data is exactly what
proves why it got blocked.

**If no run has ever succeeded**, estimate from the nearest comparable repo, and
label the number an estimate in the PR every single time you use it. Do not let an
estimate graduate into a fact between the analysis and the summary.

## A worked example

A private, macOS-only Swift package, from its last successful run:

| Job | Duration | Billed (rounded) |
|---|---|---|
| `swift-format lint (strict)` | 34s | 1 |
| `Build & Test (TZ=Asia/Tokyo)` | 6m43s | 7 |
| `Build & Test (TZ=UTC)` | 6m48s | 7 |

15 rounded minutes × 10 (macOS) = **150 billed minutes per run.**

The workflow triggers on `pull_request` *and* `push: branches: [main]`, so a
merged PR runs it twice: **300 billed minutes per merged PR.**

At that rate **13 merged PRs exhaust a 2,000-minute month.** That repo merged 87
in one month, or roughly 26,000 minutes against a 2,000–3,000 quota — which is
how it managed to block CI for every other private repo on the account.

Now apply the rules and re-derive:

- Rule 1, drop the duplicate `push` trigger: 300 → 150
- Rule 3, one TZ leg on PRs and both nightly: 150 → 80
- Rule 4, lint to Linux (`swift-format` ships in the toolchain; it parses source
  and does not need Darwin): 80 → 71
- Rule 4, tests to Linux — **only if a corpus diff proves identical output**:
  71 → 8

The first three are arithmetic and carry no platform risk. The fourth is the 10x,
and it is the one that needs a spike first.

## The same repo under ramen mode

`/tightwad ramen` does not take that fourth step. It never claims the macOS suite
runs on Linux, because that claim needs a corpus diff nobody has done. It parks the
suite instead, which needs no proof at all — only an honest account of what the
repo gave up (`ramen.md`).

Same measurement, re-derived:

- Rule 1, drop the duplicate `push` trigger: 300 → 150
- Rule 4, lint to Linux: 150 → 141
- Promote the suites that import nothing Apple-only — `ModelTests` and
  `ParserTests`, ~2m on ARM at 1x: 141 → 143, then
- Park the two macOS TZ legs (14 rounded minutes × 10): **143 → 3**

**3 billed minutes per merged PR.** Note that the promotion step *added* two
minutes before the parking removed 140. That ordering is the point: promote first,
so the Linux tier catches what it can, then park what is genuinely left.

The parked figure is the other half of the report:

```
parked: 140 billed minutes per run (2 macOS TZ legs)
  if returned to `pull_request`:  140 per merged PR
  if run weekly:                  560 per month — 28% of a 2,000 quota
  if run monthly:                 140 per month — 7%
```

That repo cannot afford weekly, and saying so is more useful than the 3. **A
monthly manual run is what it can afford**, and that is the sentence the user needs.

## Reporting the number

The PR opens with the number and nothing else:

```
300 → 71 billed minutes per merged PR (measured, run 30958306803)
~26,000 → ~6,200 minutes/month at last month's merge rate
plus ~71 minutes/month for the monthly grouped actions updater (rule 9)
```

Then the rule-by-rule breakdown. A saving nobody can check is a saving nobody
believes, so cite the run ID you measured.

**Report the net, not just the gross.** Rule 9 is the only rule that adds minutes,
and its cost comes off the same measurement as the savings:

```
dependabot_minutes_per_month = PRs_per_month × billed_minutes_per_PR_run
```

Price it against the *post-rewrite* per-run figure, not the one you started with —
the updater's pull requests run the workflows you just made cheaper. On the repo
above that is one grouped PR a month at 71 minutes, against roughly 19,800 saved.
A reader who finds that line for themselves after merging trusts the next number
less, so put it in the table.

**Report the trade in the same breath.** If one timezone leg moved to nightly, the
line reads "one TZ leg moved to nightly: −70 min/PR, and a timezone-divergence
regression now surfaces at the nightly run rather than on the PR." Both halves,
every time.

**Never fold a parked cost into the saving.** In ramen mode the minutes table
reports what CI now costs; the parked figure is a standing number describing
coverage the repo no longer has. It gets its own heading, with the three un-park
prices under it. Adding it to the saving would make a hole read as an
optimisation.
