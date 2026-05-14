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

`AnalyticsState` carries `isOptedOut`, `currentScreen`, and `lastIdentifiedUserID` (plugin-managed). `AnalyticsAction` cases:

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

Identity follows the same shape — the plugin watches the keypath across dispatches and fires `identify` / `reset` on transitions automatically:

```swift
let analyticsIdentity = AnalyticsIdentity<AppState>(
    userID: \.auth.currentUserID,
    userProperties: { state in
        ["subscription_tier": state.paywall.isPro ? "pro" : "free"]
    }
)
```

The keypath-based init requires `KeyPath<State, String?> & Sendable`. For derived IDs (e.g., hashed), use the closure-based init: `AnalyticsIdentity(userID: { hash($0.auth.currentUserID) })`.

## Plugin construction in `Store.configured()`

```swift
// App/AppStore.swift
import SwiduxAnalytics
import SwiduxMixpanelAnalytics

// inside Store.configured():
let analyticsService: any AnalyticsService =
    Secrets.mixpanelToken.isEmpty
        ? MockAnalyticsService()
        : MixpanelAnalyticsService(token: Secrets.mixpanelToken)

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

The empty-token branch picks the no-op `MockAnalyticsService` from `SwiduxAnalytics`. The choice lives next to the plugin — no environment indirection.

`MixpanelAnalyticsService.init(token:)` covers the common knobs: `trackAutomaticEvents` (iOS only), `flushInterval`, `instanceName`, `optOutTrackingByDefault`, `useUniqueDistinctId`, `superProperties`, `serverURL` (EU residency), `useGzipCompression`. For apps that need a fully custom `MixpanelInstance` (proxy server config), the escape hatch is `MixpanelAnalyticsService(instance:)` — that's the only path that still requires `import Mixpanel`, and almost no app needs it.

## Dispatching events from reducers

When the mapper isn't the right shape — usually for async events that depend on effect results — dispatch explicitly:

```swift
case .auth(.signedIn(let userID)):
    state.auth.currentUserID = userID
    return { send in
        await send(.analytics(.alias(newID: userID)))
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
