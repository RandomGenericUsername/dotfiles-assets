# `skins/` — v2 Appearance manifests, CSS targets and non-CSS artifacts

A **skin** is appearance: surface paint/geometry, interaction state, type, ink
and mode overrides. It is not a variant and it is not structure: which widget
sits where, and which named variant a host selects, belong to the app. This
class now targets the **Appearance token model v2** from `contracts=v0.11.0`;
the optional root `[host]` policy is a delegation object, not a token group.
The `v0.11.0` release expands its allowlist from the outer panel to the inner
card/control/cell rectangle radii, while `surface.pill.radius` stays explicit.
The earlier `v0.10.0` release added the optional `appearance.artifacts` family
for non-CSS consumers; this class ships `rofi` as `rasi` and keeps
`conf`/`theme` reserved. The frozen v1 skin schemas stay vendored for
provenance only.

## The v2 token groups

| Group | Tokens |
| --- | --- |
| `surface.panel` | `bg`, `border`, `border-width`, `radius`, `padding`, `shadow`, `blur` |
| `surface.card` | `bg`, `border`, `border-width`, `radius`, `padding` |
| `surface.cell` | `bg`, `border`, `border-width`, `radius`, `padding`, `hover-bg` |
| `surface.control` | `bg`, `border`, `border-width`, `radius`, `padding`, `font-size`, `font-weight` |
| `surface.pill` | `bg`, `border`, `border-width`, `radius`, `padding`, `font-size`, `letter-spacing` |
| `state.hover` | `fill`, `ink`, `ring` |
| `state.selected` | `fill`, `ink`, `ring` |
| `state.focus` | `fill`, `ink`, `ring` |
| `state.disabled` | `fill`, `ink`, `ring` |
| `type` | `font-family`, `font-weight`, `letter-spacing`, `size-caption`, `size-meta`, `size-body`, `size-title`, `size-display` |
| `ink` | `ink`, `ink-dim`, `accent`, `accent-muted`, `ink-over` (always `auto`) |
| `layout.<app>` | unitless numeric metrics, namespaced per app |

There are no `structure`, `variant`, `density` or `paint` groups. A key outside
the five groups (plus the optional `mode` overrides and the optional root
`host` policy) fails `make validate-skins`; the app owns everything the tokens
do not describe.

`[host]` is **not a token group**. It is an optional policy object that
delegates an explicit allowlist of logical token paths to the live compositor;
the resolved `tokens.json` still contains concrete numbers and strings.

**Per-role borders replace the v1 global split.** `surface.panel.border-width`
is `1.5` in `glass`; `surface.card`, `surface.control` and `surface.pill` own
their own `1` hairlines. `surface.cell` is deliberately borderless (`transparent`,
width `0`) because a transparent border changes allocated height.

