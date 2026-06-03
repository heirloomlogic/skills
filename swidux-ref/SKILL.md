---
name: swidux-ref
description: Architecture rules and code templates for Swidux — a Redux-style state-management library for SwiftUI — and its provider-agnostic service layer (analytics, paywall) and SwiftData persistence layer. Use when writing Swidux apps, adding actions or reducers, wiring plugins (Persistence, Undo, Killswitch, ParentalGate, Paywall, Analytics, FeatureFlags), setting up local or iCloud/CloudKit persistence (SwiduxPersistence, SwiduxCloudKitSync, the @Persisted macro), or integrating third-party services like Mixpanel or RevenueCat through their Swidux adapter packages. By default app development runs on the SDK-free in-repo dev services (ConsoleAnalyticsService, SimulatedPaywallService, SwiduxDevPaywallUI) so the vendor decision can be deferred indefinitely; persistence starts local-only (no iCloud entitlements) and adds iCloud sync only when needed. Activate on "Swidux", "@Swidux", "AppStore", "AppReducer", "EntityStore", "killswitch", "paywall", "parental gate", "AnalyticsService", "PaywallService", "ConsoleAnalyticsService", "SimulatedPaywallService", "devPaywall", "SwiduxDevPaywallUI", "MixpanelAnalyticsService", "RevenueCatPaywallService", "SwiduxPersistence", "SwiduxCloudKitSync", "@Persisted", "PersistenceCoordinator", "SyncCoordinator", "EntityDB", "iCloud sync", "CloudKit sync", "SwiftData persistence".
---

# Swidux Reference

Swidux is a Redux-style state-management library for SwiftUI. State lives in one observable store; mutations go through reducers; side effects run as async closures. Macros generate observability boilerplate; plugins handle persistence, undo, paywalls, killswitches, parental gates, analytics, and feature flags. Third-party services (Mixpanel, RevenueCat, …) are accessed through their dedicated Swidux adapter packages — never imported into app code directly.

**Default posture: develop with no vendor.** Because app code only ever speaks the protocol (`AnalyticsService`, `PaywallService`), the recommended way to build a Swidux app is to do the bulk of development on the SDK-free in-repo dev services — `ConsoleAnalyticsService` (logs every analytics call) and `SimulatedPaywallService` + `SwiduxDevPaywallUI` (a fully driveable paywall). The app stays light (no SDK, no API keys, no vendor account), yet every analytics and paywall marker is exercised end to end through the real plugin pipeline. Adopting Mixpanel/RevenueCat later is the same two-line swap in `Store.configured()` as swapping any provider — so the vendor decision can be deferred indefinitely rather than made up front.

This skill captures the rules, conventions, and dispatch lifecycle. Code templates are in `references/swidux-patterns.md`. Full wiring walkthroughs for the analytics and paywall layers — including the protocol/adapter layering and provider-swap recipe — are in `references/swidux-analytics.md` and `references/swidux-paywall.md`.

## The 11 architecture rules

### 1. State is a `nonisolated` struct annotated with `@Swidux`

```swift
@Swidux
nonisolated struct AppState: Equatable, Sendable {
    var items: EntityStore<Item> = .init()
    @Slice var ui: UIState = .init()
}
```

The macro emits an `@Observable` companion class (`AppStateObserver`) and a `SwiduxObservable` extension with `init(observer:)`, `makeObserver(from:)`, `apply(_:to:)`, and `applyRestore(from:to:)`. Don't hand-write the observer. Mark nested struct properties with `@Slice` so they get their own observer class for per-property observation.

### 2. Actions are `Sendable` enums, never `async` and never `throws`

```swift
enum AppAction: Sendable {
    case items(ItemAction)
    case selectItem(UUID?)
}
```

Async work lives in effects, not in actions. Action cases describe events and intents; the reducer translates them into state mutations and optional effects.

### 3. Reducers are pure and synchronous

