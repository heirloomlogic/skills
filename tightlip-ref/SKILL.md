---
name: tightlip-ref
description: Setup and code patterns for Tightlip — a SwiftPM build-tool plugin that injects secrets into a Swift app at compile time via a generated `Secrets` enum. Use when integrating Tightlip into a new app, adding or renaming a secret, configuring per-environment keys (staging vs. production), debugging Lipservice build failures, placing `Secrets.yml`, or referencing `Secrets.<key>` in Swift code. Activate on "Tightlip", "Lipservice", "Secrets.yml", "TIGHTLIP_ENV", "build-time secrets", ".zshenv API key", or when a project's Package.swift depends on Tightlip.
---

# Tightlip Reference

Tightlip is a SwiftPM build-tool plugin (`Lipservice`) that reads a `Secrets.yml` config plus environment variables at **build time** and emits a `nonisolated enum Secrets` compiled into the consuming target. No runtime initialization, no dependency injection, no async — call sites just read `Secrets.myKey` as a `String`. Plaintext literals never appear in the binary (XOR-obfuscated against a deterministic salt), and the config file is the only thing that lives in source control. Real values come from the developer's shell env (default `~/.zshenv`) or CI's `env:` block.

This skill captures setup, the `Secrets.yml` grammar, environment selection, and the common failure modes.

## Setup

### SwiftPM target

Add the package dependency:

```swift
// Package.swift
.package(url: "https://github.com/heirloomlogic/Tightlip", from: "1.0.0"),
```

Attach the plugin to the target that needs secrets:

```swift
.target(
    name: "MyApp",
    plugins: [.plugin(name: "Lipservice", package: "Tightlip")]
)
```

Place `Secrets.yml` at the target's **source root**: `Sources/MyApp/Secrets.yml`.

### Xcode project (no Package.swift)

1. `File > Add Package Dependencies…` → paste `https://github.com/heirloomlogic/Tightlip` → Dependency Rule **Up to Next Major** from `1.0.0`. (`Add Local…` works for vendored checkouts.)
2. Target → `Build Phases > Run Build Tool Plug-ins` → add **Lipservice**.
3. Place `Secrets.yml` at `<ProjectRoot>/<TargetName>/Secrets.yml` — the directory next to `.xcodeproj`. `<TargetName>` is the target's **display name**, and the path is resolved on the filesystem; the file's position in the Project Navigator is irrelevant. For a stock app template, this is the existing `<TargetName>/` folder.
4. Reference anywhere in the target: `Secrets.revenueCatAPIKey`.

### Caller imports nothing

Downstream code does **not** `import Tightlip`. The plugin generates a file (`Tightlip.swift`) into the build directory; it's compiled into the same module as the target, so `Secrets` is in scope automatically.

## `Secrets.yml` formats

Two formats. The parser auto-detects from the first non-comment line.

### Flat (single environment)

```yaml
# Secrets.yml
revenueCatAPIKey: REVENUECAT_API_KEY
hmacSigningKey:   HMAC_KEY
```

Left side becomes a static property on `Secrets`. Right side names an env var resolved at build time.

### Sectioned (multi-environment)

```yaml
# Secrets.yml
staging:
  revenueCatAPIKey: STAGING_REVENUECAT_API_KEY
  hmacSigningKey:   STAGING_HMAC_KEY

production:
  revenueCatAPIKey: PROD_REVENUECAT_API_KEY
  hmacSigningKey:   PROD_HMAC_KEY
```

Each top-level identifier followed by `:` (no value) opens a section. Section bodies indent **exactly 2 spaces**. All sections must declare the same set of property names — adding `hmacSigningKey` to `production` only is a parse error.

### Grammar rules (strict, on purpose)

- Identifiers (both sides): `[A-Za-z_][A-Za-z0-9_]*`. No quoting, no dashes, no dots.
- Comments: `#` at the **start of a line** only. Inline comments after a value are not supported.
- Tabs are rejected anywhere — they're a common paste artifact.
- Flat mode: no leading whitespace on mapping lines.
- Sectioned mode: section headers at column 1, content at exactly 2 spaces.
- Duplicate keys, empty files, and anything else are parse errors with a line number.

Every declared secret is **required** at build time. If an env var is unset, the build fails pointing at the missing variable. For truly optional values, read `ProcessInfo` at runtime instead of declaring them in `Secrets.yml`.

