# SwiduxPersistence + SwiduxCloudKitSync Wiring

First-class persistence for Swidux apps. Two opt-in products absorb the SwiftData boilerplate apps used to hand-write — `@Model` shadow classes, a per-type DB actor, and a `StateWriter` per `EntityStore`:

- **`SwiduxPersistence`** — local SwiftData persistence. The `@Persisted` macro generates an entity's `@Model` shadow + converters; a generic `EntityDB` actor and a `PersistenceCoordinator` build the container, synthesize the writers, reuse the core `PersistencePlugin`, and expose **only** a merge-based re-hydration path.
- **`SwiduxCloudKitSync`** — opt-in iCloud sync on top: a runtime opt-out toggle, launch-time entitlement/account detection that degrades to local-only instead of crashing, and a merge-based remote-change observer.

This is the recommended path. The hand-wired `PersistencePlugin` + `StateWriter` + your own `@Model`/DB actor (see `swidux-patterns.md` and DocC `PersistenceMiddlewareGuide`) is the low-level fallback — reach for it only when you need control the macro can't express.

## Two products, one decision

The split is deliberate and load-bearing for App Review:

- **Local-only** → link `SwiduxPersistence` alone. It needs **no iCloud, CloudKit, or Push entitlements** — only the sandbox `com.apple.security.network.client` entitlement if the app already makes network calls (killswitch, analytics, feature flags). Adding sync entitlements to a local-only app is dead configuration and an App Review risk.
- **Cross-device sync** → also link `SwiduxCloudKitSync`. **Linking this product is the single signal that the app has taken on the iCloud / CloudKit / Push entitlement family.** Same posture the rest of Swidux uses for vendors: defer the heavy decision. Start local-only; add the sync product (and its entitlements) when cross-device sync is actually a requirement, not up front.

## `@Persisted` — generate the SwiftData shadow

`@Persisted` lives in `SwiduxPersistence`. Annotate a value-type domain entity that already satisfies the `EntityStore` contract (`Identifiable & Equatable & Sendable`, `ID == UUID`):

```swift
import SwiduxPersistence

@Persisted
nonisolated struct Card: Identifiable, Equatable, Sendable {
    var id: UUID
    var quote: String
    var createdAt: Date
}
```

This generates `CardModel: @Model final class` (conforming to `PersistableModel`) with the converter trio `init(from:)` / `toDomain()` / `update(from:)` (the last never reassigns `id`), plus `extension Card: PersistableEntity { typealias Model = CardModel }`. By default every stored property is mirrored directly — SwiftData persists scalars *and* `Codable` composites natively, so no manual blob columns.

**`@Persisted` is for domain entities; `@Swidux` is for state containers** (`AppState`, `@Slice` slices). Different layers — they never apply to the same type. They emit differently-named peers (`{Type}Model` vs `{Type}Observer`), so in the rare case a type needs both, they compose without conflict.

No `@Attribute(.unique)` is generated on `id`: CloudKit forbids unique constraints. Identity is enforced by upsert-by-`id` inside `EntityDB`, so the *same* generated model backs both local and synced containers.

### Property markers

A macro can't infer relationships, foreign keys, or derived fields. Four markers (named to avoid SwiftData's own `@Attribute`/`@Relationship`/`@Transient`) override the default mirroring:

```swift
@Persisted
nonisolated struct Card: Identifiable, Equatable, Sendable {
    var id: UUID
    var quote: String

    @Inline var styling: TextStyling                 // one opaque JSON Data column
    @ForeignKey var deckID: UUID                      // scalar parent reference
    @Relation(deleteRule: .cascade, inverse: \TagModel.card)
    var tags: [Tag]                                   // SwiftData relationship
    @Ignored var renderedPreview: String?             // derived; omitted from the model
}
```

| Marker | Effect |
|---|---|
| *(none)* | Mirror directly as `var name: T`. SwiftData persists scalars and `Codable` composites. |
| `@Inline` | Force a `Codable` value into a single opaque JSON `Data` column, exposed through a computed accessor of the original type. Keeps a CloudKit record compact; sidesteps SwiftData `Codable`-attribute edge cases. |
| `@ForeignKey` | Intent/documentation marker on a `UUID`; functionally a mirrored scalar column. |
| `@Relation(deleteRule:inverse:)` | A SwiftData relationship to another `@Persisted` entity. The property's type references the **domain** type (`[Tag]` / `Tag?` / `Tag`); the model substitutes the `…Model` shadow and the converters map element-by-element. `inverse` is a key path on the *generated model* (`\TagModel.card`). `deleteRule` is a `SwiduxDeleteRule` (`.cascade`, `.nullify`, `.noAction`, `.deny`). |
| `@Ignored` | Exclude a derived/denormalized field. **Must be optional** so `toDomain()` can reconstruct it as `nil` on load — a diagnostic fires on a non-optional `@Ignored`. |

