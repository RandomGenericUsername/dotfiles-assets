# Icons manifest — semantic role migration (REQ-008 Phase A)

**Status: proposal only. No pin changed, no render changed.**
This is the Phase A deliverable of `tickets/req-008-icons-role-mappings`: one proposed
semantic role and one surface class for every placeholder in
`icons/mappings/icons.yaml`, plus the role vocabulary (`vocabulary.json`) and the
validator that will hold Phase B to it. **Phase B is blocked on user review** — the
pins in `icons.yaml` and `defaults.yaml` are untouched until this table is signed off.

Scope of the proposal: **22 groups, 136 variants** — 28 group-level token rows,
38 variant-level override rows, 4 `defaults.yaml` rows, covering **232 placeholder
occurrences across the 136 variants** (the complete inventory is the last table).

## Why the current pins cannot stay

The pins were written against a 16-colour carrier list whose positions do not mean
the same thing under the producer's current role order. Under tpr, `color0..15`
resolve to (in order) `surface, error, tertiary, secondary, primary,
surface_variant, outline_variant, on_surface, outline, error_container,
tertiary_container, secondary_container, primary_container, surface_container,
surface_container_high, on_surface_variant`. The evidence is the producer's
`LEGACY_COLOR_ORDER` (`theme-producer/src/theme_producer/domain/services.py:45-62`)
and `MaterialRole` (`theme-producer/src/theme_producer/domain/enums.py:17-76`).

Concrete failures in the current manifest, all reproducible from the pins:

| Pin | Current value | What it resolves to now | Effect |
|---|---|---|---|
| `battery.COLOR_FOREGROUND` (`icons.yaml:4`) | `color15` | `on_surface_variant` | bar ink is a de-emphasised grey, not the brightest neutral |
| `battery.COLOR_ACCENT` (`icons.yaml:3`) | `color13` | `surface_container` | the charging bolt is near-black in dark mode |
| `network.COLOR_CROSS` / `COLOR_WARNING` (`icons.yaml:87-88`) | `color13` | `surface_container` | the failure marker disappears into a dark bar |
| `power-menu.COLOR_SECONDARY` (`icons.yaml:199`) | `color1` | `error` | a red gradient stop that no one asked for |
| `capture-tool.camera-accent` / `video-accent` (`icons.yaml:332,337`) | `color6` | `outline_variant` | "success" reads as a neutral grey / disabled |
| `capture-tool.warning-caution` (`icons.yaml:342`) | `color3` | `secondary` | nothing about it is a caution hue |
| `settings-panel.wifi` / `bluetooth` (`icons.yaml:490,504`) | `color13` | `surface_container` | the on-state glyph is the same near-black as the panel |
| `settings-panel.*-signal-*` (`icons.yaml:543-591`) | `color12/13` + `color0` | `primary_container`/`surface_container` + `surface` | dark ink on a dark badge in dark mode, light on light in light mode — the pair inverts |
| `media-transport-panel.COLOR_BACKGROUND` (`icons.yaml:785`) | `color6` | `outline_variant` | the comment names the primary-action role; the value is outline grey |
| `ui.COLOR_ACCENT` (`icons.yaml:397`) | `color12` | `primary_container` | declared but unused by any current template |
| `defaults.COLOR_SECONDARY` (`defaults.yaml:17`) | `accent` | alias → `primary` | the token says "secondary", the alias resolves to primary |
| `defaults.COLOR_ACCENT` (`defaults.yaml:18`) | `accent-muted` | alias → `secondary` | the token says "accent", the alias resolves to the neutral pole |

Two further facts make the vocabulary the right layer to fix this:

- **`foreground` is an alias, not a role.** 24 of the 70 mapping values are the
  literal `foreground`; the producer resolves it to `on_surface`
  (`theme-producer/src/theme_producer/adapters/projections/registry.py:56-71`). That
  is correct on a panel and wrong over the wallpaper, but nothing in the manifest
  says which surface a group is on. Surface classes make that explicit.
- **The producer now has a role for the wallpaper question.** `on_backdrop`
  (theme-producer REQ-022) is "ink over the wallpaper's bar band": the neutral-pole
  candidate with maximum WCAG contrast against the top 48 rows of the image. It
  replaces the runtime contrast guard at the data layer.

## Surface classes

`surface` is the missing datum this proposal adds to the contract. It is declared per
group and optional per variant (a variant that paints its own container is a different
surface). It is **optional in Phase A** — no value is set in `icons.yaml` yet, because
setting one is a render input and Phase A must not change renders.

| Class | Meaning | Ink contract |
|---|---|---|
| `wallpaper` | composited directly over the wallpaper (floating bar glyph, full-screen wallpaper button) | `on_backdrop` for the glyph ink; accents may be `primary`/`tertiary`/`error` but shape must still carry the state |
| `dark-glass` | translucent sheet, `alpha(surface*, ~0.9)` over a transparent window | on-surface / on-container family for that sheet; `on_backdrop` is wrong because no wallpaper band is behind the glyph |
| `solid` | opaque surface, field, or a container the variant paints itself | on-surface / on-container family for that surface |