**`layout.<app>` is TSX-owned.** `layout.ags.panel-width` and
`layout.ags.bt-list-spacing` (plus the other apps' observed metrics) stay in
the manifest and resolved `tokens.json` for `skinValue()`, but a template MUST
NOT expand them into CSS (`min-width`, `margin`, `min-height`). A layout
placeholder in a template is a gate failure. `bar-row-height` and `chip-min`
were retired in `v0.12.2`: no app source reads them.

## Layout

```text
skins/
  schema.json                             local v2 envelope + vendored/pin metadata
  contracts/PIN                           contracts tag + sha256 of each vendored schema
  contracts/appearance-manifest.schema.json   canonical v2 manifest schema + host policy
  contracts/appearance-json.schema.json       canonical resolved tokens.json schema
  contracts/appearance-artifact.schema.json   canonical appearance.json schema
  contracts/generation-manifest.schema.json   canonical generation schema, byte-parity only
  contracts/skin-*.schema.json                frozen v1 schemas, provenance only
  manifests/glass.toml                    default/fallback parity skin
  manifests/flat.toml                     zero-chrome skin
  manifests/paper.toml                    palette-axis skin with explicit mode.light
  manifests/terminal.toml                 dense-monospace, square/hairline skin
  manifests/terminal-host.toml            terminal paint/type + opt-in host geometry
  templates/ags.gtk.css.j2                bar settings + Bluetooth paint (target: ags)
  templates/ags-clipboard.gtk.css.j2      clipboard overlay (target: ags-clipboard)
  templates/ags-notifications.gtk.css.j2  notification cards (target: ags-notifications)
  templates/ags-wallpaper-selector.gtk.css.j2 selector dialog (target: ags-wallpaper-selector)
  templates/ags-capture.gtk.css.j2        capture bar/overlay/panel (target: ags-capture)
  templates/ags-icme.gtk.css.j2           icon color mapping editor (target: ags-icme)
  templates/ags-btop-studio.gtk.css.j2    btop theme studio (target: ags-btop-studio)
  templates/wlogout.gtk.css.j2            wlogout card fill/state + panel geometry (target: wlogout)
  templates/gtk3.gtk.css.j2               global GTK3 paint, conservative selectors (target: gtk3)
  templates/gtk4.gtk.css.j2               global GTK4/libadwaita named colours (target: gtk4)
  templates/rofi.rasi.j2                  rofi solid roles + px geometry (artifact: rofi, rasi)
  tests/                                  pytest fixtures mirroring the validator
  tests/fixtures/invalid/                 negative fixtures (hex, transition, structure, role, numeric string, mode, layout, template name, format dialect)
  tests/fixtures/positive/                positive fixtures (terminal + terminal-host shapes, wlogout template)
  tests/fixtures/parity/                  glass-vs-source ownership/parity record
```

## Template families: targets vs artifacts

The shared template set has two families, mapped by filename suffix:

- **CSS targets:** `<configDir>.gtk.css.j2` renders `<configDir>.css`. Every
  target lands in `appearance.targets`.
- **Non-CSS artifacts:** `<consumer>.<format>.j2` renders `<consumer>.<format>`
  where `format` is `rasi`, `conf` or `theme`. Every artifact lands in
  `appearance.artifacts`. The suffix is part of the filename, so an unknown
  `*.j2` fails closed instead of being silently ignored.

This tag ships `rasi` (`rofi.rasi.j2`). `conf` (kitty) and `theme` (btop) remain
reserved: btop and kitty stay palette-only until a colour/unit rule makes a
skin projection honest. `skins/schema.json` freezes the exact
`required_targets` (including `gtk3`/`gtk4`) and `required_artifacts`
(`rofi`/`rasi`); a missing or unregistered template fails `validate-skins`.

## Template set: `<configDir>.gtk.css.j2` → `<configDir>.css`

The eight app-owned sheets keep the original naming; the two global GTK sheets
use the same suffix with `gtk3`/`gtk4` consumer aliases (the real config dirs
contain dots, which the `configDir` grammar excludes). The target is the
prefix, so `templates/ags.gtk.css.j2` renders `ags.css`.

| Template | Target `configDir` | Canonical source |
| --- | --- | --- |
| `ags.gtk.css.j2` | `ags` | bar settings/Bluetooth |
| `ags-clipboard.gtk.css.j2` | `ags-clipboard` | clipboard overlay |
| `ags-notifications.gtk.css.j2` | `ags-notifications` | notification cards |
| `ags-wallpaper-selector.gtk.css.j2` | `ags-wallpaper-selector` | selector dialog |
| `ags-capture.gtk.css.j2` | `ags-capture` | capture bar/overlay/panel |
| `ags-icme.gtk.css.j2` | `ags-icme` | icon color mapping editor |
| `ags-btop-studio.gtk.css.j2` | `ags-btop-studio` | btop theme studio |
| `wlogout.gtk.css.j2` | `wlogout` | logout action cards: `surface.card` fill/border/padding with `surface.panel` radius/border-width; hover/focus keep the card fill and move only state ring/ink; the static source owns structure only and imports this sheet last |
| `gtk3.gtk.css.j2` | `gtk3` | global GTK3 paint: `@define-color`/alpha only, no custom properties or colour-mixing, allowlisted selectors, no layout/size |
| `gtk4.gtk.css.j2` | `gtk4` | global GTK4/libadwaita named colours (`window_*`, `view_*`, `accent_*`, …), conservative selectors, no layout/size |

| Artifact template | Consumer / format | Output |
| --- | --- | --- |
| `rofi.rasi.j2` | `rofi` / `rasi` | `rofi.rasi`: solid hyphenated palette roles + px geometry; no alpha, no underscore role names, no typography (Pango units deferred) |

## Placeholder flattening and the value convention

A v2 placeholder is the full nested token path, uppercased with every run of
non-alphanumeric characters replaced by `_`, prefixed with `SKIN` and wrapped
in `{{...}}`:

| Token path | Placeholder |
| --- | --- |
| `surface.panel.bg` | `{{SKIN_SURFACE_PANEL_BG}}` |
| `surface.cell.hover-bg` | `{{SKIN_SURFACE_CELL_HOVER_BG}}` |
| `state.selected.ring` | `{{SKIN_STATE_SELECTED_RING}}` |
| `type.size-body` | `{{SKIN_TYPE_SIZE_BODY}}` |
| `ink.ink` | `{{SKIN_INK_INK}}` |

All lengths are **unitless JSON numbers** in the manifest and in the resolved
`tokens.json`; in a CSS length position the expander renders `<number>px`.
`font-weight` renders unitless; `letter-spacing` renders `<number>em`. Paints,
fonts and ink values render verbatim. The v1 `cell-pad` pair is gone: the
contract stores one numeric `padding` per surface role, so an asymmetric
component padding keeps its second value as a template literal.

## The five manifests

Numbers are stored unitless; the `px` shown in prose is what the template
renders. `terminal-host` carries the same token values as `terminal`; its only
difference is the opt-in `[host]` policy.

| Token | `glass` (default/fallback) | `flat` | `paper` | `terminal` | `terminal-host` |
| --- | --- | --- | --- | --- | --- |
| `[host]` policy | panel + card/control/cell radii/border | none (explicit) | panel + card/control/cell radii/border | none (explicit) | panel + card/control/cell radii/border |
| `surface.panel` radius / border-width / padding | 12 / 1.5 / 11 | 0 / 0 / 11 | 6 / 1 / 11 | 0 / 1 / 9 | 0 / 1 / 9 (host when supplied) |
| `surface.card` radius / border-width / padding | 9 / 1 / 10 | 0 / 0 / 10 | 4 / 1 / 10 | 0 / 1 / 8 | 0 / 1 / 8 (radius host when supplied) |
| `surface.cell` radius / border-width / padding / hover-bg | 7 / 0 / 8 / `alpha(@on_surface, 0.08)` | 0 / 0 / 7 / same | 3 / 0 / 8 / same | 0 / 0 / 5 / `alpha(@on_surface, 0.10)` | same as `terminal` (radius host when supplied) |
| `surface.control` radius / border-width / padding / font-size / weight | 7 / 1 / 4 / 11 / 600 | 0 / 0 / 4 / 11 / 600 | 3 / 1 / 4 / 11 / 600 | 2 / 1 / 3 / 10 / 600 | same as `terminal` (radius host when supplied) |
| `surface.pill` radius / border-width / padding / font-size / letter-spacing | 20 / 1 / 2 / 9.5 / 0.05 | 999 / 0 / 2 / 9.5 / 0.05 | 999 / 1 / 2 / 9.5 / 0.05 | 2 / 1 / 1 / 9 / 0.04 | same as `terminal` |
| `surface.panel.bg` | `alpha(@surface, 0.94)` | `transparent` | `@surface_container_lowest` | `@surface` | `@surface` |
| `surface.card.bg` | `alpha(@surface_container_high, 0.18)` | `transparent` | `@surface_container_low` | `@surface_container` | `@surface_container` |
| `surface.panel.border` | `@primary` | `transparent` | `alpha(@on_surface, 0.22)` | `alpha(@on_surface, 0.22)` | `alpha(@on_surface, 0.22)` |
| `surface.panel.shadow` | `none` | `none` | `0 10px 28px rgba(0,0,0,0.22)` | `none` | `none` |
| `state.selected` fill / ink | `@primary_container` / `@on_primary_container` | `@primary` / `@on_primary` | `@primary_container` / `@on_primary_container` | `@primary_container` / `@on_primary_container` | same as `terminal` |
| `ink` / `ink-dim` / `accent` / `accent-muted` | `@on_surface` / `alpha(@on_surface, 0.62)` / `@primary` / `alpha(@primary, 0.18)` | `@on_surface` / `@on_surface_variant` / same | same as `flat` | `@on_surface` / `alpha(@on_surface, 0.62)` / `@primary` / `alpha(@primary, 0.5)` | same as `terminal` |
| `type` font-family / title / body / caption / meta / display | `inherit` / 12.5 / 13 / 10.5 / 11 / 16 | system-ui / 15 / 13 / 10.5 / 11 / 16 | same as `flat` | JetBrainsMono Nerd Font, monospace / 13 / 12 / 9 / 10 / 14 | same as `terminal` |
| `layout.ags` panel-width / bt-list-spacing | 312 / 4 | 312 / 4 | 312 / 6 | 312 / 4 | 312 / 4 |

### Host defaults: rectangle radii (`v0.18.0`)

`glass`, `paper` and `terminal-host` opt in to the optional root policy:

```toml
[host]
inherit = [
  "surface.panel.radius",
  "surface.panel.border-width",
  "surface.card.radius",
  "surface.control.radius",
  "surface.cell.radius",
]
fallback = "skin"
```

`terminal` and `flat` deliberately opt out: square/hairline and zero-chrome
are explicit identities, so they carry no `[host]` block. `terminal-host`
(`v0.16.0`) remains the opt-in counterpart: it carries terminal's token values
but adds the `[host]` block, so a consumer that selects it follows the host
panel and rectangle geometry while `terminal` keeps its explicit square frame.
`[host]` is not a token group and does not change any token type.

- **Rectangle allowlist only.** `inherit` must be non-empty, unique and may
  contain only `surface.panel.radius` (Hyprland `decoration:rounding`),
  `surface.panel.border-width` (`general:border_size`) and the inner
  `surface.card.radius`, `surface.control.radius` and `surface.cell.radius`.
  Border width is delegable only on the panel. Gaps, padding, type, colours,
  layout and structure are never host-injectable.
- **The pill stays explicit.** `surface.pill.radius` is deliberately absent:
  a pill is a capsule whose identity is the skin's decision, not a host
  rectangle. A manifest that lists it fails the vendored schema.
- **Precedence:** a value supplied by the selected `mode.<mode>` group wins
  over the host; otherwise an inherited token uses the live host value; a token
  not in `inherit` always uses the skin value. `paper`'s authored
  `mode.light.surface` group is therefore explicit and wins in light mode for
  every delegated rectangle.
- **Fallback:** headless/invalid host values use the skin fallback by default.
  `fallback = "error"` fails the generation closed before publishing.
- **Identity churn:** `glass`, `paper` and `terminal-host` gain the four inner
  radius paths in `[host].inherit`, so their manifest bytes and
  content-addressed skin hashes change. `terminal` and `flat` are byte-
  identical. No token/path migration is needed; the template set is unchanged.

`make validate-skins` enforces the allowlist through the vendored
`appearance-manifest` schema (including `items`, `minItems` and
`uniqueItems`); `make test-skins` adds positive/negative host fixtures.

### Rectangle radii delegate; the pill does not (`v0.18.0`)

`surface.panel` remains the canonical outer-surface role (`rofi.window`,
`wlogout` window, the AGS bar panel). The host rounding value now also feeds
the inner rectangles when a skin lists them: `rofi.mainbox` → `card`,
`rofi.inputbar` → `control`, `rofi.element` → `cell`, and the GTK3/GTK4
`popover`/`.card` and `button`/`entry` roles follow the same card/control
tokens. The rofi host-probe test asserts all four rofi selectors follow the
probe for `glass`, `paper` and `terminal-host`, while `terminal` and `flat`
keep their authored values. The GTK host probe covers card/control, and the
wlogout probe covers the panel mapping.

`terminal-host` keeps its square `0/2/0` inner fallback but follows the host
when it supplies values; `glass` and `paper` author rounded inner roles.
`surface.pill.radius` is always the skin's authored value.

The guard inversion is tests/docs: the old invalid `host-inner-radius.toml`
fixture is gone (inner radii are valid when listed), `host-pill-radius.toml`
proves the pill is still rejected, and `host-rectangles.toml` is a positive
all-five-path fixture. No production template or required target changed.

**wlogout action cards use panel geometry by mapping.** The generated
`wlogout.gtk.css.j2` takes each `button` radius/border from `surface.panel`
because those buttons are wide action cards, not compact controls (docs/108
`W-2.12`). The host probe therefore moves their frame with the panel even
though `surface.card.radius` is now delegable elsewhere. That is a
consumer-template mapping decision, not a rule that card/control/cell radii are
unavailable to the host.

### wlogout action cards align to the panel (`v0.15.2`)

wlogout's `button` widgets are wide action cards, not compact controls. The
generated `wlogout.gtk.css.j2` therefore maps the base card to `surface.card`:
`bg` becomes the fill, `border` the border colour and `padding` the card
rhythm. The outer geometry comes from `surface.panel`: `border-width` and
`radius` keep the action cards on the same rounding/frame as the
compositor/panel. `surface.control` is no longer used by this target.

The result is a visibly filled card for `glass`
(`alpha(@surface_container_high, 0.18)`), `paper` (`@surface_container_low`),
`terminal` (`@surface_container`) and `terminal-host` (the same terminal card
fill); `flat` stays transparent because its own card token is transparent.
Because `glass`, `paper` and `terminal-host` delegate
`surface.panel.radius`/`border-width` to `[host]`, their wlogout cards follow
the live Hyprland values; `terminal` remains the explicit 0px/1px square
identity. The static `templates/wlogout/style.css.tpl` remains structure-only
and unchanged from `v0.15.1`.

### wlogout hover/focus keep the card surface (`v0.15.3`)

`state.hover.fill` and `state.focus.fill` are compact-control state paints, not
card surfaces. `terminal`, `glass` and `paper` declare the focus fill as
`transparent`, so using it as the wlogout button background made a focused card
lose its fill and show the wallpaper through it.

The generated `wlogout.gtk.css.j2` now keeps `surface.card.bg` as the background
for `button`, `button:hover` and `button:focus`. Hover and focus change only
`state.hover.*`/`state.focus.*` **ring and ink**; their `fill` tokens are not
referenced by this target. `button:active` keeps the deliberate
`state.selected.fill`/ink/ring press paint, and `button span` keeps the `type.*`
typography. A GTK3 style-context probe asserts that a focused terminal card
still computes to `@surface_container` while its border moves to `@primary`.
The static sheet remains structure-only and is unchanged from `v0.15.2`.

### Layout defaults preserve the apps' pre-v2 window sizes

`v0.12.2` corrects two blocks that were extracted from CSS minima instead of
the apps' default window size. All five skins carry the same values, so the
default skin keeps the pre-v2 behaviour:

| Block | Value | Source of truth |
| --- | --- | --- |
| `layout.ags-icme.root-width` / `root-height` | 1280 / 800 | `ags-icme@v0.3.0:ui/EditorWindow.tsx:612-613` |
| `layout.ags-wallpaper-selector.root-width` / `root-height` | 960 / 640 | `ags-wallpaper-selector@v0.3.0:ui/WallpaperSelectorWindow.tsx:600-601` |

The rest of the layout audit:

| Block | Value | Verdict |
| --- | --- | --- |
| `layout.ags.panel-width` | 312 | keep — real TSX literal (`ags-bar@v0.3.0:settings-panel/SettingsPanel.tsx:22`) |
| `layout.ags.bt-list-spacing` | 4 (`paper` 6) | keep — real TSX literal (`ags-bar@v0.3.0:components/bluetooth/BluetoothContent.tsx:750,798`) |
| `layout.ags-clipboard.card-width` | 260 | keep — real TSX literal (`ags-clipboard@v0.3.0:ui/ItemCard.tsx:179`) |
| `layout.ags-notifications.card-width` | 380 | keep — real TSX literal (`ags-notifications@v0.3.0:ui/NotificationsWindow.tsx:60`) |
| `layout.ags-capture.panel-width` | removed in `v0.13.0` | was CSS `min-width` only (`ags-capture-tool@v0.5.0:style.css:793,997`); the app is corrected to its pre-v2 natural layout in parallel |
| `layout.ags-btop-studio.left-width` / `right-width` | removed in `v0.13.0` | was CSS `min-width` only (`ags-btop-theme-studio@v0.3.0:style.css:42,241`); the app is corrected to its pre-v2 natural layout in parallel |

`v0.13.0` removes the capture panel width and btop rail widths from every
manifest. `req-017` recorded them as cleanup candidates: their only pre-v2
source was a CSS minimum, not a TSX default, and the apps are being corrected
to their pre-v2 natural layout in parallel. The skin class no longer declares
CSS geometry as skin semantics; a consumer that still reads those tokens falls
back to the app's own default until the app commit lands.

`glass` is the value a consumer uses when no skin is selected. Its declarations
are a **literal extraction** of today's `../ags-bar/style.css`, not a
design-system re-expression: panel `alpha(@surface, 0.94)` / `1.5px @primary` /
`12px` / `11px`, card `alpha(@surface_container_high, 0.18)` / `9px` / `10px
11px`, row `8px 9px` / `7px`, badge radius `20px` / `9.5px` / `0.05em`, no panel
shadow, and `ink-dim = alpha(@on_surface, 0.62)`. `flat` removes surfaces and
borders and tightens the rhythm. `paper` changes shape, rhythm and surface
roles; it does not add a second variant. `terminal` is the dense monospace,
square/hairline skin: opaque `@surface` panels, `@surface_container` cards, zero
radii, 1px hairlines, tight paddings and a 9–14px JetBrainsMono scale.

Other namespaces (`layout.ags-clipboard`, `layout.ags-notifications`,
`layout.ags-wallpaper-selector`, `layout.ags-icme`) carry the app metrics from
the audit above and remain TSX-owned. The two window-size blocks preserve the
apps' pre-v2 defaults; capture and btop are no longer skin tokens.

## `paper` is mode-aware now

`paper`'s **base** groups are the v1 paper values converted faithfully; they
are the deliberate dark-paper branch (a dark palette + `paper` keeps them).
`paper` also declares an explicit **`mode.light`** override: complete
`surface`, `state` and `ink` groups with light-paper borders, wash and shadow.
Generation selects exactly one mode before expansion, so a template never
branches on mode, palette or skin. A light palette + `paper` reads light; a
dark palette + `paper` keeps the base groups. This replaces the v1 behaviour
where `paper` depended on whichever mode the palette happened to be. The
complete `mode.light.surface` group is an explicit override, so it wins over
the `[host]` policy for panel, card, control and cell radii and the panel
border width in light mode.

## `terminal` is mode-agnostic

`terminal` is the dense monospace, square/hairline skin. Its panel is opaque
`@surface` with a `1px` `alpha(@on_surface, 0.22)` frame; cards use
`@surface_container`; radii are `0` on panel/card/cell, `2` on control/pill;
paddings are `9`/`8`/`5`/`3`/`1`; and the type scale is JetBrainsMono Nerd Font
at weight `500`, `9`/`10`/`12`/`13`/`14`. It declares no `mode` overrides: the
base groups serve both dark and light, so a palette-only mode change cannot
produce a different terminal shape. Only palette-role expressions are used, so
it still follows the palette family it is generated against. It declares no
`[host]` policy: the square/hairline radius and border are explicit.

## `terminal-host` is the opt-in Hyprland-following variant

`terminal-host` (`v0.16.0`) is a separate manifest, not a mode or variant of
`terminal`: its `groups` are byte-for-byte the same terminal values, and its
only delta is the root `[host]` policy. Selecting it keeps the dense monospace
paint, type and rhythm, but `surface.panel.radius`,
`surface.panel.border-width` and the `surface.card/control/cell.radius`
rectangles resolve from the live host `decoration:rounding` /
`general:border_size` when available and fall back to the skin's square
values when not; the pill stays explicit. `terminal` remains `[host]`-free, so
its square/hairline identity is still available explicitly. Neither skin
declares `mode` overrides.

`make validate-skins` resolves every `[host]` manifest against deterministic
probe values (`panel radius=13`, `border-width=2`, `card=14`, `control=15`,
`cell=16`): the inherited paths must equal those values, no other token may
move (including the pill), and no-host manifests must be byte-identical with
or without the probe. The rofi render probe covers `window`→panel,
`mainbox`→card, `inputbar`→control and `element`→cell; GTK covers
card/control and wlogout covers panel. A GTK3 `CssProvider`/style-context
probe expands the wlogout card target for `terminal-host` with the full host
probe, so the panel radius is applied while the delegated inner radii do not
replace the action-card mapping and the card fill stays identical to
`terminal`.

## What the GTK templates do and do not control

The templates use a `{{SKIN_*}}` placeholder for every role property the v2
model covers: panel/card/cell/control/pill paint, per-role borders and radii,
role paddings, control/pill type and padding, hover/selected/focus/disabled
state, the type scale and ink. Component geometry that has no token stays a
literal copied from that app's `style.css` (for example the bar scrollbar's
`5px`, tile asymmetric padding, slider geometry, signal-cell size and the
`0.5`/`0.42` ink alphas that are not `ink-dim`).

