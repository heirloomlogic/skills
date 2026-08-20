# Exceptions — what to preserve

The skeleton is confident and it is often wrong about one line in a file. This is
the rule that stops that confidence being destructive.

## The rule

**A workflow line carrying an explanatory comment is load-bearing until proven
otherwise.** It survives the rewrite verbatim, comment included, in the same
position relative to the step it protects.

An uncommented line is fair game.

That asymmetry does useful work in both directions. It protects knowledge that was
expensive to acquire, and it puts quiet pressure on the repo: a step nobody
explained is a step nobody defends.

**`.github/dependabot.yml` is covered by this rule**, not just the workflows. A
commented `ignore:` entry usually records an upgrade that broke something, and a
commented `groups:` block usually records a batching decision somebody priced. Both
survive verbatim. Amend that file; never rewrite it.

## Why this rule exists

Two real examples, both of which a template would have deleted.

**A 40-line comment explaining a build flag.** A Swift package passes
`--disable-experimental-prebuilts`, and the comment says why: SwiftPM's prebuilt
swift-syntax is on by default, is obviously attractive, downloads in 0.26s — and
then fails to link, because of a specific SwiftPM bug
([swiftlang/swift-package-manager#10218](https://github.com/swiftlang/swift-package-manager/issues/10218)).
The comment names the exact symbol the build dies on, and records that deleting
the macro test target was *measured* not to dodge it. Drop the flag and you
reintroduce a bug that took a day to characterise, and the failure arrives as a
link error with nothing in the diff to explain it.

**A two-timezone test matrix.** The comment says the divergence between the zones
is the signal that caught a specific issue — a device-timezone-dependent bug — and
that `Asia/Tokyo` is chosen because it sits the far side of the date line from
UTC, where a weekday-derived value diverges most. Collapse that matrix to one leg
without reading the comment and you have thrown away a deliberately-built
detector.

Both comments look like noise to a skeleton. Both are the most valuable lines in
their file.

## Reading a comment properly

Not every comment is a reason. Sort them:

**Load-bearing — preserve:**

- It names a bug, an issue number, or a symbol. *"caught #51"*, *"swiftlang/swift-package-manager#10218"*
- It records a measurement. *"~2m against ~3m40s"*, *"measured, not assumed"*
- It explains why the obvious thing is wrong. *"`nil` would be the better degradation, but…"*
- It carries an expiry condition. *"WHEN 6.5 SHIPS: drop these flags"*

**Not load-bearing — treat as uncommented:**

- It restates the code. `# checkout the repo`
- It is a section header. `# --- tests ---`
- It is commented-out configuration nobody deleted.

An expiry condition deserves special handling: **check whether it has expired.**
A comment saying "re-enable when Swift 6.5 ships" is load-bearing until 6.5 ships
and dead weight afterwards. If you can tell it has expired, that is a finding worth
its own line in the PR — and it is the one case where you may remove a
load-bearing comment, because the comment itself told you to.

## When the skeleton and a comment disagree

**Do not delete. Collect the conflict.**

At the end of Phase 3 you will have zero or more conflicts. Put each one to the
user with `AskUserQuestion`, one decision per conflict, framed as a price:

> `ci.yml` runs two timezone legs. The comment says the divergence caught #51.
> The skeleton wants one leg on PRs and both nightly.
> Keeping both on PRs costs **70 billed minutes per merged PR**.
> Keep both / move the second to nightly / drop it?

Three things make that a good question:

- The cost is a number, so the user is trading rather than guessing.
- The reason is quoted, so they are not re-deriving what the comment already knows.
- The middle option usually wins, and the skeleton would have missed it.

**Do not batch conflicts into one question with a combined price.** Each is a
separate call and the user may answer them differently.

## Version bumps go through the same gate

A major version bump is not a formatting change, so it gets the same treatment as
a load-bearing comment. Read the release notes for every major you cross
(`hardening.md`). If one describes a changed default, a removed input, or a new
required permission that touches how this repo uses the action, **collect it as a
conflict rather than shipping it**:

> `actions/download-artifact` is pinned at v4.3.0; latest stable is v8.0.1.
> v5 changed the default download path when no `name` is given, and
> `release.yml:116` relies on that default.
> Bump and adjust the path / bump and pin the old behaviour / leave it?

Patch and minor bumps do not need this. Cross a major without reading its notes
and you have swapped a stale action for a red build, which is the worse trade.

## What you may remove without asking

- Duplicate triggers running the same job on the same commit (rule 1). This is
  arithmetic, not judgement — the second run tests a commit already tested.
- A missing `timeout-minutes` (rule 5). You are adding, not removing.
- A missing `concurrency` block (rule 2), on a PR workflow.
- Steps and jobs with no comment at all, where the skeleton has an equivalent.
- **Patch and minor** action bumps, and pinning a floating tag to the SHA it
  currently resolves to. Behaviour is unchanged at the moment you make the edit.
- The rule 8 additions — a `permissions:` block, `persist-credentials: false` on a
  checkout that does not push. You are constraining, not removing, and both fail
  loudly rather than silently if you get them wrong.
- **A `.github/dependabot.yml` where none exists** (rule 9). You are adding, like
  `timeout-minutes`. Editing one that already exists is not covered by this and
  goes through the preserve rule above.

## What you never remove, with or without a comment

- **The last check standing between a PR and `main`.** If your change means a PR
  no longer catches something it used to catch, that is not a cut, it is a policy
  change. Ask.
- **Anything with `secrets.` in it**, until you have traced what reads it. A deploy
  that silently stops stamping a build SHA is worse than a slow deploy.
- **A `concurrency: cancel-in-progress: false` on a deploy workflow.** That `false`
  is deliberate every time.
- **Credentials on a checkout that pushes.** A release, a docs deploy, or a
  changelog commit needs the token to survive. Leave `persist-credentials` alone
  there and add the comment saying why.

## Writing your own comments

Every change you make that a future reader would want to undo gets a comment
explaining why — the same standard you are applying to everyone else. In
particular, when you move a check from PR-time to merge-time or nightly, say so in
the file:

```yaml
# Runs at merge rather than on every PR: at 10x, two legs on every PR cost 140
# billed minutes and the divergence they detect is rare. A regression here
# surfaces at the nightly run rather than on the PR. Widen back if one slips
# through.
```

That comment is now load-bearing, and the next run of this skill will preserve it.
That is the intended outcome: the skeleton gets applied once, and the reasons
accumulate.

## The one place a reason may not go

A pinned `uses:` line is the exception, and it is a hard one. Dependabot maintains
the trailing version comment only when the version is the last thing on the line,
so appending a reason there breaks the automation that rule 9 just installed — the
SHA keeps getting bumped, the comment does not, and the file starts lying about
which version it runs.

```yaml
# Wrong. The reason is real; the position kills the update.
- uses: actions/checkout@3d3c... # v7.0.1, pinned for the fetch-depth fix

# Right. Same reason, still load-bearing, and the bot can still do its job.
# Pinned for the fetch-depth fix — see #214.
- uses: actions/checkout@3d3c... # v7.0.1
```

**The reason goes above the line; the version ends the trailing comment.** When you
find the wrong shape in a repo, move the reason up rather than deleting it. That
move preserves the comment, so it needs no conflict question.