## Local wiring

### 1. Add the dependency

```swift
.target(name: "MyApp", dependencies: ["Swidux", "SwiduxPersistence"])
```

### 2. Put the `EntityStore` on state

```swift
@Swidux
nonisolated struct AppState: Equatable, Sendable {
    var cards: EntityStore<Card> = .init()
}
```

Reducers mutate `state.cards` like any `EntityStore` (`state.cards[id] = card`, `.modify(id) { … }`, `state.cards[id] = nil`); every change is recorded for the plugin to drain.

### 3. Build the coordinator in `Store.configured()`

`Store.configured()` becomes `async` (hydration awaits disk):

```swift
import SwiduxPersistence

extension Store where State == AppState, Action == AppAction {
    static func configured() async -> AppStore {
        let container = try! ContainerFactory.makeLocalContainer(models: [CardModel.self])

        let persistence = PersistenceCoordinator<AppState, AppAction>(
            entities: [.entity(\.cards)],
            container: container,
            debounce: .milliseconds(250)   // default
        )

        let plugins = PluginHost<AppState, AppAction>()
        // Register UndoPlugin first if you use it — snapshots must precede writes.
        plugins.register(persistence.corePlugin)

        var initial = AppState()
        await persistence.hydrate(into: &initial)   // first-load: fill EntityStores from disk

        return Store(initialState: initial, reducer: { … }, plugins: plugins)
    }
}
```

You write no `StateWriter` body, no `@Model`, no DB actor. `PersistenceCoordinator.init(entities:container:debounce:)` synthesizes one writer per registered `.entity(\.keyPath)`, wraps the core `PersistencePlugin` (exposed as `persistence.corePlugin`), and owns the `EntityDB` behind a swappable `DatabaseHandle`.

### 4. Flush on background

Writes are debounced — drain them when the app backgrounds or terminates:

```swift
.onChange(of: scenePhase) { _, phase in
    if phase == .background {
        Task { await persistence.corePlugin.flush() }
    }
}
```

### Multiple entities and ordering

One `.entity(\.keyPath)` per `EntityStore`; pass every generated `…Model` to the container:

```swift
let persistence = PersistenceCoordinator<AppState, AppAction>(
    entities: [.entity(\.decks), .entity(\.cards), .entity(\.tags)],
    container: try! ContainerFactory.makeLocalContainer(
        models: [DeckModel.self, CardModel.self, TagModel.self]
    )
)
```

Writers flush in registration order. If entity B holds a `@Relation` to A, register A first so B's upsert finds A's row.

## `hydrate` vs `rehydrate` — the rule-#8 guarantee, enforced by the API

This is the most important distinction in the whole layer:

- **`hydrate(into:)` is first-load only.** It *replaces* each `EntityStore` with the on-disk rows. Safe only at launch, before any live edits exist.
- **`rehydrate(into:)` is the only post-launch refresh path.** It *always merges*, preferring in-memory values, and absorbs disk-only rows. Mid-session, in-memory state is authoritative — it may hold unflushed writes still in the debounce window or in-progress edits bound to live UI. A wholesale replace silently clobbers them and surfaces as dropped keystrokes / lost edits.

Because the coordinator only exposes `rehydrate` (merge) for refresh, rule #8 is enforced by construction — there's no merge closure to remember to write. This is what neutralizes the classic CloudKit trap: `.NSPersistentStoreRemoteChange` fires for the app's **own** local saves, not just remote-device imports, so a "re-hydrate on remote change" observer feeds the app its own writes. Because rehydrate merges, that's a no-op instead of visible data loss.

## CloudKit sync

`SwiduxCloudKitSync` reuses the same `@Persisted` models and the same `PersistenceCoordinator`. Sync only changes how the `ModelContainer` is built (`cloudKitDatabase` set vs `.none`) and adds the toggle, the preflight, and the remote observer.

