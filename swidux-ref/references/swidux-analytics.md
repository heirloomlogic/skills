# SwiduxAnalytics + Mixpanel Wiring

Provider-agnostic analytics. App code depends on `AnalyticsService` from `SwiduxAnalytics`; `MixpanelAnalyticsService` from `SwiduxMixpanelAnalytics` calls `Mixpanel.initialize` internally so the app never imports `Mixpanel`.

## The protocol

`SwiduxAnalytics` defines what an analytics backend must do. Apps depend on this, not on Mixpanel:

```swift
public protocol AnalyticsService: Sendable {
    func track(_ event: AnalyticsEvent) async
    func identify(userID: String, properties: [String: AnalyticsValue]) async
    func alias(newID: String, previousID: String?) async
    func reset() async
    func flush() async
}
```

`AnalyticsValue` is a closed enum (`.string`, `.int`, `.double`, `.bool`, `.date`, `.array`, `.dict`, `.null`) with literal conformances — write `"pro"` and `5` directly in dictionaries; the adapter translates these into native Mixpanel types internally. The app never sees `MixpanelType`.

## Default: develop with no vendor

Because app code only ever speaks `AnalyticsService`, you don't need a vendor to build and verify analytics. `SwiduxAnalytics` ships two SDK-free conformers; the recommended `service:` while the Mixpanel decision is still open is `ConsoleAnalyticsService`:

```swift
import SwiduxAnalytics

let analyticsService: any AnalyticsService = ConsoleAnalyticsService()
```

`ConsoleAnalyticsService(subsystem: "Swidux", category: "Analytics")` logs every `track` / `identify` / `alias` / `reset` / `flush` to `os.Logger` — visible in the Xcode console and Console.app, quiet in Release — with a deterministic pretty-printer for `AnalyticsValue` (dict keys sorted). It is a *micro version of the real thing*: the mapper, identity transitions, screen-view enrichment, and opt-out all run through the real plugin pipeline, so analytics wiring is developed and QA-tested end to end with no SDK, no token, and no vendor account.

Don't confuse it with the silent `MockAnalyticsService()` — a parameterless no-op for previews and tests, where verification happens against a recording mock, not console output. For *developing* the app, `ConsoleAnalyticsService` is the default because the markers are observable.

Adopting Mixpanel later is purely the two-line `Store.configured()` swap shown under "Swapping providers" — mapper, identity, events, reducers, views, and tests are untouched. The vendor decision is deferred, not foundational.

## State slice and action enum

```swift
// AppState.swift
@Swidux
nonisolated struct AppState: Equatable, Sendable {
    @Slice var analytics: AnalyticsState = .init()
}

// AppAction.swift
enum AppAction: Sendable {
    case analytics(AnalyticsAction)
}

// AppReducer.swift — root reducer falls through; the plugin owns its actions.
case .analytics:
    return nil
```

`AnalyticsState` carries `isOptedOut`, `currentScreen`, `lastIdentifiedUserID`, and `lastIdentifiedProperties` (the last two are plugin-managed; the plugin diffs the pair to decide when to re-fire `identify`). `AnalyticsAction` cases:

- `.track(AnalyticsEvent)` — explicit event, bypasses the mapper
- `.screenView(String, properties: [String: AnalyticsValue])` — also updates `currentScreen` so subsequent events get a `"screen"` property auto-attached
- `.identify(userID:properties:)`, `.alias(newID:previousID:)`, `.reset` — identity transitions
- `.setOptedOut(Bool)` — opting out clears identity and pauses both mapper and auto-identify

## Declarative event mapping

The plugin has two surfaces: passive (the mapper, run after every non-analytics action) and explicit (`AnalyticsAction` cases dispatched directly). Prefer the mapper; it keeps reducers and views ignorant of analytics.

```swift
// App/AnalyticsMapping.swift  (lives in the app, not the adapter)
let analyticsMapper = AnalyticsMapper<AppState, AppAction> { state, action in
    switch action {
    case .items(.add):
        return [AnalyticsEvent("item_added")]
    case .items(.remove):
        return [AnalyticsEvent("item_removed")]
    case .paywall(.request(let reason)):
        return [AnalyticsEvent("paywall_requested", ["reason": .string(reason)])]
    default:
        return []
    }
}
```