```swift
struct AppReducer: SwiduxReducer {
    func reduce(state: inout AppState, action: AppAction, environment: AppEnvironment) -> Effect? {
        switch action {
        case .selectItem(let id):
            state.ui.selectedItemID = id
            return nil
        }
    }
}
```

Mutate state in place. Return `Effect?` — `nil` if no async work, or a closure that does I/O and dispatches follow-up actions. Never call `await` from inside a reducer body. Never throw.

### 4. Effects run off the MainActor; sends hop back

```swift
typealias Send = Swidux.Send<AppAction>      // @MainActor @Sendable (AppAction) -> Void
typealias Effect = Swidux.Effect<AppAction>  // @Sendable (Send) async -> Void
```

The `Store` runs effects with `Task { @concurrent in }` to keep them off the MainActor. The `send` callback inside an effect is `@MainActor`, so dispatching back happens on MainActor automatically. Specialize `Send` and `Effect` once for your `AppAction`.

### 5. The store is a typealias and an extension

```swift
typealias AppStore = Store<AppState, AppAction>

extension Store where State == AppState, Action == AppAction {
    static func configured(environment: AppEnvironment = .live()) -> AppStore { … }
}
```

Don't subclass `Store`. Compose it through a configuration extension that registers plugins and returns the wired instance.

### 6. Plugins are the single extension point

The `SwiduxPlugin` protocol has four hooks (all default no-op):

| Hook | When | Use for | Returns |
|---|---|---|---|
| `willReduce(state:action:)` | Before app reducer | Snapshots, pre-mutation analytics | `Void`, read-only state |
| `reduce(state:action:) -> Effect?` | After app reducer | Domain logic, async work | Optional effect |
| `afterReduce(state:action:)` | After all reducing | Persistence drain, logging | `Void` |
| `flush() async` | App shutdown | Drain async buffers | `Void` |

**Core middleware** (`PersistencePlugin`, `UndoPlugin`) is action-agnostic — works with any app, no wiring beyond construction. **Domain plugins** (`KillswitchPlugin`, `ParentalGatePlugin`, `PaywallPlugin`, `AnalyticsPlugin`, `FeatureFlagsPlugin`) own a state slice and action enum and require keypath + action lifter + extractor.

Domain plugins backed by an external service (Killswitch, Paywall, Analytics) take a `service:` parameter typed as the protocol (`KillswitchService`, `PaywallService`, `AnalyticsService`) — never an SDK type. The protocol/adapter layering is rule #11.

### 7. The dispatch lifecycle is fixed

For every `store.send(action)`:

```
1. pack:        observer tree → state struct snapshot
2. willReduce:  plugins observe pre-state (UndoPlugin snapshots here)
3. reducer:     app reducer mutates state, may return Effect
4. plugins.reduce: domain plugins handle their actions, may return Effects
5. afterReduce: plugins observe post-state (PersistencePlugin drains here)
6. unpack:      diff state vs observer tree, assign only changed properties
7. effects:     each Effect runs in Task { @concurrent in }
```

Per-property observation is preserved by step 6: only changed properties are written back to the observer tree, so SwiftUI views only re-render the parts they read.

### 8. Persistence is declare-and-register via `@Persisted` + `PersistenceCoordinator`

The recommended path is `SwiduxPersistence`. Annotate a domain entity with `@Persisted` — the macro generates its SwiftData `@Model` shadow, the value↔model converters, and `PersistableEntity` conformance — then register an `EntityStore` keypath with a coordinator that reuses the core `PersistencePlugin`:

```swift
@Persisted
nonisolated struct Card: Identifiable, Equatable, Sendable { var id: UUID; var quote: String }

// In Store.configured() (now async, because hydration awaits disk):
let container = try! ContainerFactory.makeLocalContainer(models: [CardModel.self])
let persistence = PersistenceCoordinator<AppState, AppAction>(
    entities: [.entity(\.cards)],
    container: container
)
plugins.register(persistence.corePlugin)         // register UndoPlugin first if used
var initial = AppState()
await persistence.hydrate(into: &initial)         // first-load only
```