## Role-choice rules used in the tables

1. **Wallpaper → `on_backdrop`.** Battery, network, bluetooth, volume, microphone,
   btop, thunderbird, tray, power-menu, email-client, wallpaper-selector, settings,
   wlogout.
2. **Dark glass / solid → the on-surface family.** `on_surface` for default ink,
   `on_surface_variant` for de-emphasised ink, `on_primary*` / `on_*_container` for
   ink on a filled container.
3. **Accents → `primary`** for action/success/accent emphasis, **`tertiary`** for
   caution and secondary emphasis, **`secondary`** for a neutral emphasis stop,
   **`error`** for failure.
4. **Badges → container/on-container pairs.** A badge fill is `primary_container`
   (emphasis) or `surface_container_high` (neutral); its ink is the matching
   `on_*_container` / `on_surface`. See judgment call 1.
5. **Brand fills stay literal.** `app-icons` ships its own fills; it gets a surface
   class and no `color_mappings` row, because a brand mark recoloured by a theme is
   no longer a brand mark.
6. **Aliases are not roles.** `foreground`, `accent`, `accent-muted`, `warning` are
   producer aliases; the manifest carries role names only.

## Group proposals — surface and composition

| Group | Surface | Composition |
|---|---|---|
| `battery` | `wallpaper` | Bar battery level glyph; charging variants add an accent bolt. |
| `network` | `wallpaper` | Bar network glyphs; the cross/slash and warning shapes carry state. |
| `wlogout` | `wallpaper` | Full-screen wallpaper with transparent buttons — the glyph is on the wallpaper. |
| `power-menu` | `wallpaper` | Bar power glyph; one variant paints its own disc behind the ring. |
| `power-mode` | `dark-glass` | Power-mode row glyphs on the battery panel's dark glass. |
| `capture-tool` | `dark-glass` | Capture overlay/window glyphs on the capture panel's dark glass. |
| `email-client` | `wallpaper` | Bar mail glyph floating over the wallpaper. |
| `wallpaper-selector` | `wallpaper` | Bar wallpaper glyph floating over the wallpaper. |
| `wallpaper-progress` | `dark-glass` | Progress card glyphs inside a notification card (alpha surface over the wallpaper). |
| `btop` | `wallpaper` | Bar btop glyph: frame ink plus tick marks. |
| `thunderbird` | `wallpaper` | Bar mail glyph floating over the wallpaper. |
| `tray` | `wallpaper` | Bar tray glyph floating over the wallpaper. |
| `ui` | `solid` | Picker/field glyphs on a solid content surface, not the bar band. |
| `settings` | `wallpaper` | Bar settings glyph floating over the wallpaper. |
| `bluetooth` | `wallpaper` | Bar bluetooth glyph floating over the wallpaper. |
| `settings-panel` | `dark-glass` | Settings panel rows on dark glass; capability glyphs tint by state. |
| `brightness` | `wallpaper` | Bar brightness glyph floating over the wallpaper. |
| `volume` | `wallpaper` | Bar volume glyphs floating over the wallpaper; system copies on glass. |
| `microphone` | `wallpaper` | Bar microphone glyphs floating over the wallpaper; system copies on glass. |
| `app-icons` | `dark-glass` | Brand marks with literal fills; no placeholder, no role, no mapping. |
| `media-transport` | `dark-glass` | Transport glyphs in the audio popup's dark-glass rows. |
| `media-transport-panel` | `dark-glass` | Round filled transport button in an audio row: container + on-container ink. |

## Group-level token proposals

Every row is a mapping currently declared at group level. "Current value" is the
literal value in `icons.yaml` today; the rationale says what it resolved to and why
the proposed role is the intent.

