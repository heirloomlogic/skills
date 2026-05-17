# SwiduxPaywall + RevenueCat Wiring

Provider-agnostic paywall. App code depends on `PaywallService` from `SwiduxPaywall`; `RevenueCatPaywallService` from `SwiduxRevenueCatPaywall` calls `Purchases.configure` internally so the app never imports `RevenueCat` or `RevenueCatUI`.

## The protocol

`SwiduxPaywall` defines what a paywall backend must do. Apps depend on this, not on RevenueCat:

```swift
public protocol PaywallService: Sendable {
    func customerInfo() async throws -> EntitlementSnapshot
    func customerInfoStream() -> AsyncStream<EntitlementSnapshot>
    func restorePurchases() async throws -> EntitlementSnapshot
}
```

`EntitlementSnapshot` is the cross-vendor entitlement type — `{ isPro: Bool, hasPermanentLicense: Bool }`. RevenueCat's `CustomerInfo` and `Offerings` types stay inside the adapter; the app never sees them.

## State slice and action enum

```swift
// AppState.swift
@Swidux
nonisolated struct AppState: Equatable, Sendable {
    @Slice var paywall: PaywallState = .init()
}

// AppAction.swift
enum AppAction: Sendable {
    case paywall(PaywallAction)
}

// AppReducer.swift — root reducer falls through; the plugin owns its actions.
case .paywall:
    return nil
```

`PaywallState` exposes `isPro`, `hasPermanentLicense`, `isPresented`, `requestedReason`, `isLoading`, `error`, `isCustomerCenterPresented`, and a derived `isGateSatisfied` (`isPro || hasPermanentLicense`).

`PaywallAction` cases:

- `.request(reason: String)` — presents the paywall sheet, tagged with a feature reason
- `.dismiss` — clears `isPresented` and triggers a customer-info refresh
- `.observeCustomerInfo` — long-lived stream of entitlement updates (purchases, refunds, family-share, sandbox renewals)
- `.refreshCustomerInfo` — one-shot fetch
- `.customerInfoUpdated(EntitlementSnapshot)` — plugin-emitted result of an observation or refresh
- `.refreshFailed(String)` — plugin-emitted error
- `.restorePurchases`
- `.presentCustomerCenter` / `.dismissCustomerCenter`
- `.openManageSubscriptions` — opens the system Manage Subscriptions page

## Default: develop and QA with no vendor

Because app code only ever speaks `PaywallService` / `PaywallState` / `EntitlementSnapshot`, you don't need RevenueCat to build, gate, and QA the paywall. `SwiduxPaywall` ships `SimulatedPaywallService` — a stateful `actor` conformer that is the recommended `service:` while the vendor decision is still open. It's a *micro version of the real thing*: entitlement changes are pushed through `customerInfoStream()`, so they flow through the real `PaywallPlugin` pipeline and survive a later `refreshCustomerInfo` / `restorePurchases` exactly as a RevenueCat or StoreKit service would.

Beyond the `PaywallService` protocol it exposes a simulation surface (driven by the dev UI, not by app code):

```swift
public actor SimulatedPaywallService: PaywallService {
    public init(isPro: Bool = false, hasPermanentLicense: Bool = false,
                subsystem: String = "Swidux", category: String = "Paywall")

    // Not part of PaywallService — the dev sheet drives these:
    func grantPro(); func grantTrial(); func grantPermanentLicense(); func setFree()
    func setRestoreShouldFail(_: Bool); func setRefreshShouldFail(_: Bool)
    func setArtificialDelay(_: Duration)
}

public enum SimulatedPaywallError: Error, Equatable { case restoreFailed, refreshFailed }
```

**Modeling limitation.** `EntitlementSnapshot` is only `{ isPro, hasPermanentLicense }`, so `grantTrial()` yields `isPro == true` — it differs from `grantPro()` only in the log line, not in observable state. Model trial-specific UI from your own state, not from the snapshot.

### The dev paywall sheet

`SwiduxDevPaywallUI` is a separate, opt-in library product (`import SwiduxDevPaywallUI`). Its `.devPaywall(state:service:onAction:)` modifier mirrors the shape of the vendor sheet (`.revenueCatPaywall(state:onAction:)`) so the call site is unchanged on adoption. The sheet shows the live `PaywallState`, entitlement-grant buttons, real Restore/Refresh flows, and QA failure/latency toggles.