You write no `StateWriter` body, no `@Model`, no DB actor. `EntityStore.modify(_:_:)`, `removeAll(where:)`, and `sort(by:)` track changes; the plugin debounces and batches them. You never call `save()` from a reducer — reducers stay pure, persistence is observed. Flush on background: `Task { await persistence.corePlugin.flush() }`. Full walkthrough (markers, multiple entities, CloudKit) in `references/swidux-persistence.md`.

**`@Persisted` is for entities; `@Swidux` is for state containers** — different layers, never the same type.

**Generated models are CloudKit-safe by construction** — which is what lets the same model back both local and synced containers. Non-optional mirrored attributes get a default (your domain default if present, else a canonical primitive default), relationships are generated optional, and `@Inline` blobs default to `Data()`. The two cases the macro can't auto-fix are compile errors: a non-optional, non-primitive property (custom `Codable`, `URL`, enum) with no default and no `@Inline` → `mirrorRequiresDefault` (give it a default, make it optional, or mark `@Inline`); a non-optional to-one `@Relation` → `relationRequiresOptional` (make it `T?`). Full rules in `references/swidux-persistence.md`.

**`hydrate` vs `rehydrate` — the merge rule, enforced by the API.** `hydrate(into:)` is first-load only: it *replaces* each `EntityStore` from disk, safe before any live edits exist. `rehydrate(into:)` is the only post-launch refresh path, and it *always merges* preferring in-memory values. Once past launch, in-memory state is authoritative — it may hold unflushed writes in the debounce window or in-progress edits bound to live UI. A wholesale replace silently clobbers them and surfaces as dropped keystrokes / lost edits. The coordinator exposes only `rehydrate` for refresh, so the rule is enforced by construction — no merge closure to remember.

This neutralizes the classic CloudKit trap: `.NSPersistentStoreRemoteChange` fires for the app's **own** local saves, not just remote-device imports, so a "re-hydrate on remote change" observer feeds the app its own writes. Because `rehydrate` merges, that's a no-op instead of visible data loss — `SwiduxCloudKitSync`'s `RemoteChangeObserver` is built on exactly this.

**Linking `SwiduxCloudKitSync` is the single signal the app needs the iCloud/CloudKit/Push entitlement family.** A local-only app links only `SwiduxPersistence` and needs none of them. Both the local and sync wiring — and the Apple Developer portal setup — are in `references/swidux-persistence.md`.

**Low-level fallback.** The hand-wired `PersistencePlugin` + `StateWriter` closures + your own `@Model`/DB actor (see `references/swidux-patterns.md` and DocC `PersistenceMiddlewareGuide`) still works — reach for it only when you need control the macro can't express.

**Scalar preferences (UserDefaults) use a different mechanism.** `EntityStore` is for collections of identifiable entities. For one-off scalar values (theme, sort order, last-seen version), inject a `KeyValueStore` through `Environment`, declare type-safe keys on `KVKey`, hydrate state at startup, and write from effects:

```swift
nonisolated extension KVKey where Value == Theme {
    static let theme = KVKey<Theme>("theme")
}

struct AppEnvironment: Sendable {
    var keyValue: any KeyValueStore  // production: UserDefaultsKeyValueStore or KeychainKeyValueStore

    static func live() -> Self { .init(keyValue: UserDefaultsKeyValueStore()) }
}

extension AppState {
    static func hydrated(from store: any KeyValueStore) -> AppState {
        AppState(theme: store.value(.theme) ?? .system)
    }
}

// Reducer arm — no try?, no throws. Encode errors are logged + assertionFailure in DEBUG.
case .themeChanged(let theme):
    state.theme = theme
    return { @Sendable _ in
        environment.keyValue.setValue(theme, for: .theme)
    }
```

Under `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`, any decl reached from the macro's nonisolated reconstruction or from `static func hydrated(from:)` must itself be nonisolated — hence `nonisolated extension KVKey …` above, and `nonisolated func` on any free helper that hydration and a reducer share (e.g. a `clampScale` used by both `UIState.hydrated` and the reducer; keep it `internal`, not `private`, so both files reach it). This is a property of *what reads the decl*, not a blanket "annotate everything."

