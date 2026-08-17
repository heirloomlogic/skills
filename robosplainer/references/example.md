<!--
A real, unedited output of this skill: HeirloomKit PR #66, a 305-line code change.
306 prose words, five walkthrough units, no risks section. Read it when the shape is unclear.
-->

# The elevation fill picks its own colour

`GlassFrameLayout` now hands back finished `Color`s for the dark-mode elevation lift and the selection wash, so the view modifier no longer decides a hue that no test can reach. [PR #66](https://github.com/heirloomlogic/HeirloomKit/pull/66) — 256 added, 49 deleted, 5 files.

A `.glassFrame` on the opaque fill and the pre-26 material fallback gets no `glassEffect`, so it shows depth as a value ladder: in dark mode `hard`, `medium` and `soft` paint a white overlay at 0.030, 0.055 and 0.085 opacity. `GlassFrameLayout.elevationLift` gave the number, but the `.white` was written in a `private var` on the `@MainActor` modifier, where no test could see it. Issue #55 shipped that way once — a darkening tint, every test green, because the tests only checked numbers.

**The layout enum returns the colour**

```swift
static func elevationFill(for depth: GlassDepthStyle, in colorScheme: ColorScheme) -> Color? {
    let lift = elevationLift(for: depth, in: colorScheme)
    return lift > 0 ? .white.opacity(lift) : nil
}
```

`Sources/HeirloomKit/Components/GlassFrame.swift:504`. `nil` rather than a clear colour, so the caller paints no layer at all — that is every light-mode frame.

**The call site picks, it does not decide**

```swift
// before
if case .selectionMark(let accent, .outline) = depth {
    return accent.color.opacity(0.07)
}
let lift = GlassFrameLayout.elevationLift(for: depth, in: colorScheme)
return lift > 0 ? .white.opacity(lift) : nil

// after
GlassFrameLayout.selectionWash(for: depth)
    ?? GlassFrameLayout.elevationFill(for: depth, in: colorScheme)
```

`GlassFrame.swift:280`. Both branches now come from `GlassFrameLayout`, and the `??` only chooses which `nil` wins: `elevationLift` returns 0 for `.selectionMark` by construction.

**One wash, both fill paths**

```swift
static func selectionWash(for depth: GlassDepthStyle) -> Color? {
    guard case .selectionMark(let accent, .outline) = depth else { return nil }
    return accent.color.opacity(0.07)
}
```

`GlassFrame.swift:517`. That `0.07` was written out twice, once per fill path, which is how a selected card comes to change shade with the OS version. The glass path at `:306` now calls the same helper, and `glassTint` drops its `lift` parameter because it already holds `depth` and `colorScheme`.

**One rule, three sites**

```swift
func expectLighteningTint(
    _ tint: Color,
    in colorScheme: ColorScheme,
    sourceLocation: SourceLocation = #_sourceLocation
) {
    #expect(
        tint.resolvedLuminance(in: colorScheme) > 0.9,
        "A lift must lighten its ground, not darken it — see #55.",
        sourceLocation: sourceLocation
    )
}
```

`Tests/HeirloomKitTests/TintDirectionExpectations.swift:30`. `resolvedLuminance` ignores alpha, so white reads 1.0 at any opacity and black reads 0.0 — the check is on direction, not strength. `NeutralGlassTintTests` and `CapsuleBarLogicTests.IndicatorTintTests` drop their inline copies and call it.

**The guard the whole change buys**

```swift
@Test(
    "Dark-mode elevation fill is a lightening colour",
    arguments: GlassFrameTests.liftingDepths
)
func darkElevationFillLightens(_ depth: GlassDepthStyle) throws {
    let fill = try #require(GlassFrameLayout.elevationFill(for: depth, in: .dark))
    expectLighteningTint(fill, in: .dark)
}
```

`Tests/HeirloomKitTests/GlassFrameTests.swift:387`. The author wrote `.black` first and watched these three cases fail while every magnitude assertion stayed green. Every shipped value is unchanged; nothing renders differently.