## Event names are the wire key — not an enum

`AnalyticsEvent.name` is a `String` by design (`SwiduxAnalytics/AnalyticsEvent.swift`): the value is sent verbatim as the provider's event key. A library-, action-, or mapper-level event-name enum is an **anti-pattern, not a deferred improvement** — it would force the provider-agnostic library to enumerate every app's vocabulary, and the adapter would `.rawValue` it straight back to a string at the boundary anyway. The string *is* the deliberate wire type; don't re-architect around it.

Typos, missing autocomplete, no central registry, and Mixpanel Lexicon drift are real concerns — solve them **additively, app-side** with named static factories that still return the boundary type. The mapper shape is unchanged:

```swift
// App/AnalyticsEvents.swift — the app's event registry
extension AnalyticsEvent {
    static func itemAdded() -> AnalyticsEvent { .init("item_added") }
    static func paywallRequested(reason: String) -> AnalyticsEvent {
        .init("paywall_requested", ["reason": .string(reason)])
    }
}

// App/AnalyticsMapping.swift — factory form; equivalent to the literal form above
case .items(.add):
    return [.itemAdded()]
case .paywall(.request(let reason)):
    return [.paywallRequested(reason: reason)]
```

**Named `AnalyticsEvent` factories, never an event-name enum.** The factory file is the app's registry: one place to grep, one place autocomplete surfaces, one place to reconcile against Lexicon.

## Identity

Identity is the analytics plugin's second passive surface. Like the mapper, `userID` and `userProperties` are pure functions of state, and the plugin re-runs them on every non-analytics dispatch. When `(userID, userProperties)` changes against the last-sent pair, the plugin fires `service.identify`; when `userID` transitions to `nil`, it fires `service.reset`. Late-arriving values (paywall entitlements, feature flags, A/B variants) flow into the analytics service automatically as soon as state reflects them — no need to gate `userID` behind a "ready" flag or to manually dispatch `.analytics(.identify(...))` when properties change.

Both closures run hot. Keep them to direct keypath reads, dictionary literals, and simple ternaries. Avoid allocations, sorting, JSON encoding, work proportional to collection size, and — above all — I/O. The exact mistake to avoid is reading the device UUID out of Keychain from inside the `userID` closure: it executes per dispatch, which would mean a Keychain hit per dispatch. Hydrate at launch, read from state. Dictionary equality short-circuits the no-op case, so cheap-and-frequent is the intended shape.

Two canonical paths cover almost every app:

### Auth path (signed-in users)

State carries an optional `currentUserID`; the auth reducer sets it on sign-in and clears it on sign-out:

```swift
@Swidux
nonisolated struct AuthState: Equatable, Sendable {
    var currentUserID: String? = nil
}

// Reducer arms
case .auth(.signedIn(let userID)):
    state.auth.currentUserID = userID
    return nil

case .auth(.signedOut):
    state.auth.currentUserID = nil
    return nil

// Identity wiring
let analyticsIdentity = AnalyticsIdentity<AppState>(
    userID: \.auth.currentUserID,
    userProperties: { state in
        [
            "subscription_tier": state.paywall.isPro ? "pro" : "free",
            "ab_onboarding_v2": state.featureFlags.onboardingV2,
        ]
    }
)
```

**What happens on logout.** Clearing `currentUserID` makes the next dispatch trip the `id → nil` transition; the plugin fires `service.reset()` exactly once. No manual `.analytics(.reset)` dispatch needed — and importantly, dispatching one in addition will double-fire. Let the transition do its work.

### Anonymous path (no auth — device-stable identity)

Apps without a user account system still want stable identity for analytics so a single user's sessions correlate. Mint a UUID once, persist it in Keychain so it survives reinstall, hydrate into `AppState.deviceID` at launch, and feed it through the keypath:

```swift
// Key declaration (somewhere central, e.g., AppState.swift)
extension KVKey where Value == String {
    static let deviceID = KVKey<String>("device-id")
}

// AppState — always present after launch; non-optional
@Swidux
nonisolated struct AppState: Equatable, Sendable {
    var deviceID: String
    @Slice var ui: UIState = .init()
    // …
}

// In Store.configured(), before constructing the store
let kv = KeychainKeyValueStore(service: "com.example.myapp")
let deviceID = kv.value(.deviceID) ?? {
    let new = UUID().uuidString
    kv.setValue(new, for: .deviceID)
    return new
}()
let initial = AppState(deviceID: deviceID, ui: .hydrated(from: kv))

// Identity wiring
let analyticsIdentity = AnalyticsIdentity<AppState>(
    userID: \.deviceID,
    userProperties: { _ in [:] }
)
```

`AppState.deviceID` is non-optional — it's hydrated before the store exists and never absent. `AnalyticsIdentity(userID:)` has a `KeyPath<State, String>` init for exactly this case; the `String?` init is reserved for genuinely-optional IDs (signed-out auth).

**Keychain vs UserDefaults.** `KeychainKeyValueStore` survives reinstall (default `.afterFirstUnlockThisDeviceOnly` accessibility — readable in the background after first unlock, excluded from iCloud Keychain sync and device-to-device migration). `UserDefaultsKeyValueStore` does not survive reinstall — a fresh install gets a new identity. Pick Keychain when you want analytics to attribute a re-installer to their old identity (the usual choice); pick UserDefaults when reinstall-as-new-user is the right product semantic. The full comparison table and accessibility tuning live in Swidux DocC `KeyValueStoreGuide`.

**macOS Keychain entitlement.** `KeychainKeyValueStore` uses the data-protection keychain, so it **never** prompts the user — no Always Allow/Deny dialog, no locked-keychain prompt, no Touch ID / Face ID. Don't reason about this per app; the answer is fixed. **Default: ship a provisioning-profile–signed build and leave `accessGroup: nil`** — the implicit `application-identifier` group, identical to the iOS default and the most private option (zero sharing surface). For an *unsigned* local or CI build the first `setValue` fails with `errSecMissingEntitlement` / `OSStatus` −34018 — a **signing/build** condition, not a runtime prompt or a bug. Fix it by adding a single team-prefixed entry (nothing else, and never a shared group first):

```xml
<key>keychain-access-groups</key>
<array>
    <string>$(AppIdentifierPrefix)com.example.myapp</string>
</array>
```

iOS / iPadOS / tvOS / watchOS need no extra entitlement. The full strictness ranking lives in Swidux DocC `KeyValueStoreGuide` → "macOS sandbox & entitlements".

### Derived IDs

For hashed or transformed IDs, use the closure-based init:

```swift
AnalyticsIdentity(userID: { state in hash(state.auth.currentUserID) })
```

For hashed/transformed IDs use the closure init; for a plain non-optional stored ID, prefer the `KeyPath<State, String>` init. Same cheapness rules apply: pure, allocation-free, no I/O.

### Identity tests

Inject `InMemoryKeyValueStore` for both paths to make hydration deterministic. The DocC `KeyValueStoreGuide` "Testing" section shows the pattern (same-instance read-back after a write); identity tests build on top by hydrating an `AppState` from that store and asserting on the plugin's `service.identify` / `service.reset` calls captured by `MockMixpanelAnalyticsService`. See "Tests" below for the general analytics mock setup.

## Plugin construction in `Store.configured()`

**Default (no vendor yet) — develop on `ConsoleAnalyticsService`:**

```swift
// App/AppStore.swift
import SwiduxAnalytics

// inside Store.configured():
let analyticsService: any AnalyticsService = ConsoleAnalyticsService()

plugins.register(
    AnalyticsPlugin<AppState, AppAction>(
        state: \.analytics,
        action: AppAction.analytics,
        extractAction: { if case .analytics(let a) = $0 { return a }; return nil },
        service: analyticsService,
        mapper: analyticsMapper,
        identity: analyticsIdentity
    )
)
```

This is the form you keep for the bulk of development — no `import SwiduxMixpanelAnalytics`, no token. Every tracked event prints, so the wiring is observable while you build.

**After adopting Mixpanel — token-gated:**

