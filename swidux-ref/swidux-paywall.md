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

## Plugin construction in `Store.configured()`

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