**There is no border-width deviation.** The expanded `glass` bar keeps its
`1.5px` panel frame and `1px` card/control/pill hairlines, `.settings-net` keeps
`border: none` with no layout margin/height, and no template emits a layout
token. `tests/fixtures/parity/deviations.json` records the policy and the
nonvisual rules; `tests/test_parity.py` asserts the rendered declarations and,
when the read-only `../ags-bar` tree is present, the exact source lines.

**Radius clipping is the app's job.** GTK CSS has no `overflow` property. When a
radius-clipped container's children can reach its corners, the app MUST set
overflow HIDDEN on the widget carrying `.settings-surface` (and any other
radius-clipped surface). The template comment states the same requirement.

## Vendoring and pinning the canonical schema

The canonical documents live in the separate `contracts` repository. This
repository vendors byte-for-byte copies under `skins/contracts/` so the gate
validates the same bytes a consumer will parse.

- `skins/contracts/PIN` records `contracts=v0.11.0`, the peeled source commit
  `6a3ed99dab6cf3e49a4643bc82e9d7428d0880ca` and one `sha256` line per vendored
  file. Editing a vendored schema by hand is a defect; re-vendor from the
  canonical tag and update the PIN in the same change.
- The three appearance schemas are the delegates. The canonical
  `generation-manifest` schema is vendored at the same tag for contract-byte
  parity only: this class emits skin/appearance documents, not generations, and
  its optional host snapshot records the same delegated rectangle paths. The
  frozen v1 skin schemas remain for provenance.
