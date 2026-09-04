<!--
A real output of this skill, restructured for progressive disclosure: HeirloomKit PR #66, a 305-line code change.
Opener, longer version, four detail sections, no risks section.
The opener and the longer version name no term they do not explain; the detail sections below them are written for a reviewer.
-->

# The tests could not see the colour, so a shading bug shipped

In dark mode this app lifts a panel off its background by washing it with a little white. That wash once shipped darkening instead, with every test green: the tests checked its strength, never its colour. This change moves the colour somewhere a test can reach, and the tests now check which way it goes.

[PR #66](https://github.com/heirloomlogic/HeirloomKit/pull/66) — 256 added, 49 deleted, 5 files.

## The longer version

A panel in this library is drawn inside a glass frame — a frosted backing that sits behind the content. On recent versions of iOS the system draws real glass for it. Everywhere else the frame has to fake depth. It fakes it by painting a thin white layer over the panel. The layer is 3% opaque for the flattest panel, 5.5% for the middle one, 8.5% for the closest. Those three numbers are the depth ladder.

The numbers came from a helper the tests could call, `GlassFrameLayout.elevationLift`. The white they were multiplied by was written elsewhere, inside view code the test target cannot even create. So the tests could prove the wash was faint. They could not prove it was white rather than black. Issue #55 is what that gap cost: a darkening wash shipped, and every test stayed green.

This change moves the decision down into `GlassFrameLayout`, a plain lookup table with no view code in it. A test can call it directly. It hands back a colour now, not a number: `elevationFill` covers the depth ladder, `selectionWash` covers the tint on a selected panel. The view code picks one of the two and paints it. Both drawing paths, real glass and painted fallback, now call the same two helpers. That deletes a duplicated 7% which had let a selected panel change shade with the iOS version.

The tests then check the thing that actually broke: not how strong the wash is, but which way it goes. No shipped value changed and nothing renders differently.

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