### Naming convention

Prefix every env var with an app tag in screaming snake case — `<APP_PREFIX>_<SECRET>` (e.g. `ACME_REVENUECAT_API_KEY`). The plugin doesn't enforce it; the convention just keeps configs from colliding across apps on the same dev machine.

## Environment selection (sectioned configs)

The plugin picks one section in this order:

1. **`TIGHTLIP_ENV`** — if set, must match a section name exactly. Highest priority.
2. **Automatic inference** — when **exactly two sections** exist and **one is named `prod` or `production`**:
   - `CONFIGURATION=Release` (Xcode) → the `prod`/`production` section.
   - Anything else (Debug, unset) → the other section.
3. **Error** otherwise (3+ sections, or two non-prod-named sections). The build fails listing available environment names.

Flat configs have no environment concept and ignore all of this.

**Recommended setup:**

- **Local dev:** add `export TIGHTLIP_ENV=staging` to `~/.zshenv`, or rely on Debug builds inferring the non-production section.
- **CI release lane:** set `TIGHTLIP_ENV=production`, or rely on `CONFIGURATION=Release` if building through `xcodebuild`.
- **3+ environments (qa, uat, staging, prod):** always set `TIGHTLIP_ENV` explicitly — inference only works for the two-section prod/non-prod case.

## Where env vars come from