### Shared-instance wiring

The plugin and the dev sheet must drive the *same* `SimulatedPaywallService` instance — the sheet's buttons mutate the actor, and those changes only reach the store if the plugin is observing that exact instance. So construct it once in the owning view and hand it to both:

```swift
struct MyApp: App {
    @State private var paywallService: SimulatedPaywallService
    @State private var store: AppStore

    init() {
        let service = SimulatedPaywallService()
        _paywallService = State(initialValue: service)
        _store = State(initialValue: .configured(paywallService: service))
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
                .devPaywall(state: store.paywall, service: paywallService) {
                    store.send(.paywall($0))
                }
        }
    }
}
```

This is the **one sanctioned exception** to "construct the service only inside `Store.configured()`" (see `SKILL.md` anti-patterns): the debug UI must drive the same instance the plugin observes, so `Store.configured()` takes a `paywallService:` parameter on the dev path. It is deliberate, scoped to the no-vendor path, and removed the moment a real provider is adopted — at which point `Store.configured()` constructs the vendor service internally again and the rule re-applies unchanged.

`Store.configured()` registers the plugin with the passed instance:

```swift
extension Store where State == AppState, Action == AppAction {
    static func configured(paywallService: any PaywallService) -> AppStore {
        // …
        plugins.register(
            PaywallPlugin<AppState, AppAction>(
                state: \.paywall,
                action: AppAction.paywall,
                extractAction: { if case .paywall(let a) = $0 { return a }; return nil },
                service: paywallService
            )
        )
        // …
    }
}
```

Everything downstream — gating, `.request(reason:)`, the observe/refresh/restore actions, the analytics mapper — is identical to the vendor path. You build the entire paywall surface this way and defer the RevenueCat decision indefinitely.

## Plugin construction in `Store.configured()` (after adopting RevenueCat)

The wiring below is what `Store.configured()` looks like *once a vendor is chosen*. Until then, use the SDK-free `SimulatedPaywallService` form above — this section is the destination, not the starting point.

```swift
// App/AppStore.swift
import SwiduxPaywall
import SwiduxRevenueCatPaywall

// inside Store.configured():
RevenueCatPaywall.configure(apiKey: Secrets.revenueCatAPIKey)
plugins.register(
    PaywallPlugin<AppState, AppAction>(
        state: \.paywall,
        action: AppAction.paywall,
        extractAction: { if case .paywall(let a) = $0 { return a }; return nil },
        service: RevenueCatPaywallService(entitlementID: "pro")
    )
)
```

`RevenueCatPaywall.configure(...)` is a static entry point on a namespace enum, not a method on the service. Repeated invocations are a no-op (safe for SwiftUI `App` re-instantiation and previews). Optional knobs: `appUserID`, `userDefaults` (use an app-group `UserDefaults` to share entitlement state with widgets), `logLevel` from the package's own `RevenueCatPaywall.LogLevel` enum.

`RevenueCatPaywallService(entitlementID:)` binds the entitlement identifier that surfaces as `isPro`. For a lifetime SKU alongside a subscription, pass `permanentLicenseEntitlementID:` for the second identifier (surfaces as `hasPermanentLicense`).

## Starting the entitlement stream at launch

The plugin doesn't auto-subscribe — dispatch `.observeCustomerInfo` once, typically from the root view:

```swift
struct ContentView: View {
    @Environment(AppStore.self) private var store

    var body: some View {
        // …
            .task { store.send(.paywall(.observeCustomerInfo)) }
    }
}
```

This kicks off a long-lived task that forwards every entitlement transition (purchase, refund, family-share, sandbox renewal) as `.customerInfoUpdated(snapshot)`.

## Gating a feature

```swift
Button("Pro feature") {
    if store.paywall.isGateSatisfied {
        store.send(.proFeature(.run))
    } else {
        store.send(.paywall(.request(reason: "pro_feature")))
    }
}
```

Tag upgrade events by mapping `.paywall(.request(let reason))` in `AnalyticsMapper`.

## View integration

Import `SwiduxRevenueCatPaywallUI` in the one view that attaches the sheet. The convenience modifier attaches both the paywall and the customer-center in a single call, driven by `PaywallState`:

```swift
// Views/RootView.swift
import SwiduxRevenueCatPaywallUI
import SwiftUI

struct RootView: View {
    @Environment(AppStore.self) private var store

    var body: some View {
        ContentView()
            .revenueCatPaywall(state: store.paywall) { store.send(.paywall($0)) }
    }
}
```

