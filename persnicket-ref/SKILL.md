---
name: persnicket-ref
description: Setup and usage reference for the Persnicket SPM plugin — a lightweight `swift-format` wrapper for Swift packages. Use when adding lint or format tooling to a Swift package or Xcode project, when you see `Persnicket`, `Persnoop`, or `Persnipe` in a `Package.swift`, or when wiring `swift-format` into GitHub Actions CI. Covers the SPM dependency line, per-target `Persnoop` build-tool plugin attachment, the `Persnipe` `format-source-code` command, choosing or generating a `.swift-format` config (vanilla `swift-format dump-configuration` vs. Persnicket's opinionated config), Linux/macOS toolchain caveats, the recommended GitHub Actions workflow with the `bin/ci-lint-setup` helper and inline-annotation problem matcher, and keeping Persnoop dev-only when publishing a Swift package so consumers don't inherit the build-tool plugin — gating it behind a gitignored `.dev-tooling` sentinel and the `swift package purge-cache` reset that toggling it requires.
---

# Persnicket Reference

Persnicket is a lightweight Swift Package Manager plugin that lints and formats Swift source files using the Swift toolchain's built-in `swift-format` binary. It ships two plugins:

- **Persnoop** — a SwiftPM build-tool plugin. Runs `swift-format lint` as a pre-build step on every target it's attached to, so style violations surface during normal `swift build` / Xcode builds.
- **Persnipe** — a SwiftPM command plugin. Registers the `format-source-code` verb and runs `swift-format format --in-place` on demand.

Persnicket has no compile-time dependencies beyond the Swift toolchain itself — no `swift-syntax` tree to build, no binary artifacts to download. The version of `swift-format` it uses is always the one shipping with the active Swift toolchain.

## Install

Add Persnicket to `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/HeirloomLogic/Persnicket", from: "2.0.0"),
],
```

Attach **Persnoop** to each target you want linted on every build:

```swift
.target(
    name: "MyTarget",
    plugins: [
        .plugin(name: "Persnoop", package: "Persnicket"),
    ]
)
```

In Xcode: **File → Add Package Dependencies**, paste the URL, then attach the plugin to a target under the target's **Build Phases → Run Build Tool Plug-ins**.

You don't need to declare Persnipe in any target — it's a command plugin, available package-wide once the dependency is added.

> If the package you're attaching Persnoop to **publishes a product** others depend on, don't attach it unconditionally — that leaks Persnicket into every consumer's graph. See [Keeping Persnoop dev-only in a published package](#keeping-persnoop-dev-only-in-a-published-package).

## Persnoop vs. Persnipe — which to use

- **Persnoop** for *visibility*: lints on every build and surfaces violations as **build warnings** (inline in Xcode). It never fails the build — `swift-format lint` only exits non-zero in `--strict` mode, and a failing pre-build step would block compilation. For hard enforcement, run `swift-format lint --strict` directly in CI (see the CI section).
- **Persnipe** for *reformatting*: run it on demand to rewrite files in-place. Use when you want to bulk-fix existing code or fix a single file's formatting.

They aren't mutually exclusive. A common pattern is Persnoop attached to every target plus Persnipe available for quick reformats.

## Running Persnipe

From the command line at the package root:

```bash
swift package plugin --allow-writing-to-package-directory format-source-code
```

The `--allow-writing-to-package-directory` flag is required because Persnipe edits files in place. The plugin runs silently on success — diff with `git diff` to see what changed.

In Xcode: **right-click the project or package in the navigator → Persnipe**.

## Configuration

Persnicket looks for a `.swift-format` file in the **package root**. If one is found, both Persnoop and Persnipe use it. If not, Persnicket falls back to its own embedded opinionated config (the same one published in the Persnicket repo).

There are two clean ways to materialize a `.swift-format` file. **Offer both to the user** rather than picking silently — the choice meaningfully affects how strict the linter will be:

### Option A — vanilla `swift-format` default

A permissive starting point you'll tune from. Good if you want minimal style enforcement or you intend to handpick rules.

```bash
# macOS
xcrun swift-format dump-configuration > .swift-format

# Linux
swift-format dump-configuration > .swift-format
```

### Option B — Persnicket's opinionated config

The same strict config the plugin's embedded fallback enforces. Good if you just want the defaults Persnoop already gives you, but materialized so you can read and tweak it.

```bash
curl -fsSL https://raw.githubusercontent.com/HeirloomLogic/Persnicket/main/.swift-format -o .swift-format
```

What the opinionated config enforces (highlights):

- 4-space indentation, 120-character line length
- `OrderedImports`, trailing commas on multi-element collections
- `NeverForceUnwrap`, `NeverUseForceTry`, `NeverUseImplicitlyUnwrappedOptionals`
- `AllPublicDeclarationsHaveDocumentation`, `ValidateDocumentationComments`
- `FileScopedDeclarationPrivacy` set to `private`
- `UseEarlyExits`, `OmitExplicitReturns`, `UseShorthandTypeNames`

## Keeping Persnoop dev-only in a published package

If your package **publishes a product** (a library or plugin others depend on), attaching Persnoop to its targets leaks Persnicket into every downstream consumer's graph — forcing them to resolve and run your dev-only linter just to build. (This is specific to build-tool plugins on a published target; command plugins like Persnipe don't carry downstream.) Apps at the top of their graph aren't affected.

