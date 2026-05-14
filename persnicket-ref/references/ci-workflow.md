# Persnicket CI Workflow Reference

How to wire `swift-format` lint into GitHub Actions for a Swift package using Persnicket. The recommended pattern invokes `swift-format lint --strict` directly (not via the SwiftPM plugin) and uses a problem matcher to annotate violations inline on the PR.

## macOS workflow

```yaml
name: Lint

on:
  pull_request:
  push:
    branches: [main]

jobs:
  swift-format-lint:
    runs-on: macos-26
    steps:
      - uses: actions/checkout@v4

      - name: Setup swift-format lint
        run: |
          swift package resolve
          .build/checkouts/Persnicket/bin/ci-lint-setup

      - name: Lint (strict)
        run: xcrun swift-format lint --strict --parallel --recursive --configuration .swift-format Sources Tests
```

What each step does:

- **`swift package resolve`** — pulls Persnicket into `.build/checkouts/` so the setup script is reachable.
- **`.build/checkouts/Persnicket/bin/ci-lint-setup`** — copies a default `.swift-format` into the repo root if one is missing, installs the problem matcher at `.github/swift-format-matcher.json`, and emits the `::add-matcher::` workflow command so violations annotate the PR.
- **`xcrun swift-format lint --strict …`** — the actual linter. Exit code drives the job's pass/fail. `--strict` promotes warnings to errors. Replace `Sources Tests` with whichever directories you want linted.

## Linux delta

Two changes for Linux:

1. Add a Swift setup step before the `ci-lint-setup` run, with a pinned `swift-version`.
2. Drop the `xcrun` prefix from the lint command.

```yaml
jobs:
  swift-format-lint:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - uses: swift-actions/setup-swift@v2
        with:
          swift-version: "6.2"

      - name: Setup swift-format lint
        run: |
          swift package resolve
          .build/checkouts/Persnicket/bin/ci-lint-setup

      - name: Lint (strict)
        run: swift-format lint --strict --parallel --recursive --configuration .swift-format Sources Tests
```

The `ci-lint-setup` script itself is portable `sh` and runs unchanged.

## The problem matcher

`bin/ci-lint-setup` installs a small JSON file at `.github/swift-format-matcher.json` that tells the runner how to parse `swift-format`'s output:

```json
{
  "problemMatcher": [
    {
      "owner": "swift-format",
      "severity": "warning",
      "pattern": [
        {
          "regexp": "^(.+):(\\d+):(\\d+): (warning|error): (.+)$",
          "file": 1, "line": 2, "column": 3, "severity": 4, "message": 5
        }
      ]
    }
  ]
}
```

`swift-format` emits violations in `path:line:col: severity: message` form. The matcher's regex extracts those fields, and the `::add-matcher::` directive (also emitted by `ci-lint-setup`) tells GitHub to convert matched lines into native annotations on the PR's "Files changed" tab.

This approach uses zero third-party actions and no extra workflow permissions. The linter's own exit code drives job pass/fail.

## Caveats

**Inline annotations only show on changed lines.** Annotations on the PR diff are limited to lines that are part of the diff. Violations on unchanged lines still appear in the workflow run summary, just not inline next to the code.

**GitHub caps inline annotations at 10 errors + 10 warnings per run.** Anything past that is listed in the run summary instead. This is rarely a problem for steady-state PRs, but for a first-time lint sweep across a large codebase, run `swift-format lint` locally to see the full list.

**`.swift-format` format can drift between Swift minor versions.** The `swift-format` configuration schema has previously shipped breaking changes without a version bump. A `.swift-format` that parses cleanly under Swift 6.1 may fail under 6.2. If local dev and CI drift, you'll see lint failures that can't be reproduced locally. Mitigate by pinning the same Swift major.minor on both sides; patch versions don't matter.

**`swift-actions/setup-swift@v2` defaults to an older Swift if you omit `swift-version`.** This can produce a `swift-format cannot parse the configuration — linting skipped` warning even when the build itself succeeds. Always pin `swift-version` to match the toolchain your `.swift-format` was written against.

## Why lint via CLI, not via Persnoop

Persnoop (the build-tool plugin) lints during `swift build`, which is great for local feedback but adds two friction points in CI:

- The plugin must build itself before linting can run, slowing CI on cold caches.
- The plugin emits warnings, not failures, by default — driving CI pass/fail requires extra plumbing.

Calling `swift-format lint --strict` directly skips both. Keep Persnoop attached for local dev (so devs see violations during normal builds) and let CI invoke the linter standalone.