```swift
// App/AppStore.swift
import SwiduxAnalytics
import SwiduxMixpanelAnalytics

// inside Store.configured():
let analyticsService: any AnalyticsService =
    Secrets.mixpanelToken.isEmpty
        ? ConsoleAnalyticsService()
        : MixpanelAnalyticsService(token: Secrets.mixpanelToken)
```

Once a vendor is chosen, this swap is the *only* change — the plugin registration above is identical. Note the empty-token fallback is `ConsoleAnalyticsService()`, not the silent `MockAnalyticsService()`: a build without a token (a teammate's checkout, CI) should still show analytics output rather than drop it silently. The choice lives next to the plugin — no environment indirection.

`MixpanelAnalyticsService.init(token:)` covers the common knobs: `trackAutomaticEvents` (iOS only), `flushInterval`, `instanceName`, `optOutTrackingByDefault`, `useUniqueDistinctId`, `superProperties`, `serverURL` (EU residency), `useGzipCompression`. For apps that need a fully custom `MixpanelInstance` (proxy server config), the escape hatch is `MixpanelAnalyticsService(instance:)` — that's the only path that still requires `import Mixpanel`, and almost no app needs it.

## Dispatching events from reducers

When the mapper isn't the right shape — usually for async events that depend on effect results, or identity transitions that need an `alias` for anon-to-known stitching — dispatch explicitly. This sits on top of auto-identify: the keypath transition still fires `identify`/`reset` automatically; the explicit dispatch is purely for the *additional* work the passive surfaces don't cover.

```swift
case .auth(.signedIn(let userID)):
    state.auth.currentUserID = userID                   // auto-identify fires from this on the next dispatch
    return { send in
        await send(.analytics(.alias(newID: userID)))   // stitches the prior anonymous distinctId to the new userID
        await send(.analytics(.track(AnalyticsEvent("user_signed_in"))))
    }
```

Reducers never call `MixpanelInstance` directly. The plugin enriches each event with `currentScreen` automatically.

## Screen views from SwiftUI

```swift
struct ContentView: View {
    @Environment(AppStore.self) private var store

    var body: some View {
        List { /* … */ }
            .task { store.send(.analytics(.screenView("Home"))) }
    }
}
```

## Tests

Inject the recording mock and assert against its captured calls:

```swift
import Testing
import SwiduxMixpanelAnalytics
@testable import MyApp

@MainActor
@Test func itemAdded_tracksEvent() async throws {
    let mock = MockMixpanelAnalyticsService()
    let plugin = AnalyticsPlugin<AppState, AppAction>(
        state: \.analytics,
        action: AppAction.analytics,
        extractAction: { if case .analytics(let a) = $0 { return a }; return nil },
        service: mock,
        mapper: analyticsMapper
    )

    var state = AppState()
    plugin.afterReduce(state: &state, action: .items(.add))
    await plugin.flush()

    let events = await mock.trackedEvents
    #expect(events.first?.name == "item_added")
}
```

`MockMixpanelAnalyticsService` is an `actor` that records `trackedEvents`, `identifyCalls`, `aliasCalls`, `resetCount`, `flushCount`, plus opt-out / logging / geo state — read them with `await` after calling `plugin.flush()`. For previews where nothing needs verifying, the core `MockAnalyticsService()` from `SwiduxAnalytics` is a parameterless no-op struct.

## Swapping providers

To swap Mixpanel for a hypothetical Amplitude adapter, change two lines in `Store.configured()`:

```diff
- import SwiduxMixpanelAnalytics
+ import SwiduxAmplitudeAnalytics

- let analyticsService = MixpanelAnalyticsService(token: Secrets.mixpanelToken)
+ let analyticsService = AmplitudeAnalyticsService(apiKey: Secrets.amplitudeAPIKey)
```

…and swap the package dependency in `Package.swift`. Mapper, identity, state slice, action enum, reducer dispatches, screen views, and tests are unchanged — they speak `AnalyticsService` / `AnalyticsValue` / `AnalyticsEvent` from `SwiduxAnalytics`, not the adapter. (See rule #11 in `SKILL.md`.)