The fix is to gate the dev dependency and the `Persnoop` attachments in `Package.swift` on a gitignored `.dev-tooling` sentinel file — present only in a maintainer's clone and in CI:

```swift
let isDevBuild = FileManager.default.fileExists(atPath: devSentinel)
let devPlugins: [Target.PluginUsage] = isDevBuild ? [.plugin(name: "Persnoop", package: "Persnicket")] : []
```

Consumers evaluate a clean, plugin-free manifest; maintainers `touch .dev-tooling` to keep lint-on-build. There's one sharp edge — SwiftPM caches the evaluated manifest by its *text*, so toggling the sentinel after a build needs `swift package purge-cache` (not `reset`). See **`references/dev-only-gating.md`** for the full `Package.swift` recipe, the CI delta, the cache gotcha, and the `CONTRIBUTING.md` note.

## Requirements

- **Swift 6.0+** toolchain that includes `swift-format`.
- **macOS**: Xcode 16+. The plugin invokes `swift-format` via `/usr/bin/xcrun`, which resolves to the binary in the active Xcode toolchain.
- **Linux**: any Swift 6.0+ toolchain. Persnicket auto-discovers `swift-format` in this order:
  1. `$SWIFT_FORMAT` environment variable, if set to an absolute path.
  2. Sibling of `swift` on `$PATH` (the canonical location for toolchain installs).
  3. `/usr/local/bin/swift-format`, then `/usr/bin/swift-format`.
  4. `swift-format` directly on `$PATH`.

Setting `$SWIFT_FORMAT` is the override path for non-standard layouts. If discovery fails, Persnicket emits a clear error listing every path it checked rather than failing with a cryptic `env: 'swift-format': No such file or directory`.

## CI

For CI lint workflows, **invoke `swift-format lint --strict` directly** rather than going through the SwiftPM plugin. Reasons:

- Exit code drives job pass/fail with no extra wiring.
- No plugin build cost on every CI run.
- Lets you pair with a GitHub problem matcher so violations render as inline PR annotations.

Persnicket ships `bin/ci-lint-setup`, which (a) copies a default `.swift-format` into the project root if you don't have one, (b) installs the problem matcher at `.github/swift-format-matcher.json`, and (c) emits the `::add-matcher::` workflow command so violations annotate the PR diff. The script is idempotent and never overwrites an existing project `.swift-format`.

See **`references/ci-workflow.md`** for the full macOS workflow YAML, the Linux delta, problem matcher details, and known annotation caveats.

## What this skill is not

This skill wires Persnicket into a downstream app. It doesn't pick `swift-format` rules for you (that lives in your `.swift-format`), and it doesn't substitute for actually running the linter. For the full `swift-format` rule catalog, see the [swift-format rule documentation](https://github.com/swiftlang/swift-format/blob/main/Documentation/RuleDocumentation.md).