Reads are for **hydration only** — don't read from a reducer mid-cycle. Tests inject `InMemoryKeyValueStore`. Choose `KeychainKeyValueStore` when the value should survive app reinstall (anonymous device IDs are the canonical case — see "Identity for analytics" below, including the fixed macOS entitlement answer); `UserDefaultsKeyValueStore` for everything else. Values are JSON-encoded as `Data`, so `@AppStorage` cannot observe them (intentional — Swidux state is the source of truth).

### 9. Undo is opt-in via `UndoPlugin`

```swift
let undoPlugin = UndoPlugin<AppState, AppAction>(
    isUndoable: { action in
        if case .items(.add) = action { return true }
        if case .items(.remove) = action { return true }
        return false
    },
    coalescing: { action in
        if case .items(.setName) = action { return true }  // collapse keystrokes
        return false
    }
)
```

`isUndoable` filters which actions snapshot. `coalescing` collapses bursts of the same action class into a single undo step (typically text edits). On macOS, hook `store.undo()` / `store.redo()` into `CommandGroup(replacing: .undoRedo)`.

### 10. Plugin registration order matters at the boundaries

```swift
let plugins = PluginHost<AppState, AppAction>()
plugins.register(undoPlugin)         // 1. snapshots in willReduce — must run before mutation
plugins.register(persistencePlugin)  // 2. drains in afterReduce — wants final state
plugins.register(killswitchPlugin)   // 3. domain plugins — relative order rarely matters
plugins.register(paywallPlugin)
plugins.register(parentalGatePlugin)
```

Undo first, persistence second, then domain plugins.

### 11. Third-party services are accessed only through their Swidux adapter

App code depends on the protocol (`AnalyticsService`, `PaywallService`, `KillswitchService`, …), never on the underlying SDK. The concrete adapter — `MixpanelAnalyticsService` from `SwiduxMixpanelAnalytics`, `RevenueCatPaywallService` from `SwiduxRevenueCatPaywall` — calls `Mixpanel.initialize` / `Purchases.configure` internally; the app never does.

Because app code is protocol-blind, the default `service:` during development is the SDK-free in-repo conformer — `ConsoleAnalyticsService` (`SwiduxAnalytics`) and `SimulatedPaywallService` (`SwiduxPaywall`) — not a vendor adapter. The "swap providers" change below is the *same* two-line change whether you're going dev-default → vendor (the first adoption) or vendor → vendor (Mixpanel → Amplitude); both are deferred, not foundational, decisions.

Vendor names appear in exactly two files: `Package.swift` (the dependency) and `App/AppStore.swift` (the service construction inside `Store.configured()`). For paywalls the one view that attaches the sheet is a third allowed site (`import SwiduxRevenueCatPaywallUI`). Everything else — `@main`, root view, feature views, reducers, environment, models — stays vendor-blind.

Swapping providers (Mixpanel → Amplitude, RevenueCat → StoreKit2) is a two-line change in `Store.configured()` plus the package swap. State slices, actions, reducer dispatches, gate checks, and analytics events are unchanged because they speak the Swidux types (`AnalyticsService`, `AnalyticsEvent`, `PaywallState`, `EntitlementSnapshot`). Any migration that touches more than these sites means the protocol has leaked — find it and push it back.

Full wiring in `references/swidux-analytics.md` and `references/swidux-paywall.md`.

## Domain plugin wiring shape

Every domain plugin (Killswitch, ParentalGate, Paywall, or your own) takes the same three keypath/closure pieces:

```swift
SomePlugin(
    state: \.someFeature,                                         // WritableKeyPath into AppState
    action: AppAction.someFeature,                                // (FeatureAction) -> AppAction
    extractAction: { if case .someFeature(let a) = $0 { return a }; return nil },
    …                                                              // plugin-specific service / source / etc.
)
```