### Step 1: Apple Developer portal setup

CloudKit needs capabilities on the App ID and a CloudKit container, configured at <https://developer.apple.com/account/resources/identifiers>:

1. **Identifiers → your App ID** (or create one matching the bundle id, e.g. `com.yourcompany.yourapp`).
2. **Enable iCloud** with **Include CloudKit support**.
3. **Enable Push Notifications** on the same App ID — CloudKit delivers remote-change notifications over APNs, which drives `.NSPersistentStoreRemoteChange`.
4. Switch the filter to **iCloud Containers**, create `iCloud.<your-bundle-id>` (e.g. `iCloud.com.yourcompany.yourapp`), and **assign it** back on the App ID.
5. Save. Xcode regenerates the provisioning profile next time it signs the app.

The built app must carry:

| Entitlement | Value |
|---|---|
| `com.apple.developer.icloud-container-identifiers` | `[iCloud.com.yourcompany.yourapp]` — **non-empty**, matching the id passed in code |
| `com.apple.developer.icloud-services` | `[CloudKit]` |
| `aps-environment` | `development` in dev builds, `production` in release archives |

An **empty** `icloud-container-identifiers` array paired with a `CloudKit` services line is misconfiguration, not sync — `SyncPreflightService` reports the app unavailable. The portal container id, the entitlement, and the `cloudKitContainerID` passed in code must all match.

### Step 2: Xcode capabilities

In the app target's **Signing & Capabilities**:

1. **+ Capability → iCloud** → check **CloudKit**, select the `iCloud.<bundle-id>` container.
2. **+ Capability → Background Modes** → check **Remote notifications** (receives CloudKit's silent push that fires `.NSPersistentStoreRemoteChange`).
3. **Push Notifications** is added automatically with CloudKit; confirm it's present.

For a SwiftPM-defined app, add the matching keys to an `.entitlements` file and point the target's `CODE_SIGN_ENTITLEMENTS` at it.

### Step 3: Dependency + sync-mode container at launch

```swift
.target(name: "MyApp", dependencies: ["Swidux", "SwiduxPersistence", "SwiduxCloudKitSync"])
```

Read the desired mode **before** building the container (mode determines the `ModelConfiguration`):

```swift
import SwiduxPersistence
import SwiduxCloudKitSync

let containerID = "iCloud.com.yourcompany.yourapp"
let mode = resolveDesiredSyncMode(from: env.keyValue)   // default .iCloud (opt-out)

let container = try CloudContainerFactory.makeContainer(
    models: [CardModel.self],
    mode: mode,
    cloudKitContainerID: containerID   // nil ⇒ .automatic
)

let persistence = PersistenceCoordinator<AppState, AppAction>(
    entities: [.entity(\.cards)],
    container: container
)
plugins.register(persistence.corePlugin)
await persistence.hydrate(into: &initial)
```

`resolveDesiredSyncMode(from:default:)` reads the persisted `KVKey.syncMode`. The default for any app linking this product is **sync-on with opt-out** (`.iCloud`); pass `default: .localOnly` to make sync strictly opt-in. (`SyncMode` is `.localOnly` / `.iCloud`.) `CloudContainerFactory` and `ContainerFactory` share one store URL across both modes, so toggling never moves or loses local rows — only the CloudKit mirror attaches or detaches.

### Step 4: The runtime sync toggle

`SyncCoordinator` owns the opt-in/opt-out toggle:

```swift
let sync = SyncCoordinator<AppState, AppAction>(
    persistence: persistence,
    models: [CardModel.self],
    mode: mode,
    preflight: .live(containerID: containerID),
    keyValue: env.keyValue,
    cloudKitContainerID: containerID
)
```

From a Settings toggle:

```swift
let status = await sync.setSyncEnabled(isOn, into: &state)
state.persistence.syncMode = sync.mode
state.persistence.syncStatus = status
```

`setSyncEnabled(_:into:)` flushes pending writes, resolves availability, rebuilds the container in the *effective* mode (CloudKit only when actually usable, else a local fallback), swaps the active database behind the coordinator's `DatabaseHandle`, persists the user's **choice** (not the fallback) for next launch, and re-hydrates via **merge** (never replace). It returns the resolved `SyncStatus`.

### Step 5: Detect availability and degrade gracefully

`SyncPreflightService` probes `FileManager.ubiquityIdentityToken` and `CKContainer.accountStatus`; `SyncStatus.resolve(desired:entitled:account:)` maps the result to a verdict-in-state enum (mirroring `KillswitchVerdict`):

| `SyncStatus` | Meaning | Response |
|---|---|---|
| `.localOnlyByChoice` | User opted out | Healthy; on-device. |
| `.syncing` | Entitled, signed in, active | Healthy. |
| `.unavailableNotSignedIn` | Entitled, no iCloud account | Gentle "Sign in to iCloud" banner; never assert. `isUserActionable == true`. |
| `.unavailableRestricted` | MDM/parental restriction | Inform; run local-only. |
| `.misconfiguredNoEntitlement` | Sync requested but **not entitled** — a build/signing bug | Degrade to local-only; `assertionFailure` in **DEBUG only**, never crash release. |

`.isDegraded` is true for everything except `.syncing` / `.localOnlyByChoice`. Run the probe at launch and on `scenePhase → .active`, and disable the Settings toggle when the status isn't user-actionable:

```swift
let status = await sync.currentStatus()
state.persistence.syncStatus = status
```

`SyncPreflightService.live(containerID:)` is the real probe; `.mock(ubiquityToken:account:)` is the deterministic test stub. The Keychain `−34018` condition (from `KeychainKeyValueStore`, used for the analytics device-id) is a *separate*, always-present capability — it stays where it is and is **not** folded into the sync preflight.

### Step 6: Observe remote changes

```swift
let observer = RemoteChangeObserver(debounce: .seconds(2)) {
    await persistence.rehydrate(into: &state)   // merge, never replace
}
observer.start()
```

`.NSPersistentStoreRemoteChange` also fires for the app's own local saves; because rehydrate merges preferring in-memory, feeding the app its own writes is a no-op. Call `observer.stop()` before a sync toggle (the coordinator rebuilds the container).

### Optional: a `PersistenceState` slice

Embed `@Slice var persistence: PersistenceState` on `AppState` to drive a launch hydration gate and a sync toggle. It carries `hydrationPhase` (`.loading` / `.ready` / `.failed(String)`), `syncMode` (what the user asked for, persisted), and `syncStatus` (the resolved runtime reality the app updates from the `SyncCoordinator`).

### Privacy copy — be accurate about CloudKit semantics

- Turning sync **off** is reversible and **non-destructive**: it stops syncing and keeps data on this device. Data already in the user's private CloudKit database stays there until an explicit, confirmed delete — opt-out is *not* deletion.
- Turning sync **on** later merges local and server rows; it never clobbers.

Example UI copy: *"By default your data is stored only on this device. If you turn on iCloud Sync it is stored in your private iCloud account and synced across your devices. Turning it off stops syncing and keeps your data on-device; data already in iCloud remains in your account until you delete it."*

## Testing

The whole stack runs against an in-memory SwiftData store — unit-testable with no disk and no CloudKit. Tests use Swift Testing (`import Testing`, `@Test`, `#expect`).

```swift
let container = try ContainerFactory.makeInMemoryContainer(models: [CardModel.self])
let db = EntityDB(modelContainer: container)

try await db.upsert(Card(id: id, quote: "hi", createdAt: .now), as: CardModel.self)
let all = try await db.fetchAll(CardModel.self)
#expect(all.first?.quote == "hi")
```

- **Rule-#8 merge guarantee**: seed the store, make a live in-memory edit, call `coordinator.rehydrate(into:)`, assert the live edit survives.
- **Sync, no entitlements**: `SyncStatus.resolve(desired:entitled:account:)` truth table, `SyncPreflightService.mock(ubiquityToken:account:)`, the `KVKey.syncMode` round-trip, and the opt-out toggle path against an in-memory container.
- **Real two-device mirroring** needs entitlements and a signed-in device — cover it with a manual smoke test: two-device sync, opt-out keeps data local, opt-in merges, signed-out iCloud degrades with a banner, and a build missing the entitlement trips the DEBUG assertion.

## See also

- DocC `HowToAddPersistence`, `HowToAddICloudSync`, `MacrosReference` (the `@Persisted` section), `PersistenceMiddlewareGuide`.
- `SKILL.md` rule #8 (the recommended-path summary and the `hydrate`/`rehydrate` distinction).
- `swidux-patterns.md` (the hand-wired low-level fallback).
