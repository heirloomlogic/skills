# Currency and hardening

The cost rules make CI cheaper. These make it safe. Both are **on by default**,
for the same practical reason: you already have the file open. Applying hardening
later means opening every workflow a second time.

Keep the two kinds of claim apart when you report. **Cost is measured; hardening
is categorical.** Do not blend them into one number.

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
- **Dependency scanning and Dependabot.** Worth having, not this skill's job.
  Worth one line in the PR, though: a repo that adopts rule 7 gets SHA pins that a
  human will not keep current by hand.

## Reporting hardening

A separate section of the PR body, under its own heading, never mixed into the
minutes table. Two lines per finding: what was open, what it is now.

Where a bump crosses a major, say which majors were crossed and that the release
notes were read. A reviewer needs to know the difference between "bumped a patch"
and "crossed three majors and believed the changelog."
