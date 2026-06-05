# Keeping Persnoop Dev-Only in a Published Package

How to lint your own code with **Persnoop** without forcing the packages that depend on you to inherit Persnicket. This matters only if your package **publishes a product** (a library or plugin others depend on). An app that sits at the top of its dependency graph leaks nothing — none of this applies, and the plain [install steps](../SKILL.md#install) are all you need.

## The problem

Persnoop is a SwiftPM **build-tool plugin**. Attaching it to a target makes Persnicket a *hard dependency of that target*: SwiftPM must resolve Persnicket and run the linter as a pre-build step before the target compiles.

That's exactly what you want locally. But when the target belongs to a published product, the dependency travels: every downstream consumer resolves Persnicket into their graph and runs your dev-only `swift-format` linter just to build — a tool they never asked for and shouldn't have to trust. Linting is a maintainer concern; it has no business in a consumer's build.

## What actually leaks (and what doesn't)

Be precise about the failure mode, because not every dev dependency behaves the same way:

- **Build-tool plugins attached to a published target carry downstream and force execution.** This is the real harm. Persnoop is one; a SwiftLint build-tool plugin would be another. Any plugin in a target's `plugins:` list runs in the consumer's build.
- **Command plugins are attached to no target and force nothing.** Persnicket's own **Persnipe** (`format-source-code`) and `swift-docc-plugin` are command plugins. A consumer never runs them as a side effect of building, so they don't create the forced-linter problem.
- **Plain `.package` dependencies don't force execution, but still bloat the resolved graph.** Even a dependency no target uses gets pulled into the consumer's `Package.resolved`. That's graph noise, not a forced tool — but it's tidy to remove it too.

So the gate below has two jobs: it *must* remove build-tool plugin attachments (the forced linter), and it *may as well* remove the dev-only `.package` lines (graph hygiene). Fold both into one switch.

## The pattern — a gitignored `.dev-tooling` sentinel

SwiftPM has no first-class notion of a dev-only dependency. The workaround: gate the dev dependencies and plugin attachments in `Package.swift` on the presence of a sentinel file that exists only in a maintainer's working clone (and in CI), never in a consumer's checkout.

```swift
// swift-tools-version: 6.1

import PackageDescription
import Foundation

// Dev-only tooling (the Persnoop swift-format linter) must not leak into downstream
// consumers' dependency graphs. SwiftPM has no first-class dev-dependencies, so gate
// it on a gitignored `.dev-tooling` sentinel, present only in this package's own
// working clone (and created as a step in CI). `#filePath` anchors the lookup to this
// manifest's directory, independent of the current working directory.
let packageDir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
let devSentinel = packageDir.appendingPathComponent(".dev-tooling").path
let isDevBuild = FileManager.default.fileExists(atPath: devSentinel)

let devDependencies: [Package.Dependency] = isDevBuild
    ? [
        .package(url: "https://github.com/HeirloomLogic/Persnicket", from: "2.0.0"),
    ]
    : []

let devPlugins: [Target.PluginUsage] = isDevBuild
    ? [.plugin(name: "Persnoop", package: "Persnicket")]
    : []

let package = Package(
    name: "MyLibrary",
    products: [
        .library(name: "MyLibrary", targets: ["MyLibrary"]),
    ],
    dependencies: devDependencies,
    targets: [
        .target(
            name: "MyLibrary",
            plugins: devPlugins
        ),
    ]
)
```

The shape that matters:

- **`import Foundation`** — `Package.swift` is ordinary Swift, so `URL` and `FileManager` are available.
- **`#filePath` anchors the lookup to the manifest's own directory**, so the sentinel is found whether you build from the package root, a parent directory, or Xcode.
- **`isDevBuild` is the single switch.** Both `devDependencies` and `devPlugins` collapse to empty arrays when the sentinel is absent — a consumer evaluates a clean, single-product manifest with no Persnicket anywhere.
- **Wire `dependencies: devDependencies`** at the package level and **`plugins: devPlugins`** on *every* target you'd otherwise have attached Persnoop to. Miss one target and that target still leaks.

If you also have dev-only `.package` lines that aren't build-tool plugins (a docs plugin, say), add them to `devDependencies` for the graph-hygiene reasons above.

## gitignore the sentinel

The sentinel must never be committed — committing it would defeat the gate and ship the dev dependency to everyone who clones a tag.

```gitignore
.dev-tooling
```

## Enable it locally

Create the sentinel once, **before your first build**, so the first manifest evaluation picks it up (see the cache caveat below for why "first" matters):

```sh
touch .dev-tooling
```

That's the whole setup. Linting then runs on every `swift build`, identically in Xcode, the command line, and Conductor — no environment variables, no `launchctl`. Without the sentinel, your build mirrors a consumer's: no Persnicket, no linting.

## Enable it in CI

CI is just another maintainer build — it creates the sentinel as a step before resolving. Against the workflow in [`ci-workflow.md`](./ci-workflow.md), the only change is one line at the top of the lint job:

```yaml
      - name: Setup swift-format lint
        run: |
          touch .dev-tooling
          swift package resolve
          .build/checkouts/Persnicket/bin/ci-lint-setup
```

Add the same `touch .dev-tooling` to any other maintainer job that needs the dev dependencies (for example a DocC build job, if you gate a docs plugin the same way).

## Caveats — the manifest-cache gotcha

This is the sharp edge. **SwiftPM caches the evaluated manifest keyed on `Package.swift`'s *text*.** The manifest text is byte-identical whether or not the sentinel exists — the file it reads is *external* to the manifest. So once SwiftPM has evaluated and cached the manifest, creating or deleting `.dev-tooling` changes nothing: you keep whichever mode was evaluated first, no matter how many times you rebuild.

If you add the sentinel *after* a build has already cached the consumer-mode manifest, you must clear that one cache layer:

- **Command line:** `swift package purge-cache`, then `swift package resolve`. The re-resolve reconciles `Package.resolved` for you.
- **Xcode:** quit Xcode, run `swift package purge-cache`, then reopen `Package.swift`. If stale dependencies linger, nudge a re-resolve with **File → Packages → Resolve Package Versions**. (Deleting DerivedData / `Package.resolved` also works but is rarely necessary.)

Note what does **not** clear this layer: `swift package reset` and Xcode's **Reset Package Caches** both leave the evaluated-manifest cache intact. `purge-cache` is the specific verb.

A fresh clone that runs `touch .dev-tooling` before its very first build sidesteps all of this — the first (and only) evaluation already sees the sentinel. Because `Package.resolved` is itself gitignored in a published package, this churn is entirely local; toggling the sentinel never reaches a consumer.

## Document it for contributors

A contributor who clones and runs `swift build` without the sentinel builds in consumer mode and sees **no lint warnings** — then submits a PR that fails CI. Pre-empt that in `CONTRIBUTING.md`:

- Tell contributors to run `touch .dev-tooling` once, before their first build.
- Document the `swift package purge-cache` reset for anyone who built before creating the sentinel.

This is what [Tightlip PR #13](https://github.com/heirloomlogic/Tightlip/pull/13) did, and it's the difference between the gate being invisible plumbing and a recurring "why didn't lint run for me" question.