- `skins/schema.json` sets `schema_major: 2`, `canonical.vendored: true`,
  `canonical.tag`, `canonical.pin`, the three v2 delegates, the frozen v1
  `legacy` paths and `canonical.resolved_document` (the vendored
  `appearance-json` schema for the runtime-emitted `tokens.json`).
- The manifests are `schemaVersion = 2` (the manifest envelope is
  `schema_major: 2` in the local schema). The resolved document is
  `{"version": 2, "surface": …, "state": …, "type": …, "ink": …, "layout": …}`;
  mode overrides are already applied and there are no `mode`/`skin`/palette
  fields.

## Validation

```bash
make validate-skins   # vendored hashes + v2 manifests + both modes + tokens.json + family/format/expansion gates
make test-skins       # pytest fixtures, including GTK3/GTK4 parse, rofi dump+stderr, parity, mode and negative cases
```

`make validate-skins` is stdlib-only and part of `make gates`. It validates
each manifest against the vendored `appearance-manifest` schema (including the
optional `[host]` allowlist and fallback), resolves it under both `dark` and
`light`, validates each resolved `tokens.json` against `appearance-json`, and
expands all eleven templates for all five manifests × both modes (10
manifest×mode documents per template). It also feeds deterministic host probe
values through every `[host]` policy: inherited paths must equal the probe,
non-inherited tokens must not move, and no-host manifests must be unchanged.
The frozen `required_targets`/`required_artifacts` sets are compared exactly
with the discovered template families, so a missing `gtk3`, `gtk4` or `rofi`
template (or any other required consumer) fails the gate instead of silently
dropping a target. It checks the flattened placeholder vocabulary two ways,
rejects literal hex, transitions/animations, structure/variant properties and
layout placeholders in the rendered bytes, enforces the GTK3 dialect ban
(custom properties/colour-mixing), the GTK3/GTK4 selector allowlist and
layout/size-property ban, and the rasi solid-role/no-alpha/no-underscore rules.
`make test-skins` adds the positive frozen values (including `terminal-host` =
`terminal` tokens + `[host]`), glass parity against today's declarations, paper
light/dark expansion, state/role coverage, host positive/negative fixtures
(including the all-five-path positive and the pill rejection), GTK3/GTK4
provider parse probes, the rofi `-dump-theme`+stderr probe (and its negative
fixtures proving exit 0 alone is not validation), the rofi/GTK/wlogout
host-geometry probes and the other negative fixtures.