The modifier handles platform differences: `fullScreenCover` on iOS, a 400×600-minimum `sheet` on macOS for the paywall; a `sheet` on iOS, an App Store deep link on macOS for the customer center. The view never imports `RevenueCat` or `RevenueCatUI` — those stay inside the UI target of the adapter package.

For the rarer one-sheet-at-a-time case, the lower-level modifiers `.revenueCatPaywall(isPresented:)` and `.revenueCatCustomerCenter(isPresented:)` take a `Binding<Bool>` directly.

Dispatch `.paywall(.presentCustomerCenter)` from anywhere to open the customer center; `.paywall(.openManageSubscriptions)` jumps straight to the system page.

## Tests

Use the recording mock from the adapter package — its stream stays live so tests can drive entitlement transitions:

```swift
import Testing
import SwiduxPaywall
import SwiduxRevenueCatPaywall
@testable import MyApp

@MainActor
@Test func upgrade_flipsIsPro() async throws {
    let mock = MockRevenueCatPaywallService(isPro: false)
    let plugin = PaywallPlugin<AppState, AppAction>(
        state: \.paywall,
        action: AppAction.paywall,
        extractAction: { if case .paywall(let a) = $0 { return a }; return nil },
        service: mock
    )

    var state = AppState()
    let effect = try #require(
        plugin.reduce(state: &state, action: .paywall(.observeCustomerInfo))
    )

    let stream = Task {
        var dispatched: [AppAction] = []
        await effect { dispatched.append($0) }
        return dispatched
    }

    mock.send(EntitlementSnapshot(isPro: true))
    mock.finish()

    let result = await stream.value
    #expect(result.contains(where: {
        if case .paywall(.customerInfoUpdated(let snap)) = $0 { return snap.isPro }
        return false
    }))
}
```

The core `SwiduxPaywall` package also ships a simpler `MockPaywallService(isPro:hasPermanentLicense:)` whose stream finishes immediately — useful for previews where one snapshot is enough, but not for tests that need to simulate a purchase transition.

## Swapping providers

To swap RevenueCat for a hypothetical StoreKit2-backed adapter, you change two lines in `Store.configured()`:

```diff
- import SwiduxRevenueCatPaywall
+ import SwiduxStoreKit2Paywall

- RevenueCatPaywall.configure(apiKey: Secrets.revenueCatAPIKey)
- let paywallService = RevenueCatPaywallService(entitlementID: "pro")
+ let paywallService = StoreKit2PaywallService(productIDs: ["pro_monthly", "pro_annual"])
```

…and in the one view that attaches the sheet:

```diff
- import SwiduxRevenueCatPaywallUI
+ import SwiduxStoreKit2PaywallUI

- .revenueCatPaywall(state: store.paywall) { store.send(.paywall($0)) }
+ .storeKit2Paywall(state: store.paywall) { store.send(.paywall($0)) }
```

…plus the package dependencies in `Package.swift`. State slice, action enum, reducer dispatches, gate checks, `.request(reason:)` calls, analytics mapper — all unchanged, because they speak `PaywallState` / `PaywallAction` / `EntitlementSnapshot` from `SwiduxPaywall`. (See rule #11 in `SKILL.md`.)

### Adopting a vendor from the SDK-free dev default

The first adoption (`SimulatedPaywallService` → RevenueCat) is the same two-line `Store.configured()` swap, plus it *removes* the dev-only shared-instance wiring:

```diff
- @State private var paywallService: SimulatedPaywallService
  @State private var store: AppStore

  init() {
-     let service = SimulatedPaywallService()
-     _paywallService = State(initialValue: service)
-     _store = State(initialValue: .configured(paywallService: service))
+     _store = State(initialValue: .configured())   // constructs RevenueCatPaywallService internally
  }
```

```diff
- import SwiduxDevPaywallUI
+ import SwiduxRevenueCatPaywallUI

- .devPaywall(state: store.paywall, service: paywallService) { store.send(.paywall($0)) }
+ .revenueCatPaywall(state: store.paywall) { store.send(.paywall($0)) }
```

`Store.configured()` drops the `paywallService:` parameter and constructs the vendor service internally, so the "construct the service only inside `Store.configured()`" rule re-applies with no exception. Everything else — gating, actions, reducer, mapper, tests — is untouched.