This is the contract — plugins never assume your root types.

## Identity for analytics

`AnalyticsIdentity` closures run on every non-analytics dispatch. They must be cheap reads from state — never I/O. Hydrate identity once at launch into `AppState`, then point the keypath at it. Two shapes cover the common cases:

### App has user auth

```swift
@Swidux
nonisolated struct AuthState: Equatable, Sendable {
    var currentUserID: String? = nil
}

let analyticsIdentity = AnalyticsIdentity<AppState>(
    userID: \.auth.currentUserID,
    userProperties: { state in [:] }
)
```

Sign-in arm sets `currentUserID`; sign-out clears it. `nil → id` fires `service.identify`; `id → nil` fires `service.reset`. No manual `.analytics(.identify(...))` dispatch needed.

### App has no user auth (device-stable identity)

Use `KeychainKeyValueStore` (survives reinstall) to mint a UUID once and hydrate it into a non-optional `AppState.deviceID: String` in `Store.configured()`. The canonical read-or-mint helper lives in Swidux DocC under `KeyValueStoreGuide` → "Device-Identity Pattern" — don't reinvent the `SecItemCopyMatching` boilerplate locally.

```swift
// In Store.configured(), alongside UIState.hydrated(from:)
let kv = KeychainKeyValueStore(service: "com.example.myapp")
let deviceID = kv.value(.deviceID) ?? {
    let new = UUID().uuidString
    kv.setValue(new, for: .deviceID)
    return new
}()
let initial = AppState(deviceID: deviceID, ui: .hydrated(from: kv))

let analyticsIdentity = AnalyticsIdentity<AppState>(
    userID: \.deviceID,
    userProperties: { state in [:] }
)
```