The plugin sources `~/.zshenv` in a clean `zsh -f` subshell, captures the result, and merges with `ProcessInfo.processInfo.environment` (the build's own env). **`ProcessInfo` wins on conflict**, so Xcode Scheme env vars and CI runners override `~/.zshenv` without ceremony.

This works identically whether the build launched from Xcode.app, Conductor, VS Code, or `xcodebuild` from Terminal — eliminating the "works in shell, not in Xcode" class of bug.

On CI (no `~/.zshenv`), the tool quietly falls back to `ProcessInfo`. Sourcing failures and timeouts (5 s default) also fall back, with a single `note:` to stderr.

### Custom env file

Add a top-level `envFile:` directive **before any secret declaration**. Tilde-expanded against `$HOME`; relative paths resolve against the config's directory.

```yaml
envFile: ~/.bash_profile
revenueCatAPIKey: REVENUECAT_API_KEY
```

| Shell | Recommended path | Notes |
|---|---|---|
| zsh | `~/.zshenv` *(default — directive can be omitted)* | Sourced cleanly with `zsh -f` |
| bash | `~/.bash_profile` or `~/.bashrc` | `export` syntax is zsh-compatible |
| fish | `~/.config/tightlip.env` *(sidecar)* | Fish syntax isn't zsh-compatible — keep a file of `export KEY=value` lines |
| nushell / xonsh / etc. | `~/.tightlip.env` *(sidecar)* | Same sidecar pattern as fish |

The directive is recognized **only** as the first non-blank, non-comment line. Anything after a section header or mapping is parsed as a secret declaration.

## Using secrets in code

```swift
let client = RevenueCat(apiKey: Secrets.revenueCatAPIKey)
let signature = Crypto.sign(data: payload, key: Secrets.hmacSigningKey)
```

- `Secrets` is `nonisolated enum`; properties are `String`. No actor hops, no async, no init.
- Properties are emitted in alphabetical order. The enum name is always `Secrets`.
- The stored bytes are XOR-obfuscated against a 32-byte salt derived deterministically from the resolved values — identical inputs produce byte-identical output, which avoids spurious downstream recompiles.
- Plaintext never lands in the binary; `strings` against the shipped `.app` won't surface the values.

## Common task: adding a new secret

1. **Export the env var** in `~/.zshenv` (or wherever your `envFile` points):
   ```sh
   export ACME_NEW_THING_KEY="..."
   ```
   `source ~/.zshenv` (or restart Xcode / the build host) so the next build sees it.
2. **Add the line** to `Secrets.yml`:
   ```yaml
   newThingKey: ACME_NEW_THING_KEY
   ```
   For sectioned configs, add the property to **every** section (parse error otherwise) and set every corresponding env var.
3. **Build.** Lipservice regenerates `Tightlip.swift` automatically.
4. **Reference** as `Secrets.newThingKey`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `error: environment variable X must be set to generate Secrets.Y` | Env var unset in both sourced file and `ProcessInfo`. | Confirm the export in your `envFile` (default `~/.zshenv`). Check the `note:` line for similarly-named vars — usually a typo. Re-source / restart Xcode. |
| `note: sourcing /path/to/file ... using process environment only` | The `zsh -f` subshell sourcing your env file failed or timed out (5 s). | Reproduce with `zsh -f -c 'source <yourEnvFile>'`. Common culprits: `mise`/`asdf` inside `.zshenv` hitting sandbox, or `.zshenv` doing >5 s of work. Keep `.zshenv` cheap. |
| `error: cannot determine environment: ...` | Sectioned config with no `TIGHTLIP_ENV` and inference can't resolve (3+ sections, or two non-prod-named sections). | Set `TIGHTLIP_ENV` to one of the listed section names — in the scheme, on the CI job, or in `~/.zshenv`. |
| `error: Secrets.yml:N: ...` | Parse failure. | Check line N against the [Grammar rules](#grammar-rules-strict-on-purpose). Almost always: a tab character, a quoted value, nested indentation, or an inline `# comment` after a value. |
| `error: sections must declare the same properties` | A sectioned config has a property in one section but not another. | Add the missing property to every section (and export every corresponding env var), or remove it everywhere. |
| Plugin doesn't regenerate after changing an env var | The plugin's input-tracking didn't see a change, or you're looking at a stale build. | `xcodebuild clean` (or Product → Clean Build Folder) to force regeneration. |
| `Secrets` is "unresolved identifier" at the call site | Plugin not attached to this target, or `Secrets.yml` not at the expected path. | Xcode: confirm Lipservice is under Build Phases → Run Build Tool Plug-ins. SwiftPM: confirm the `.plugin(...)` line is on this target. Confirm `Secrets.yml` path (see [Setup](#setup)). |
| Works locally, fails on CI with "missing env var" | CI doesn't have your `~/.zshenv`. | Set the var in the CI job's `env:` block (or whatever your runner uses). `ProcessInfo` is read directly; no sourcing needed. |

## Constraints and gotchas

- **Plugin runs on macOS** (Package.swift declares `.macOS(.v10_15)`). This constrains the **build host**, not the consuming target — a downstream iOS/tvOS/watchOS app target can use Tightlip just fine; only the Mac doing the build needs macOS 10.15+.
- **Build-time only.** The generated `Secrets` enum is a compile-time constant. There is no runtime reload, no remote config, no rotation without rebuilding. For dynamic values, use a runtime config service.
- **Required ≠ optional.** Every key in `Secrets.yml` must resolve at build time. Optional values belong in `ProcessInfo` at runtime, not in this file.
- **Generated file is a build artifact**, not source. Don't check in `Tightlip.swift`; it's regenerated on every build into the plugin's work directory.
- **Don't `import Tightlip`** from app code — the package's only product is the `Lipservice` build plugin. The generated `Secrets` enum lives in your target's own module.

## When to use what

| Task | Action |
|---|---|
| First-time integration in a Package.swift target | Add `.package(...)` + `.plugin(name: "Lipservice", ...)`, drop `Secrets.yml` at `Sources/<Target>/Secrets.yml`, export env vars in `~/.zshenv` |
| First-time integration in an Xcode-only project | Add Package Dependency, attach Lipservice under Build Phases, drop `Secrets.yml` at `<ProjectRoot>/<TargetName>/Secrets.yml` |
| Add an API key | Export in `~/.zshenv`, add line to `Secrets.yml`, rebuild, reference `Secrets.<name>` |
| Different keys per env | Convert `Secrets.yml` to sectioned, set `TIGHTLIP_ENV` (or rely on `prod`/`production` inference for the two-env case) |
| CI release lane | Set the env vars in the runner's `env:` block; set `TIGHTLIP_ENV=production` (or build with `CONFIGURATION=Release`) |
| Non-zsh shell on dev's machine | Add `envFile: ~/.your-file` to the top of `Secrets.yml`; keep the file in `export KEY=value` syntax |
| Rotate a key | Update the env var, rebuild. (Source control of `Secrets.yml` doesn't change.) |
| Stop tracking a key | Remove the line(s) from `Secrets.yml` and any call sites. The env var can stay exported harmlessly. |
| Runtime/dynamic value | Don't use Tightlip — read `ProcessInfo` or a runtime config service. Tightlip is compile-time only. |
