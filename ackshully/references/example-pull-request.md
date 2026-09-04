<!--
A real output of this skill, restructured for progressive disclosure: HeirloomKit PR #66, a 305-line code change.
Opener, longer version, four detail sections, no risks section. 461 prose words.
-->

# The elevation fill picks its own colour

Well actually, the dark-mode elevation lift was never a number. It was a colour, and the colour lived in a `private var` on a `@MainActor` view modifier where no test could reach it. Issue #55 shipped a darkening tint that way once, with every test green, because the tests only checked magnitudes.

[PR #66](https://github.com/heirloomlogic/HeirloomKit/pull/66) — 256 added, 49 deleted, 5 files.

## The longer version

A `.glassFrame` shows depth two ways. On iOS 26 it gets a real `glassEffect`. On the opaque fill and on the pre-26 material fallback it gets nothing, so it has to fake depth with a value ladder: in dark mode the `hard`, `medium` and `soft` styles paint a white overlay at 0.030, 0.055 and 0.085 opacity.

`GlassFrameLayout.elevationLift` supplied those three numbers, and the tests checked them. The `.white` they multiplied was written at the call site, inside the modifier, on a type the test target cannot instantiate. So the sign of the effect — lighten or darken — was the one part of it nothing asserted. Issue #55 is what that costs.

This change moves the decision down to `GlassFrameLayout`, which is a plain enum with static methods and no actor isolation. It returns `Color?` now, not `Double`: `elevationFill` for the depth ladder, `selectionWash` for the accent tint on a selected outline. The modifier picks between them and paints. Both fill paths — glass and opaque — call the same two helpers, which also removes a duplicated `0.07` that had let a selected card change shade with the OS version.

The tests then assert the thing that actually broke. `resolvedLuminance` ignores alpha, so a lift reads near 1.0 whatever its opacity, and the check is on direction rather than strength. No shipped value changed and nothing renders differently.

## The layout enum returns the colour

```swift
static func elevationFill(for depth: GlassDepthStyle, in colorScheme: ColorScheme) -> Color? {
    let lift = elevationLift(for: depth, in: colorScheme)
    return lift > 0 ? .white.opacity(lift) : nil
}
```

`Sources/HeirloomKit/Components/GlassFrame.swift:504`. It returns `nil` rather than a clear colour, so the caller paints no layer at all — that is every light-mode frame.

## The call site picks, it does not decide

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

`GlassFrame.swift:280`. The `??` only chooses which `nil` wins, because `elevationLift` returns 0 for `.selectionMark` by construction.

## One wash, both fill paths

```swift
static func selectionWash(for depth: GlassDepthStyle) -> Color? {
    guard case .selectionMark(let accent, .outline) = depth else { return nil }
    return accent.color.opacity(0.07)
}
```

`GlassFrame.swift:517`. That `0.07` was written out twice, once per fill path, which is how a selected card comes to change shade with the OS version. The glass path at `:306` now calls this helper too, and `glassTint` drops its `lift` parameter because it already holds `depth` and `colorScheme`.

## The assertion is on direction, not strength

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

`Tests/HeirloomKitTests/TintDirectionExpectations.swift:30`. `NeutralGlassTintTests` and `CapsuleBarLogicTests.IndicatorTintTests` drop their inline copies and call this. The new parametrised test at `GlassFrameTests.swift:387` runs it over every lifting depth in dark mode; the author wrote `.black` first and watched those three cases fail while every magnitude assertion stayed green.