Declare `var deviceID: String` on `AppState` (non-optional — it's always present after launch); the keypath form binds the `KeyPath<State, String>` `AnalyticsIdentity` init. Full walkthrough including the `KVKey<String>("device-id")` declaration, accessibility tuning, and test injection in `references/swidux-analytics.md` and the DocC `KeyValueStoreGuide`.

`KeychainKeyValueStore` never prompts the user (no Always Allow/Deny, no Touch ID / Face ID). The macOS entitlement answer is fixed, not a per-app decision: ship a provisioning-profile–signed build and leave `accessGroup: nil`; an unsigned local/CI build that fails the first write with `errSecMissingEntitlement` / `OSStatus` −34018 is a signing condition, not a prompt or a bug — add one team-prefixed `keychain-access-groups` entry. See `references/swidux-analytics.md` "macOS Keychain entitlement" and DocC `KeyValueStoreGuide`.

## SwiftUI integration rules

- App owns the store with `@State`: `@State private var store = AppStore.configured()`. Inject via `.environment(store)`. Never recreate the store in `body`.
- Views read via `@Environment(AppStore.self)` and dispatch with `store.send(.someAction)`.
- For form controls, prefer `store.binding(\.path.to.value) { .someAction($0) }` — a `KeyPath<State.Observer, Value>` plus an action constructor. Falls back to `Binding(get:set:)` when the read is transformed (optional unwraps, derived values) or the setter wraps the dispatch in animation/branching. Never let SwiftUI own the truth; the reducer does.
- Per-row observation: pass `store` (or a per-row binding into `EntityStore`) into a row view, and read inside that row. SwiftUI re-renders only what it reads.

## Conventions

- Re-export Swidux from `AppState.swift`: `@_exported import Swidux`. Other files don't need `import Swidux`. **But that re-export covers core Swidux only — not the domain plugin modules.** A view that reads a plugin-owned slice or dispatches a plugin action needs that module's own import: touch `store.analytics.*` / `AnalyticsAction` → `import SwiduxAnalytics`; touch `store.paywall.*` / `PaywallAction` → `import SwiduxPaywall`. Symptom if it's missing: `property 'isOptedOut' is not available due to missing import of defining module 'SwiduxAnalytics'`. Views that only touch app-module `UIState` / `UIAction` need nothing extra.
- File layout: `App/AppState.swift`, `App/AppAction.swift`, `App/AppReducer.swift`, `App/AppStore.swift`, `App/AppEnvironment.swift`, `App/Effect.swift`. Features go in `Features/<Feature>Reducer.swift`. Models in `Models/`.
- Tests use Swift Testing (`import Testing`, `@Test`, `#expect`), not XCTest.
- One reducer per feature; root reducer routes by case.
- Effects shouldn't capture mutable state. Capture services/closures from `environment`.

## When to use what

| Task | Tool |
|---|---|
| New struct field on AppState | Just add it; macro re-runs |
| New nested struct slice | `@Slice var slice: SliceState = .init()` |
| New mutation | New `AppAction` case + reducer arm |
| New async operation | Reducer returns an `Effect` that calls service and `await send(.someResult(…))` |
| Persist a new entity collection | `@Persisted` the entity (generates its `@Model` shadow), add `EntityStore<NewEntity>` to AppState, add `.entity(\.newEntities)` to `PersistenceCoordinator` (see `references/swidux-persistence.md`) |
| Add iCloud sync to a persisted app | Link `SwiduxCloudKitSync`, build the container via `CloudContainerFactory`, wire a `SyncCoordinator`; portal/entitlement setup in `references/swidux-persistence.md` |
| Add a Settings sync on/off toggle | `await sync.setSyncEnabled(isOn, into: &state)` returns the resolved `SyncStatus` (see `references/swidux-persistence.md`) |
| Refresh persisted data from disk / on a CloudKit remote change | `await persistence.rehydrate(into: &state)` — always merges; never `hydrate` (that replaces and clobbers live edits) |
| Persist a scalar preference (theme, last-seen version) | Inject `KeyValueStore` via `Environment`; hydrate at startup, write from an effect |
| Add undo for an action | Make `isUndoable` return `true` for that case |
| Block on app version | Wire `KillswitchPlugin` (see `references/swidux-patterns.md`); host the config via the shared ConfigWorker (`references/swidux-config-worker.md`) |
| Gate a feature on subscription | Check `store.paywall.isGateSatisfied`; otherwise dispatch `.paywall(.request(reason:))` (see `references/swidux-paywall.md`) |
| Develop/QA the paywall with no vendor yet (default) | Hold one shared `SimulatedPaywallService`; pass it to `Store.configured()` and `.devPaywall(state:service:onAction:)` from `SwiduxDevPaywallUI` — see `references/swidux-paywall.md` |
| Show the paywall sheet | Dev default: `.devPaywall(state:service:onAction:)` from `SwiduxDevPaywallUI`. Post-adoption: `.revenueCatPaywall(state: store.paywall) { store.send(.paywall($0)) }` from `SwiduxRevenueCatPaywallUI` |
| Develop analytics with no vendor yet (default) | Pass `ConsoleAnalyticsService()` as the plugin `service:` — every call logs to `os.Logger`, no SDK; see `references/swidux-analytics.md` |
| Track an analytics event | Return a named `AnalyticsEvent` factory from `AnalyticsMapper` (passive), or dispatch `.analytics(.track(.someEvent()))` from a reducer (effect) — define factories in `extension AnalyticsEvent`, never an event-name enum; see `references/swidux-analytics.md` |
| Record a screen view | Dispatch `.analytics(.screenView("Home"))` from the view's `.task` |
| Identify a signed-in user | `AnalyticsIdentity(userID: \.auth.currentUserID, …)` — see "Identity for analytics" |
| Identify an anonymous user (no auth) | Hydrate a Keychain UUID into `AppState.deviceID: String`; `AnalyticsIdentity(userID: \.deviceID, …)` — see "Identity for analytics" |
| Swap analytics or paywall provider | Two lines in `Store.configured()` + the dependency in `Package.swift` (paywall also flips the UI module import in the sheet view) |
| Gate an action on parent approval | Wire `ParentalGatePlugin`; dispatch `.parentalGate(.request(reason:))` |
| Add feature flags / A/B variants / remote config | Wire `FeatureFlagsPlugin`; declare typed flags via `BoolFlag` / `VariantFlag` / `ValueFlag`; read with `store.featureFlags.isEnabled(.myFlag)`; host the JSON via the shared ConfigWorker (`references/swidux-config-worker.md`) |
| Host / deploy remote killswitch + feature-flag config (incl. multi-app portfolio) | Scaffold & deploy the shared Cloudflare ConfigWorker — one Worker + one KV namespace, keyed `/<appID>/<resource>` (see `references/swidux-config-worker.md`) |
| Custom cross-cutting feature | Write a `SwiduxPlugin` (see DocC `BuildingADomainPlugin`) |

## Anti-patterns

- ❌ Calling `await` or `try` inside a reducer
- ❌ Hand-writing an observer class when you could use `@Swidux`
- ❌ Calling `db.save()` or other I/O from inside a reducer
- ❌ Mutating state from inside an effect closure (effects dispatch actions, never mutate directly)
- ❌ Owning the store with `@StateObject` (use `@State` — `Store` is `@Observable`, not `ObservableObject`)
- ❌ Importing `Swidux` in every feature file (re-export from AppState.swift)
- ❌ Registering `PersistencePlugin` before `UndoPlugin` (snapshot must happen before any mutation)
- ❌ Using regular `var` for state slices that should be `@Slice` (loses per-property observation)
- ❌ Reading from `KeyValueStore` inside a reducer (reads are for hydration only — pull values into state at startup, then observe state)
- ❌ Calling `hydrate(into:)` (or `state.items = EntityStore(fetched)`) on a post-launch refresh or remote-change path. That *replaces* and clobbers — mid-session, in-memory is authoritative, so it drops unflushed writes and in-progress UI edits and surfaces as lost keystrokes under live bindings. The only post-launch path is `persistence.rehydrate(into:)`, which always merges (rule #8). `hydrate` is first-load only
- ❌ Hand-writing a `@Model` class, a DB actor, or a `StateWriter` body when `@Persisted` + `PersistenceCoordinator` generate all three. Reach for the manual `PersistencePlugin`/`StateWriter` path only when you need control the macro can't express (see `references/swidux-persistence.md`)
- ❌ Adding iCloud/CloudKit/Push entitlements (or a CloudKit container) to a **local-only** app. Link `SwiduxPersistence` alone — it needs none; entitlements follow `SwiduxCloudKitSync`, and adding them otherwise is dead config and an App Review risk
- ❌ Putting `@Persisted` and `@Swidux` on the same type — they're different layers (`@Persisted` = domain entities in an `EntityStore`; `@Swidux` = state containers). The macro fires on entities only
- ❌ Giving a `@Persisted` entity a non-optional, non-primitive stored property (custom `Codable`, `URL`, enum) with no default and no `@Inline`, or a non-optional to-one `@Relation`. Both break CloudKit schema validation and are now compile errors (`mirrorRequiresDefault` / `relationRequiresOptional`); fix by adding a default, making the property optional, or — for blobs — marking it `@Inline`. CloudKit-safety is checked only at synced-container creation, so a bad schema passes every in-memory unit test and crashes only on device
- ❌ Treating `.misconfiguredNoEntitlement` as a runtime error to crash on. It's a build/signing bug — degrade to local-only and `assertionFailure` in DEBUG only, never crash a release build
- ❌ Re-deciding the macOS Keychain entitlement per app, or treating `errSecMissingEntitlement` / `OSStatus` −34018 as a runtime/user-prompt bug. The store never prompts; the answer is fixed — provisioning-profile–signed build + `accessGroup: nil`, with a single team-prefixed `keychain-access-groups` entry as the unsigned-local/CI fallback (see "Identity for analytics" and `references/swidux-analytics.md`)
- ❌ Calling I/O (Keychain, UserDefaults, file system, network) from the `AnalyticsIdentity` `userID` or `userProperties` closure — closures run on every non-analytics dispatch; hydrate once at launch and read from state
- ❌ Touching `UserDefaults.standard` directly anywhere in app code (use `KeyValueStore` so tests can inject `InMemoryKeyValueStore`)
- ❌ Importing or calling any analytics/paywall SDK directly in app code (`import Mixpanel`, `import RevenueCat`, `Mixpanel.initialize`, `Mixpanel.mainInstance().track`, `Purchases.configure`, `Purchases.shared.purchase`). Adapters absorb the SDK; tracking and purchase flows go through `.analytics(...)` / `.paywall(...)` actions
- ❌ Constructing the analytics or paywall service anywhere but inside `Store.configured()` — not in `@main`'s `App.init()`, not behind an `AppEnvironment.makeAnalyticsService()` helper. The conditional and the binding sit next to the plugin that uses them. **One sanctioned exception:** the SDK-free `SimulatedPaywallService` is constructed once in the owning view and passed to *both* `Store.configured()` and `.devPaywall(...)`, because the debug UI must drive the same instance the plugin observes (see `references/swidux-paywall.md` → "Default: develop and QA with no vendor"). This shared-instance wiring is the dev path's deliberate shape and is removed — collapsing back to the construct-only-in-`Store.configured()` rule — the moment a real provider is adopted
- ❌ Storing vendor-specific types (`MixpanelInstance`, `CustomerInfo`, `Offerings`) in `AppState`, `AppEnvironment`, or any feature type, or importing `SwiduxRevenueCatPaywallUI` outside the one sheet view. State and environment hold protocol-typed services only
- ❌ Introducing an event-name enum (in the library, action, or mapper layer) to "fix" stringly-typed analytics. `AnalyticsEvent.name` is intentionally the provider wire key; an adapter would `.rawValue` an enum back to a string anyway. Named `AnalyticsEvent` factories, never an event-name enum (see `references/swidux-analytics.md` → "Event names are the wire key")

## Requirements

- Swift 6.2+ / Xcode 26+
- macOS 15+ / iOS 18+
- **Swift 6 language mode is non-negotiable** (`SWIFT_VERSION = 6.0`; `.swiftLanguageMode(.v6)` is implicit at tools 6.2). A `@Swidux nonisolated struct` only gets a nonisolated synthesized memberwise init under Swift 6 mode. Under **Swift 5 mode + `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`** that init is treated as MainActor-isolated, and the macro's nonisolated state-reconstruction can't call it — you get `call to main actor-isolated initializer … in a synchronous nonisolated context`. Adding an explicit `nonisolated init` does **not** rescue Swift 5 mode; switching to Swift 6 does (and then the explicit init is redundant).
- After editing the package **product dependencies** of an Xcode project, run `xcodebuild -resolvePackageDependencies` before building.

## Library targets

- `Swidux` — core (Store, plugins protocol, EntityStore, persistence, undo, macros)
- `SwiduxPersistence` — SwiftData persistence: `@Persisted` macro + `PersistenceCoordinator` (reuses the core `PersistencePlugin`); local-only, no iCloud entitlements
- `SwiduxCloudKitSync` — opt-in iCloud sync on top of `SwiduxPersistence`: runtime toggle (`SyncCoordinator`), entitlement/account detection (`SyncPreflightService` → `SyncStatus`), merge-based `RemoteChangeObserver`
- `SwiduxKillswitch` — version-blocking plugin
- `SwiduxParentalGate` — math-challenge gate plugin
- `SwiduxPaywall` — paywall + entitlement plugin (RevenueCat or StoreKit-shaped); also ships the SDK-free `SimulatedPaywallService` dev default
- `SwiduxDevPaywallUI` — opt-in debug paywall sheet (`.devPaywall(...)`) driving `SimulatedPaywallService`; the no-vendor dev/QA path
- `SwiduxAnalytics` — provider-agnostic analytics plugin with declarative event mapping
- `SwiduxFeatureFlags` — feature flags + A/B variants + remote-tunable values from a JSON wire format