| Group | Token | Current value | Proposed role | Surface | Rationale | Contrast note |
|---|---|---|---|---|---|---|
| `battery` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` | charging bolt is the active/accent emphasis inside the battery outline (was color13, i.e. surface_container: near-black in dark mode) | decorative emphasis; the outline ink still carries the shape, so a mid-tone primary below 4.5 does not erase the glyph |
| `battery` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `network` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `network` | `COLOR_CROSS` | `color13` | `error` | `wallpaper` | the cross/slash marks the failure state (was color13 = surface_container, i.e. near-invisible against a dark bar) | the slash is a shape signal first; the hue is a second cue, so a sub-4.5 error red does not lose the state |
| `network` | `COLOR_WARNING` | `color13` | `tertiary` | `wallpaper` | warning triangle on the no-internet variants; `warning` is the producer's stable alias for tertiary, so the role name is tertiary | shape carries the state; tertiary is a hue hint, not the only cue |
| `power-menu` | `COLOR_BACKGROUND` | `background` | `primary_container` | `wallpaper` | disc painted behind the glyph in the with-background variant (was `background` = surface, i.e. the same near-black as the bar) | container fill; the ink on top is on_primary_container, the Material-guaranteed pair |
| `power-menu` | `COLOR_SECONDARY` | `color1` | `secondary` | `wallpaper` | gradient mid-stop of the modern ring (was color1 = error, an unrelated red stop) | gradient stop between two theme hues; contrast is not load-bearing |
| `power-menu` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` | the power stroke is the accent arc of the ring (was color13 = surface_container, which erased it in dark mode) | accent arc; the ring outline stays on_backdrop, so the glyph reads even when primary is mid-tone |
| `power-menu` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `power-mode` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | row glyph on dark glass (declared `foreground`, an alias, not a role) | on_surface is the ink for surface_container surfaces; the panel background is alpha(surface_container, 0.94) |
| `capture-tool` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | base glyphs sit on the capture panel (was the `foreground` alias) | panel ink on dark glass |
| `capture-tool` | `COLOR_ACCENT` | `color13` | `primary` | `dark-glass` | the region selection accent (was color13 = surface_container: near-black on a dark panel) | accent outline around the selection; the panel ink carries the shape |
| `wallpaper-progress` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | card glyph on the notification glass (was the `foreground` alias) | card background is alpha(surface, 0.92): a glass sheet, so the panel ink applies, not on_backdrop |
| `btop` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `btop` | `COLOR_JOIN` | `color15` | `on_backdrop` | `wallpaper` | the tick marks around the frame are the same ink as the frame (was color15 = on_surface_variant, a muted grey) | same ink as the frame; splitting the two tokens would create a contrast mismatch on the same glyph |
| `thunderbird` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `tray` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `ui` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` | glyphs sit on the solid search field / content card (was color15 = on_surface_variant, a de-emphasised grey) | solid surface ink; on_backdrop would be wrong because there is no wallpaper band behind these glyphs |
| `ui` | `COLOR_ACCENT` | `color12` | `primary` | `solid` | declared but unused by current art (kept for forward compatibility; was color12 = primary_container) | not rendered today; the role keeps the declaration resolvable |
| `settings` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` | bar glyph; currently inherits the vocabulary's `foreground` alias | same band rule as every other wallpaper glyph |
| `bluetooth` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `settings-panel` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | default row ink on the panel (was the `foreground` alias) | panel ink on dark glass |
| `brightness` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` | bar glyph; currently inherits the vocabulary's `foreground` alias | same band rule as every other wallpaper glyph |
| `volume` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` | bar glyph; currently inherits the vocabulary's `foreground` alias | same band rule as every other wallpaper glyph |
| `microphone` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` | bar glyph; currently inherits the vocabulary's `foreground` alias | same band rule as every other wallpaper glyph |
| `media-transport` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | row glyph on the audio popup's dark glass (was the `foreground` alias; the group is not a bar group, so it never floated over the wallpaper) | panel ink on dark glass |
| `media-transport-panel` | `COLOR_BACKGROUND` | `color6` | `primary` | `dark-glass` | the round container is a primary action (the comment names the GUI-unification primary role; the pin was color6 = outline_variant, a neutral grey) | filled action container; its ink is on_primary, the Material pair |
| `media-transport-panel` | `COLOR_FOREGROUND` | `background` | `on_primary` | `dark-glass` | glyph ink on the filled primary container | on_primary on primary is the Material pair; `background` (surface) was only correct while the container was a surface tone |

## Variant-level overrides

Only variants with their own `color_mappings` appear here; every other variant inherits
its group rows above (the complete inventory below shows the effective value per
variant). Rows marked with a surface different from the group's are the cases the
per-variant `surface` override exists for.

| Group / variant | Token | Current value | Proposed role | Surface | Rationale | Contrast note |
|---|---|---|---|---|---|---|
| `battery` / `plugged` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` | AC-power glyph also floats over the wallpaper; the override repeats the group row, so Phase B may drop it. — bar ink: the glyph floats over the wallpaper and the producer answers "what reads over the top band?" | max-contrast neutral from the producer's candidate pole; best-effort below 4.5 on a pathological band, never worse than on_surface |
| `battery` / `system-battery-0` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | system-surface copy: sits on the dark-glass battery panel, not over the wallpaper, and is exempt from bar retargeting. — panel ink on the dark-glass sheet (was the `foreground` alias, which resolves to on_surface but is not a role) | on_surface is the Material ink for surface/surface_container; the panel is alpha(surface, 0.94) over a transparent window |
| `battery` / `system-battery-25` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | system-surface copy: sits on the dark-glass battery panel, not over the wallpaper, and is exempt from bar retargeting. — panel ink on the dark-glass sheet (was the `foreground` alias, which resolves to on_surface but is not a role) | on_surface is the Material ink for surface/surface_container; the panel is alpha(surface, 0.94) over a transparent window |
| `battery` / `system-battery-50` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | system-surface copy: sits on the dark-glass battery panel, not over the wallpaper, and is exempt from bar retargeting. — panel ink on the dark-glass sheet (was the `foreground` alias, which resolves to on_surface but is not a role) | on_surface is the Material ink for surface/surface_container; the panel is alpha(surface, 0.94) over a transparent window |
| `battery` / `system-battery-75` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | system-surface copy: sits on the dark-glass battery panel, not over the wallpaper, and is exempt from bar retargeting. — panel ink on the dark-glass sheet (was the `foreground` alias, which resolves to on_surface but is not a role) | on_surface is the Material ink for surface/surface_container; the panel is alpha(surface, 0.94) over a transparent window |
| `battery` / `system-battery-100` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | system-surface copy: sits on the dark-glass battery panel, not over the wallpaper, and is exempt from bar retargeting. — panel ink on the dark-glass sheet (was the `foreground` alias, which resolves to on_surface but is not a role) | on_surface is the Material ink for surface/surface_container; the panel is alpha(surface, 0.94) over a transparent window |
| `capture-tool` / `camera-accent` | `COLOR_FOREGROUND` | `color6` | `primary` | `dark-glass` | success-tinted notification copy of the camera glyph. — success tint for a finished capture (was color6 = outline_variant, a neutral grey that read as disabled) | tinted glyph on dark glass; primary is the theme's action hue |
| `capture-tool` / `video-accent` | `COLOR_FOREGROUND` | `color6` | `primary` | `dark-glass` | success-tinted notification copy of the video glyph. — success tint for a finished capture (was color6 = outline_variant) | tinted glyph on dark glass |
| `capture-tool` / `warning-caution` | `COLOR_FOREGROUND` | `color3` | `error` | `dark-glass` | failure-tinted notification copy of the warning glyph. — failure outcome for a capture (was color3 = secondary, which is not a caution hue at all under tpr) | failure is a semantic state; error is the Material failure role |
| `ui` / `search` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` | the magnifier sits on the solid search field. — field ink (was color15 = on_surface_variant) | same solid-surface ink as the group row; the pin survives Phase B as an explicit statement, or is dropped as redundant |
| `settings-panel` / `wifi` | `COLOR_FOREGROUND` | `color13` | `primary` | `dark-glass` | capability glyph, on = accent tint. — on-state capability tint (was color13 = surface_container: near-black on a dark panel, i.e. invisible) | on-state is a hue signal; the off state keeps brightness-only differentiation via opacity |
| `settings-panel` / `wifi-off` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | capability glyph, off = neutral ink + opacity dimming. — off state must not rely on hue; brightness (opacity) carries it, so the base ink is the panel ink | same ink as an on row; the panel applies the dimming |
| `settings-panel` / `bluetooth` | `COLOR_FOREGROUND` | `color13` | `primary` | `dark-glass` | capability glyph, on = accent tint. — on-state capability tint (was color13 = surface_container) | hue signal on dark glass |
| `settings-panel` / `bluetooth-off` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | capability glyph, off = neutral ink + opacity dimming. — off state uses the panel ink; opacity carries 'off' | same ink as an on row; the panel applies the dimming |
| `settings-panel` / `wifi-signal-full` | `COLOR_BACKGROUND` | `color12` | `primary_container` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — full-strength badge takes the accent container; the fill was color12 (= primary_container, so this one was already the right role by accident) | container fill on dark glass; the container/on-container pair keeps the bars readable in both modes |
| `settings-panel` / `wifi-signal-full` | `COLOR_FOREGROUND` | `color0` | `on_primary_container` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the accent container (was color0 = surface: light ink on a light badge in light mode) | the Material on-container role is the guaranteed ink for that container in both modes |
| `settings-panel` / `wifi-signal-good` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — good/medium/low badges take a neutral container so only full strength carries accent; the fill was color13 (= surface_container, the bar's own near-black) | container fill on dark glass; a neutral container keeps the ladder readable without four accent steps |
| `settings-panel` / `wifi-signal-good` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the neutral container (was color0 = surface: the ink/badge pair inverts in one of the two modes) | the Material on-container role family is the guaranteed ink for that container in both modes |
| `settings-panel` / `wifi-signal-medium` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — good/medium/low badges take a neutral container so only full strength carries accent; the fill was color13 (= surface_container, the bar's own near-black) | container fill on dark glass; a neutral container keeps the ladder readable without four accent steps |
| `settings-panel` / `wifi-signal-medium` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the neutral container (was color0 = surface: the ink/badge pair inverts in one of the two modes) | the Material on-container role family is the guaranteed ink for that container in both modes |
| `settings-panel` / `wifi-signal-low` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — good/medium/low badges take a neutral container so only full strength carries accent; the fill was color13 (= surface_container, the bar's own near-black) | container fill on dark glass; a neutral container keeps the ladder readable without four accent steps |
| `settings-panel` / `wifi-signal-low` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the neutral container (was color0 = surface: the ink/badge pair inverts in one of the two modes) | the Material on-container role family is the guaranteed ink for that container in both modes |
| `settings-panel` / `bluetooth-signal-full` | `COLOR_BACKGROUND` | `color12` | `primary_container` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — full-strength badge takes the accent container; the fill was color12 (= primary_container, so this one was already the right role by accident) | container fill on dark glass; the container/on-container pair keeps the bars readable in both modes |
| `settings-panel` / `bluetooth-signal-full` | `COLOR_FOREGROUND` | `color0` | `on_primary_container` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the accent container (was color0 = surface: light ink on a light badge in light mode) | the Material on-container role is the guaranteed ink for that container in both modes |
| `settings-panel` / `bluetooth-signal-good` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — good/medium/low badges take a neutral container so only full strength carries accent; the fill was color13 (= surface_container, the bar's own near-black) | container fill on dark glass; a neutral container keeps the ladder readable without four accent steps |
| `settings-panel` / `bluetooth-signal-good` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the neutral container (was color0 = surface: the ink/badge pair inverts in one of the two modes) | the Material on-container role family is the guaranteed ink for that container in both modes |
| `settings-panel` / `bluetooth-signal-medium` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — good/medium/low badges take a neutral container so only full strength carries accent; the fill was color13 (= surface_container, the bar's own near-black) | container fill on dark glass; a neutral container keeps the ladder readable without four accent steps |
| `settings-panel` / `bluetooth-signal-medium` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the neutral container (was color0 = surface: the ink/badge pair inverts in one of the two modes) | the Material on-container role family is the guaranteed ink for that container in both modes |
| `settings-panel` / `bluetooth-signal-low` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — good/medium/low badges take a neutral container so only full strength carries accent; the fill was color13 (= surface_container, the bar's own near-black) | container fill on dark glass; a neutral container keeps the ladder readable without four accent steps |
| `settings-panel` / `bluetooth-signal-low` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` | circle-badged signal-strength glyph; badge fill + ink. — bars on the neutral container (was color0 = surface: the ink/badge pair inverts in one of the two modes) | the Material on-container role family is the guaranteed ink for that container in both modes |
| `settings-panel` / `info-caution` | `COLOR_FOREGROUND` | `color15` | `tertiary` | `dark-glass` | weak-security info glyph tinted as a caution. — caution tint for the weak-security row (the pin was color15 = on_surface_variant, i.e. no caution hue at all — the comment and the pin disagreed) | caution is a hue hint on a row that still reads by shape and text; tertiary is the producer's `warning` alias target |
| `volume` / `system-muted` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |
| `volume` / `system-lowest` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |
| `volume` / `system-low` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |
| `volume` / `system-medium` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |
| `volume` / `system-max` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |
| `microphone` / `system-mic-on` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |
| `microphone` / `system-mic-off` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` | panel-surface copy: sits on dark glass, not over the wallpaper. — panel ink on dark glass (was the `foreground` alias) | panel ink; on_backdrop would chase a wallpaper band that is not behind this glyph |

## `defaults.yaml` proposals

The vocabulary defaults must be safe for the majority surface (a panel) and must stop
using alias names. A group that floats over the wallpaper pins `on_backdrop` itself —
that is the Phase B rule the validator enforces for `surface: wallpaper`.

| Token | Current value | Proposed role | Rationale | Contrast note |
|---|---|---|---|---|
| `COLOR_FOREGROUND` | `foreground` | `on_surface` | the vocabulary fallback must be the panel ink; a group that floats over the wallpaper pins on_backdrop explicitly (that is the Phase B rule) | on_surface is the Material ink for a surface/surface_container panel; `foreground` is a producer alias, not a role, so it leaves the manifest |
| `COLOR_BACKGROUND` | `surface` | `surface` | already a role — no change (listed so the table is complete) | surface == background in the Material neutral pole |
| `COLOR_SECONDARY` | `accent` | `secondary` | `accent` resolves to primary through the producer's stable aliases, so the name and the meaning disagreed; secondary is the neutral emphasis pole | alias removed; the role states the intent |
| `COLOR_ACCENT` | `accent-muted` | `primary` | `accent-muted` resolves to secondary, not to an accent of primary; the vocabulary name promised an accent and delivered the neutral pole | alias removed; primary is the accent the name claims |

## Complete inventory — every group, variant and placeholder

Mechanical inventory of `icons.yaml`: one row per variant per declared placeholder,
with the effective current value (group or variant pin) and the proposed role. Rows
whose placeholder is declared but unused by the variant's current template are
marked. This table is the completeness proof for the proposal; `make validate-icons`
fails if a group or variant in `icons.yaml` is missing from this document.

| Group | Variant | Placeholder | Current value | Proposed role | Surface |
|---|---|---|---|---|---|
| `battery` | `battery-0` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-0` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-25` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-25` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-50` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-50` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-75` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-75` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-100` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-100` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-0-charging` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-0-charging` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-25-charging` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-25-charging` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-50-charging` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-50-charging` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-75-charging` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-75-charging` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `battery-100-charging` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `battery` | `battery-100-charging` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `plugged` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `plugged` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `battery` | `system-battery-0` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `system-battery-0` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `battery` | `system-battery-25` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `system-battery-25` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `battery` | `system-battery-50` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `system-battery-50` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `battery` | `system-battery-75` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `system-battery-75` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `battery` | `system-battery-100` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `battery` | `system-battery-100` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `network` | `wifi-full-default` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-full-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-full-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-full-bold` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-full-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-full-bold` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-full-rounded` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-full-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-full-rounded` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-high-default` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-high-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-high-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-high-bold` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-high-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-high-bold` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-high-rounded` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-high-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-high-rounded` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-medium-default` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-medium-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-medium-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-medium-bold` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-medium-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-medium-bold` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-medium-rounded` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-medium-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-medium-rounded` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-low-default` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-low-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-low-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-low-bold` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-low-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-low-bold` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-low-rounded` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-low-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-low-rounded` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-not-connected-default` | `COLOR_CROSS` | `color13` | `error` | `wallpaper` |
| `network` | `wifi-not-connected-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-not-connected-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-not-connected-bold` | `COLOR_CROSS` | `color13` | `error` | `wallpaper` |
| `network` | `wifi-not-connected-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-not-connected-bold` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-not-connected-rounded` | `COLOR_CROSS` | `color13` | `error` | `wallpaper` |
| `network` | `wifi-not-connected-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-not-connected-rounded` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-no-internet-default` | `COLOR_CROSS` | `color13` | `error` | `wallpaper` |
| `network` | `wifi-no-internet-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-no-internet-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-no-internet-bold` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-no-internet-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-no-internet-bold` | `COLOR_WARNING` | `color13` | `tertiary` | `wallpaper` |
| `network` | `wifi-no-internet-rounded` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `wifi-no-internet-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `wifi-no-internet-rounded` | `COLOR_WARNING` | `color13` | `tertiary` | `wallpaper` |
| `network` | `ethernet-connected-default` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `ethernet-connected-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `ethernet-connected-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `ethernet-connected-bold` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `ethernet-connected-bold` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `ethernet-connected-bold` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `ethernet-connected-rounded` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `ethernet-connected-rounded` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `ethernet-connected-rounded` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `network` | `ethernet-no-internet-default` | `COLOR_CROSS` (declared, unused) | `color13` | `error` | `wallpaper` |
| `network` | `ethernet-no-internet-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `ethernet-no-internet-default` | `COLOR_WARNING` | `color13` | `tertiary` | `wallpaper` |
| `network` | `ethernet-not-connected-default` | `COLOR_CROSS` | `color13` | `error` | `wallpaper` |
| `network` | `ethernet-not-connected-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `network` | `ethernet-not-connected-default` | `COLOR_WARNING` (declared, unused) | `color13` | `tertiary` | `wallpaper` |
| `wlogout` | `hibernate` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wlogout` | `lock` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wlogout` | `logout` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wlogout` | `reboot` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wlogout` | `shutdown` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wlogout` | `suspend` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `power-menu` | `power-menu-default` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `power-menu` | `power-menu-default` | `COLOR_BACKGROUND` (declared, unused) | `background` | `primary_container` | `wallpaper` |
| `power-menu` | `power-menu-default` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `power-menu` | `power-menu-default` | `COLOR_SECONDARY` (declared, unused) | `color1` | `secondary` | `wallpaper` |
| `power-menu` | `power-menu-modern-gradient` | `COLOR_ACCENT` | `color13` | `primary` | `wallpaper` |
| `power-menu` | `power-menu-modern-gradient` | `COLOR_BACKGROUND` (declared, unused) | `background` | `primary_container` | `wallpaper` |
| `power-menu` | `power-menu-modern-gradient` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `power-menu` | `power-menu-modern-gradient` | `COLOR_SECONDARY` | `color1` | `secondary` | `wallpaper` |
| `power-menu` | `power-menu-modern-with-background` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `wallpaper` |
| `power-menu` | `power-menu-modern-with-background` | `COLOR_BACKGROUND` | `background` | `primary_container` | `wallpaper` |
| `power-menu` | `power-menu-modern-with-background` | `COLOR_FOREGROUND` | `color15` | `on_primary_container` | `solid` |
| `power-menu` | `power-menu-modern-with-background` | `COLOR_SECONDARY` (declared, unused) | `color1` | `secondary` | `wallpaper` |
| `power-mode` | `powersave` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `power-mode` | `balanced` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `power-mode` | `performance` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `camera` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `camera` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `video` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `video` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `region` | `COLOR_ACCENT` | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `region` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `monitor` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `monitor` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `window` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `window` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `clipboard` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `clipboard` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `save` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `save` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `speaker` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `speaker` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `mic` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `mic` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `info` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `info` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `warning` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `warning` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `pause` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `pause` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `play` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `play` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `stop` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `stop` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `capture-tool` | `camera-accent` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `camera-accent` | `COLOR_FOREGROUND` | `color6` | `primary` | `dark-glass` |
| `capture-tool` | `video-accent` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `video-accent` | `COLOR_FOREGROUND` | `color6` | `primary` | `dark-glass` |
| `capture-tool` | `warning-caution` | `COLOR_ACCENT` (declared, unused) | `color13` | `primary` | `dark-glass` |
| `capture-tool` | `warning-caution` | `COLOR_FOREGROUND` | `color3` | `error` | `dark-glass` |
| `email-client` | `email-client` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wallpaper-selector` | `wallpaper-selector` | `COLOR_FOREGROUND` | `foreground (defaults)` | `on_backdrop` | `wallpaper` |
| `wallpaper-progress` | `picture` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `wallpaper-progress` | `check-circle` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `btop` | `btop` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `btop` | `btop` | `COLOR_JOIN` | `color15` | `on_backdrop` | `wallpaper` |
| `thunderbird` | `thunderbird` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `tray` | `tidal` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `ui` | `search` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `search` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `ui` | `text` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `text` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `ui` | `image` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `image` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `ui` | `link` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `link` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `ui` | `code` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `code` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `ui` | `color` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `color` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `ui` | `emoji` | `COLOR_ACCENT` (declared, unused) | `color12` | `primary` | `solid` |
| `ui` | `emoji` | `COLOR_FOREGROUND` | `color15` | `on_surface` | `solid` |
| `settings` | `default` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `bluetooth` | `bluetooth-on` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `bluetooth` | `bluetooth-off` | `COLOR_FOREGROUND` | `color15` | `on_backdrop` | `wallpaper` |
| `settings-panel` | `wifi` | `COLOR_FOREGROUND` | `color13` | `primary` | `dark-glass` |
| `settings-panel` | `wifi-off` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `bluetooth` | `COLOR_FOREGROUND` | `color13` | `primary` | `dark-glass` |
| `settings-panel` | `bluetooth-off` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `hyprmod` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `signal-low` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `signal-medium` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `signal-good` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `signal-high` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-full` | `COLOR_BACKGROUND` | `color12` | `primary_container` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-full` | `COLOR_FOREGROUND` | `color0` | `on_primary_container` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-good` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-good` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-medium` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-medium` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-low` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` |
| `settings-panel` | `bluetooth-signal-low` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` |
| `settings-panel` | `wifi-signal-full` | `COLOR_BACKGROUND` | `color12` | `primary_container` | `dark-glass` |
| `settings-panel` | `wifi-signal-full` | `COLOR_FOREGROUND` | `color0` | `on_primary_container` | `dark-glass` |
| `settings-panel` | `wifi-signal-good` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` |
| `settings-panel` | `wifi-signal-good` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` |
| `settings-panel` | `wifi-signal-medium` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` |
| `settings-panel` | `wifi-signal-medium` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` |
| `settings-panel` | `wifi-signal-low` | `COLOR_BACKGROUND` | `color13` | `surface_container_high` | `dark-glass` |
| `settings-panel` | `wifi-signal-low` | `COLOR_FOREGROUND` | `color0` | `on_surface` | `dark-glass` |
| `settings-panel` | `info-caution` | `COLOR_FOREGROUND` | `color15` | `tertiary` | `dark-glass` |
| `settings-panel` | `password-show` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `settings-panel` | `password-hide` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `brightness` | `default` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `volume` | `muted` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `volume` | `lowest` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `volume` | `low` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `volume` | `medium` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `volume` | `max` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `volume` | `system-muted` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `volume` | `system-lowest` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `volume` | `system-low` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `volume` | `system-medium` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `volume` | `system-max` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `microphone` | `mic-on` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `microphone` | `mic-off` | `COLOR_FOREGROUND` | `foreground` | `on_backdrop` | `wallpaper` |
| `microphone` | `system-mic-on` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `microphone` | `system-mic-off` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `app-icons` | `generic` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `google-chrome` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `chromium` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `brave-browser` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `firefox` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `spotify` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `tidal-hifi` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `whatsapp` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `youtube` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `app-icons` | `youtube-music` | — | literal brand fill, no placeholder | — | `dark-glass` |
| `media-transport` | `play` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `media-transport` | `pause` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `media-transport` | `previous` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `media-transport` | `next` | `COLOR_FOREGROUND` | `foreground` | `on_surface` | `dark-glass` |
| `media-transport-panel` | `play` | `COLOR_BACKGROUND` | `color6` | `primary` | `dark-glass` |
| `media-transport-panel` | `play` | `COLOR_FOREGROUND` | `background` | `on_primary` | `dark-glass` |
| `media-transport-panel` | `pause` | `COLOR_BACKGROUND` | `color6` | `primary` | `dark-glass` |
| `media-transport-panel` | `pause` | `COLOR_FOREGROUND` | `background` | `on_primary` | `dark-glass` |

## Judgment calls the user must review

1. **Badge ink is `on_*_container`, not `on_primary`.** The rule of thumb given for
   this proposal said "badges → `primary_container`/`on_primary`". `on_primary` is only
   contrast-guaranteed against `primary`; against `primary_container` it is the wrong
   pair (white-on-light in light mode, dark-on-dark in dark mode). The tables therefore
   pair `primary_container` with `on_primary_container` and use a literal
   `primary`/`on_primary` pair only for the filled action button
   (`media-transport-panel`). Confirm this correction.
2. **`network.COLOR_CROSS` → `error`.** The cross/slash already carries the failure
   state by shape. `error` adds a hue cue, but on a bright wallpaper an error red can
   miss 4.5:1. Alternative: `on_backdrop` (shape-only, never low-contrast). The table
   proposes `error` because the token exists to be different from the ink.
3. **`battery.COLOR_ACCENT` → `primary`.** The charging bolt is a large filled shape
   inside the battery outline. A mid-tone `primary` reads as a deliberate two-tone on a
   dark bar but can flatten on a bright wallpaper. Alternative: `surface` (a true
   knock-out) or `on_backdrop` (drop the accent entirely).
4. **`ui` is declared `solid`, not `wallpaper`.** The search-field magnifier already
   pins `color15` because it sits on an opaque field, and the picker rows sit on a
   content card; the group is nevertheless in the runtime's current bar allowlist.
   Phase B makes the data explicit and the guard deletion (REQ-022) removes the
   conflict — but this is the one group whose surface is a runtime-behaviour change,
   not only a colour change.
5. **`media-transport` is declared `dark-glass`.** Its comment calls the group
   "bar-facing", but its two consumers are the audio popup's rows (glass). If any bar
   call site exists, it needs `on_backdrop` plus the `system-*` copy convention that
   battery/volume/microphone already use.
6. **`settings-panel.info-caution` → `tertiary`.** The comment says "caution tint
   follows the warning-caution precedent" but the pin was `color15`
   (`on_surface_variant`) — the comment and the data disagreed. This proposal picks
   the caution hue, so the glyph changes from neutral to tinted.
7. **`wlogout` is `wallpaper`, not `solid`.** The full-screen surface paints the
   wallpaper and leaves its buttons transparent (`templates/wlogout/style.css.tpl:14`),
   so the glyph floats over the image. It currently inherits the vocabulary default;
   Phase B must pin it explicitly or that inheritance silently decides the ink.
8. **`on_backdrop` is forward-looking.** tpr `HEAD` is v0.4.0 and REQ-022 is not
   implemented yet (`git -C ../theme-producer tag --list` → max `v0.4.0`;
   `grep -rn on_backdrop ../theme-producer/src` → 0 matches on 2026-10-30). The role
   is declared here per the approved requirement, but **Phase B must not pin it until
   tpr v0.5.0 is released**, or the render resolves an unknown key.
9. **`power-menu-modern-with-background` gets `surface: solid`.** It paints its own
   disc, so it is not over the wallpaper; its ink is `on_primary_container` instead of
   `on_backdrop`. This is the reference case for the per-variant surface override.
10. **The Phase A legacy baseline is a ratchet, not an exemption.** `vocabulary.json`
    lists the 67 pre-migration values (41 `colorN`, 24 `foreground`, 2 alias names)
    that the validator must tolerate until Phase B. It fails if an entry is not used
    by a live pin, so Phase B removals force the list down; the target is an empty
    array. Confirm that a frozen baseline is acceptable rather than a red gate now.

## Phase B — what applying this table means

Blocked until the user reviews the ten items above **and** tpr v0.5.0 ships.

- Re-pin the 28 group rows and 38 variant overrides exactly as tabulated; rewrite
  `defaults.yaml` to the four role values.
- Declare `surface:` on every group and on the variants listed with a different
  surface; then the validator's wallpaper rule becomes live: every `surface:
  wallpaper` variant whose templates use `COLOR_FOREGROUND`/`COLOR_JOIN` must resolve
  to `on_backdrop`.
- Delete every `phase_a_legacy_baseline` entry; the gate is green only with an empty
  array and zero `colorN` values.
- Render the seven wallpapers in light and dark; record before/after samples in the
  ticket.

## Evidence / Verify

- Evidence: current pins and their line numbers above; producer role order
  `theme-producer/src/theme_producer/domain/services.py:45-62`; 50-role enum
  `theme-producer/src/theme_producer/domain/enums.py:17-76`; `on_backdrop` design
  `theme-producer/tickets/req-022-on-backdrop-role/ticket.md`; alias table
  `theme-producer/src/theme_producer/adapters/projections/registry.py:56-71`;
  wlogout wallpaper surface `templates/wlogout/style.css.tpl:14`; group/variant counts
  and the inventory generated from `icons/mappings/icons.yaml`.
- Verify: `make validate-icons` (vocabulary + surface + coverage checks) and
  `make gates`; `rg -c 'color[0-9]+' icons/mappings/icons.yaml` still reports the
  Phase A baseline until Phase B.
