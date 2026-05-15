---
name: swidux-ref
description: Architecture rules and code templates for Swidux — a Redux-style state-management library for SwiftUI — and its provider-agnostic service layer (analytics, paywall). Use when writing Swidux apps, adding actions or reducers, wiring plugins (Persistence, Undo, Killswitch, ParentalGate, Paywall, Analytics, FeatureFlags), or integrating third-party services like Mixpanel or RevenueCat through their Swidux adapter packages. Activate on "Swidux", "@Swidux", "AppStore", "AppReducer", "EntityStore", "killswitch", "paywall", "parental gate", "AnalyticsService", "PaywallService", "MixpanelAnalyticsService", "RevenueCatPaywallService".
---

# Swidux Reference

Swidux is a Redux-style state-management library for SwiftUI. State lives in one observable store; mutations go through reducers; side effects run as async closures. Macros generate observability boilerplate; plugins handle persistence, undo, paywalls, killswitches, parental gates, analytics, and feature flags. Third-party services (Mixpanel, RevenueCat, …) are accessed through their dedicated Swidux adapter packages — never imported into app code directly.

This skill captures the rules, conventions, and dispatch lifecycle. Code templates are in `swidux-patterns.md`. Full wiring walkthroughs for the analytics and paywall layers — including the protocol/adapter layering and provider-swap recipe — are in `swidux-analytics.md` and `swidux-paywall.md`.

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

### 8. Persistence is automatic via `EntityStore` change tracking

```swift
let persistencePlugin = PersistencePlugin<AppState, AppAction>(
    writers: [
        StateWriter(keyPath: \.items) { writes, deletes in
            for item in writes { try? await db.upsert(item) }
            for id in deletes { try? await db.delete(id: id) }
        }
    ]
)
```

`EntityStore.modify(_:_:)`, `removeAll(where:)`, and `sort(by:)` track changes. The plugin debounces and batches them; you never call `save()` from a reducer. Reducers stay pure; persistence is observed.

**Scalar preferences (UserDefaults) use a different mechanism.** `EntityStore` is for collections of identifiable entities. For one-off scalar values (theme, sort order, last-seen version), inject a `KeyValueStore` through `Environment`, declare type-safe keys on `KVKey`, hydrate state at startup, and write from effects:

```swift
extension KVKey where Value == Theme {
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

Vendor names appear in exactly two files: `Package.swift` (the dependency) and `App/AppStore.swift` (the service construction inside `Store.configured()`). For paywalls the one view that attaches the sheet is a third allowed site (`import SwiduxRevenueCatPaywallUI`). Everything else — `@main`, root view, feature views, reducers, environment, models — stays vendor-blind.

Swapping providers (Mixpanel → Amplitude, RevenueCat → StoreKit2) is a two-line change in `Store.configured()` plus the package swap. State slices, actions, reducer dispatches, gate checks, and analytics events are unchanged because they speak the Swidux types (`AnalyticsService`, `AnalyticsEvent`, `PaywallState`, `EntitlementSnapshot`). Any migration that touches more than these sites means the protocol has leaked — find it and push it back.

Full wiring in `swidux-analytics.md` and `swidux-paywall.md`.

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

Use `KeychainKeyValueStore` (survives reinstall) to mint a UUID once and hydrate it into `AppState.deviceID: String?` in `Store.configured()`. The canonical read-or-mint helper lives in Swidux DocC under `KeyValueStoreGuide` → "Device-Identity Pattern" — don't reinvent the `SecItemCopyMatching` boilerplate locally.

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

Declare `var deviceID: String? = nil` on `AppState` so the keypath form (which needs `KeyPath<State, String?>`) typechecks; the launch path keeps it non-nil. Full walkthrough including the `KVKey<String>("device-id")` declaration, accessibility tuning, and test injection in `swidux-analytics.md` and the DocC `KeyValueStoreGuide`.

`KeychainKeyValueStore` never prompts the user (no Always Allow/Deny, no Touch ID / Face ID). The macOS entitlement answer is fixed, not a per-app decision: ship a provisioning-profile–signed build and leave `accessGroup: nil`; an unsigned local/CI build that fails the first write with `errSecMissingEntitlement` / `OSStatus` −34018 is a signing condition, not a prompt or a bug — add one team-prefixed `keychain-access-groups` entry. See `swidux-analytics.md` "macOS Keychain entitlement" and DocC `KeyValueStoreGuide`.

## SwiftUI integration rules

- App owns the store with `@State`: `@State private var store = AppStore.configured()`. Inject via `.environment(store)`. Never recreate the store in `body`.
- Views read via `@Environment(AppStore.self)` and dispatch with `store.send(.someAction)`.
- For form controls, prefer `store.binding(\.path.to.value) { .someAction($0) }` — a `KeyPath<State.Observer, Value>` plus an action constructor. Falls back to `Binding(get:set:)` when the read is transformed (optional unwraps, derived values) or the setter wraps the dispatch in animation/branching. Never let SwiftUI own the truth; the reducer does.
- Per-row observation: pass `store` (or a per-row binding into `EntityStore`) into a row view, and read inside that row. SwiftUI re-renders only what it reads.

## Conventions

- Re-export Swidux from `AppState.swift`: `@_exported import Swidux`. Other files don't need `import Swidux`.
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
| Persist a new entity collection | Add `EntityStore<NewEntity>` to AppState, add `StateWriter(keyPath: \.newEntities) { … }` to PersistencePlugin |
| Persist a scalar preference (theme, last-seen version) | Inject `KeyValueStore` via `Environment`; hydrate at startup, write from an effect |
| Add undo for an action | Make `isUndoable` return `true` for that case |
| Block on app version | Wire `KillswitchPlugin` (see `swidux-patterns.md`) |
| Gate a feature on subscription | Check `store.paywall.isGateSatisfied`; otherwise dispatch `.paywall(.request(reason:))` (see `swidux-paywall.md`) |
| Show the paywall sheet | `.revenueCatPaywall(state: store.paywall) { store.send(.paywall($0)) }` from `SwiduxRevenueCatPaywallUI` |
| Track an analytics event | Return a named `AnalyticsEvent` factory from `AnalyticsMapper` (passive), or dispatch `.analytics(.track(.someEvent()))` from a reducer (effect) — define factories in `extension AnalyticsEvent`, never an event-name enum; see `swidux-analytics.md` |
| Record a screen view | Dispatch `.analytics(.screenView("Home"))` from the view's `.task` |
| Identify a signed-in user | `AnalyticsIdentity(userID: \.auth.currentUserID, …)` — see "Identity for analytics" |
| Identify an anonymous user (no auth) | Hydrate a Keychain UUID into `AppState.deviceID: String?`; `AnalyticsIdentity(userID: \.deviceID, …)` — see "Identity for analytics" |
| Swap analytics or paywall provider | Two lines in `Store.configured()` + the dependency in `Package.swift` (paywall also flips the UI module import in the sheet view) |
| Gate an action on parent approval | Wire `ParentalGatePlugin`; dispatch `.parentalGate(.request(reason:))` |
| Add feature flags / A/B variants / remote config | Wire `FeatureFlagsPlugin`; declare typed flags via `BoolFlag` / `VariantFlag` / `ValueFlag`; read with `store.featureFlags.isEnabled(.myFlag)` |
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
- ❌ Re-deciding the macOS Keychain entitlement per app, or treating `errSecMissingEntitlement` / `OSStatus` −34018 as a runtime/user-prompt bug. The store never prompts; the answer is fixed — provisioning-profile–signed build + `accessGroup: nil`, with a single team-prefixed `keychain-access-groups` entry as the unsigned-local/CI fallback (see "Identity for analytics" and `swidux-analytics.md`)
- ❌ Calling I/O (Keychain, UserDefaults, file system, network) from the `AnalyticsIdentity` `userID` or `userProperties` closure — closures run on every non-analytics dispatch; hydrate once at launch and read from state
- ❌ Touching `UserDefaults.standard` directly anywhere in app code (use `KeyValueStore` so tests can inject `InMemoryKeyValueStore`)
- ❌ Importing or calling any analytics/paywall SDK directly in app code (`import Mixpanel`, `import RevenueCat`, `Mixpanel.initialize`, `Mixpanel.mainInstance().track`, `Purchases.configure`, `Purchases.shared.purchase`). Adapters absorb the SDK; tracking and purchase flows go through `.analytics(...)` / `.paywall(...)` actions
- ❌ Constructing the analytics or paywall service anywhere but inside `Store.configured()` — not in `@main`'s `App.init()`, not behind an `AppEnvironment.makeAnalyticsService()` helper. The conditional and the binding sit next to the plugin that uses them
- ❌ Storing vendor-specific types (`MixpanelInstance`, `CustomerInfo`, `Offerings`) in `AppState`, `AppEnvironment`, or any feature type, or importing `SwiduxRevenueCatPaywallUI` outside the one sheet view. State and environment hold protocol-typed services only
- ❌ Introducing an event-name enum (in the library, action, or mapper layer) to "fix" stringly-typed analytics. `AnalyticsEvent.name` is intentionally the provider wire key; an adapter would `.rawValue` an enum back to a string anyway. Named `AnalyticsEvent` factories, never an event-name enum (see `swidux-analytics.md` → "Event names are the wire key")

## Requirements

- Swift 6.2+ / Xcode 26+
- macOS 15+ / iOS 18+
- Strict concurrency (`.swiftLanguageMode(.v6)` is implicit at tools 6.2)

## Library targets

- `Swidux` — core (Store, plugins protocol, EntityStore, persistence, undo, macros)
- `SwiduxKillswitch` — version-blocking plugin
- `SwiduxParentalGate` — math-challenge gate plugin
- `SwiduxPaywall` — paywall + entitlement plugin (RevenueCat or StoreKit-shaped)
- `SwiduxAnalytics` — provider-agnostic analytics plugin with declarative event mapping
- `SwiduxFeatureFlags` — feature flags + A/B variants + remote-tunable values from a JSON wire format
