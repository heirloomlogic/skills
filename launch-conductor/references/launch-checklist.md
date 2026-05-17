# Launch Checklist (generic, stack-agnostic)

The path from a feature-complete iOS/macOS app to public App Store release —
the last 10%. Use this when decomposing a workstream into a per-app note.
Sections map to the canonical `phase` values; a phase is complete when all its
items are checked, which is how `phase` is inferred during reconciliation.

This is **stack-agnostic by design**. Items name a *capability*, not a vendor.
Where an item says "paywall", the app might use RevenueCat, StoreKit 2, or
nothing (free app — delete the item). Adapt wording to whatever the user
actually uses; **delete inapplicable items** so `percent_to_release` stays
honest. You track *whether* each capability is done and verifiable — never how
to implement it.

Each item's sub-bullet is the acceptance criterion: "done" must be checkable
without judgment. Items not every app needs are marked *(if applicable)*.

---

## Phase: `wiring` — launch-tail integration complete

### Monetization / paywall *(if the app charges)*

- [ ] Purchase + restore wired and tested on a real device (sandbox)
  - A real sandbox purchase unlocks entitlement; restore works on a fresh install.
- [ ] Every paid feature is gated behind the entitlement check
  - Nothing that should be paid is reachable for free; verified by walking the app signed out of any entitlement.
- [ ] Subscription management / manage-subscriptions path reachable *(if subscriptions)*
  - User can reach the system manage-subscriptions screen from the app.

### Analytics *(if the app reports analytics)*

- [ ] Analytics SDK initialized only in release/intended builds
  - No analytics in debug unless intended; key from release config, not hardcoded.
- [ ] The launch-critical funnel is instrumented
  - First-run, activation, paywall view, purchase, and core action events fire and appear in the provider's live view.
- [ ] User/device identity and opt-out handled
  - Stable identity set; a user-facing opt-out exists and actually stops collection.

### Remote killswitch / forced-update *(strongly recommended)*

- [ ] App can be remotely blocked or forced to update post-launch
  - A remote config flips a block/least-supported-version gate; the blocking UI renders; verified against a test config.
- [ ] Killswitch config hosted at a stable production URL with offline fallback
  - URL serves over HTTPS; app degrades sanely (cached/last-known) when it's unreachable.

### Feature flags / remote config *(if used for launch gating or A/B)*

- [ ] Launch-gated features sit behind flags with safe defaults
  - Default-off where risky; flipping the flag changes behavior without a new build.

### Release configuration & secrets hygiene

- [ ] Production keys/endpoints separated from debug, selected by build config
  - Release build uses prod credentials/URLs; debug uses non-prod; no manual edit-before-archive step.
- [ ] No secret or token in plaintext in the shipped binary
  - A `strings` pass on the built `.app` surfaces no API key/token value.

### Code health gate

- [ ] Lint/format clean and the project builds Release with no warnings-as-errors surprises
  - `Release` archive builds clean; formatter/linter (whatever the project uses) passes.
- [ ] *(if the app has CI)* CI is green on the release commit
  - Plain manual line — only if CI exists.

---

## Phase: `internal-testing` — it runs and survives use

- [ ] Builds and runs clean on a physical device for every supported platform
  - Release configuration; no debug-only shortcuts.
- [ ] Core flows dogfooded end to end
  - First-run, primary task, purchase, settings — exercised on device; bugs logged as items.
- [ ] Crash-free through the main flows
  - No crashes/hangs in a full manual pass; concurrency/runtime warnings triaged.
- [ ] App icon, launch screen, display name, marketing version + build number set
  - Final assets in place; version is the intended public version.
- [ ] Privacy: Info.plist usage strings + required-reason API declarations complete
  - Every accessed sensitive API has a purpose string; privacy manifest present and accurate.

---

## Phase: `testflight` — external beta

- [ ] App record created in App Store Connect; bundle ID and signing resolve
  - Archive validates; provisioning/profiles correct.
- [ ] Build uploaded and processed
  - Visible in TestFlight; no missing-compliance / ITMS errors.
- [ ] Export compliance answered
  - Encryption question answered (set the Info.plist key if it ends the prompt).
- [ ] External testers invited and on the build
  - At least one external tester has it installed.
- [ ] Beta feedback triaged
  - Crash/feedback reviewed; launch-blocking issues added as items, the rest parked post-launch.

---

## Phase: `app-review` — submitted to Apple

- [ ] Store listing complete
  - Name, subtitle, description, keywords, support/marketing URLs, category.
- [ ] Screenshots / previews uploaded for every required device size
  - Current UI, required sizes, no placeholder art.
- [ ] App privacy ("nutrition label") answered to match actual data use
  - Matches the app's real collection (analytics, purchases); consistent with the privacy manifest.
- [ ] Age rating questionnaire completed
- [ ] Pricing / availability set; IAP products "Ready to Submit" *(if monetized)*
  - Products/subscriptions ready, prices and territories set.
- [ ] Submitted for review
  - Status "Waiting for Review" / "In Review". `blocked_by: waiting on Apple`; next action is *monitor*.
- [ ] Rejection responded to *(if rejected)*
  - Reply or resubmit; reason captured in the note.

---

## Phase: `released` — live

- [ ] Released to the App Store
  - Status "Ready for Sale"; store URL resolves.
- [ ] Production smoke test from the public build
  - Install from the App Store; purchase, analytics, killswitch verified live.
- [ ] Post-launch parking lot triaged
  - Deferred features/bugs moved into the next milestone, not lost.

---

## Optional non-app workstream (e.g. a marketing/teaser site)

Only when the user actually has one. Phases: `building` → `staging` → `live`.
It competes on the board; if it gates a submission (App Store Connect requires
a live privacy-policy URL), that dependency can promote it above app work.

### `building`
- [ ] Site shell + content for each launching app
- [ ] Privacy policy + terms reachable at stable URLs
  - Required for App Store Connect submission — can block an app's `app-review`.

### `staging`
- [ ] Deployed to a staging URL, reviewed on mobile + desktop
- [ ] Links / capture / analytics verified

### `live`
- [ ] Live on the production domain (DNS/TLS resolved)
- [ ] Each app's page updated to the real App Store link as it releases
  - One sub-item per app; closes as each app goes `released`.
