# `skins/` — v2 Appearance manifests and the GTK paint templates

A **skin** is appearance: surface paint/geometry, interaction state, type, ink
and mode overrides. It is not a variant and it is not structure: which widget
sits where, and which named variant a host selects, belong to the app. This
class now targets the **Appearance token model v2** from `contracts=v0.9.0`;
the optional root `[host]` policy is a delegation object, not a token group.
The frozen v1 skin schemas stay vendored for provenance only.

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
  templates/ags.gtk.css.j2                bar settings + Bluetooth paint (target: ags)
  templates/ags-clipboard.gtk.css.j2      clipboard overlay (target: ags-clipboard)
  templates/ags-notifications.gtk.css.j2  notification cards (target: ags-notifications)
  templates/ags-wallpaper-selector.gtk.css.j2 selector dialog (target: ags-wallpaper-selector)
  templates/ags-capture.gtk.css.j2        capture bar/overlay/panel (target: ags-capture)
  templates/ags-icme.gtk.css.j2           icon color mapping editor (target: ags-icme)
  templates/ags-btop-studio.gtk.css.j2    btop theme studio (target: ags-btop-studio)
  templates/wlogout.gtk.css.j2            wlogout paint/rhythm (target: wlogout)
  tests/                                  pytest fixtures mirroring the validator
  tests/fixtures/invalid/                 negative fixtures (hex, transition, structure, role, numeric string, mode, layout, template name)
  tests/fixtures/positive/                positive fixture (terminal shape the validator must accept)
  tests/fixtures/parity/                  glass-vs-source ownership/parity record
```

## Template set: `<configDir>.gtk.css.j2` → `<configDir>.css`

Every file in `skins/templates/` must be named `<configDir>.gtk.css.j2`; the
target is the prefix, so `templates/ags.gtk.css.j2` renders `ags.css` and the
bar consumes it through its config directory. The set covers every AGS app
and the wlogout CSS consumer:

| Template | Target `configDir` | Canonical source |
| --- | --- | --- |
| `ags.gtk.css.j2` | `ags` | bar settings/Bluetooth |
| `ags-clipboard.gtk.css.j2` | `ags-clipboard` | clipboard overlay |
| `ags-notifications.gtk.css.j2` | `ags-notifications` | notification cards |
| `ags-wallpaper-selector.gtk.css.j2` | `ags-wallpaper-selector` | selector dialog |
| `ags-capture.gtk.css.j2` | `ags-capture` | capture bar/overlay/panel |
| `ags-icme.gtk.css.j2` | `ags-icme` | icon color mapping editor |
| `ags-btop-studio.gtk.css.j2` | `ags-btop-studio` | btop theme studio |
| `wlogout.gtk.css.j2` | `wlogout` | logout menu paint/rhythm/type; the static source owns structure only and imports this sheet last |

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

## The four manifests

Numbers are stored unitless; the `px` shown in prose is what the template
renders.

| Token | `glass` (default/fallback) | `flat` | `paper` | `terminal` |
| --- | --- | --- | --- | --- |
| `[host]` policy | panel radius + border | none (explicit) | panel radius + border | none (explicit) |
| `surface.panel` radius / border-width / padding | 12 / 1.5 / 11 | 0 / 0 / 11 | 6 / 1 / 11 | 0 / 1 / 9 |
| `surface.card` radius / border-width / padding | 9 / 1 / 10 | 0 / 0 / 10 | 4 / 1 / 10 | 0 / 1 / 8 |
| `surface.cell` radius / border-width / padding / hover-bg | 7 / 0 / 8 / `alpha(@on_surface, 0.08)` | 0 / 0 / 7 / same | 3 / 0 / 8 / same | 0 / 0 / 5 / `alpha(@on_surface, 0.10)` |
| `surface.control` radius / border-width / padding / font-size / weight | 7 / 1 / 4 / 11 / 600 | 0 / 0 / 4 / 11 / 600 | 3 / 1 / 4 / 11 / 600 | 2 / 1 / 3 / 10 / 600 |
| `surface.pill` radius / border-width / padding / font-size / letter-spacing | 20 / 1 / 2 / 9.5 / 0.05 | 999 / 0 / 2 / 9.5 / 0.05 | 999 / 1 / 2 / 9.5 / 0.05 | 2 / 1 / 1 / 9 / 0.04 |
| `surface.panel.bg` | `alpha(@surface, 0.94)` | `transparent` | `@surface_container_lowest` | `@surface` |
| `surface.card.bg` | `alpha(@surface_container_high, 0.18)` | `transparent` | `@surface_container_low` | `@surface_container` |
| `surface.panel.border` | `@primary` | `transparent` | `alpha(@on_surface, 0.22)` | `alpha(@on_surface, 0.22)` |
| `surface.panel.shadow` | `none` | `none` | `0 10px 28px rgba(0,0,0,0.22)` | `none` |
| `state.selected` fill / ink | `@primary_container` / `@on_primary_container` | `@primary` / `@on_primary` | `@primary_container` / `@on_primary_container` | `@primary_container` / `@on_primary_container` |
| `ink` / `ink-dim` / `accent` / `accent-muted` | `@on_surface` / `alpha(@on_surface, 0.62)` / `@primary` / `alpha(@primary, 0.18)` | `@on_surface` / `@on_surface_variant` / same | same as `flat` | `@on_surface` / `alpha(@on_surface, 0.62)` / `@primary` / `alpha(@primary, 0.5)` |
| `type` font-family / title / body / caption / meta / display | `inherit` / 12.5 / 13 / 10.5 / 11 / 16 | system-ui / 15 / 13 / 10.5 / 11 / 16 | same as `flat` | JetBrainsMono Nerd Font, monospace / 13 / 12 / 9 / 10 / 14 |
| `layout.ags` panel-width / bt-list-spacing | 312 / 4 | 312 / 4 | 312 / 6 | 312 / 4 |

### Host defaults (`v0.9.0`)

`glass` and `paper` opt in to the optional root policy:

```toml
[host]
inherit = ["surface.panel.radius", "surface.panel.border-width"]
fallback = "skin"
```

`terminal` and `flat` deliberately opt out: square/hairline and zero-chrome
are explicit identities, so they carry no `[host]` block. `[host]` is not a
token group and does not change any token type.

- **Allowlist only.** `inherit` must be non-empty, unique and may contain only
  `surface.panel.radius` (Hyprland `decoration:rounding`) and
  `surface.panel.border-width` (`general:border_size`). Gaps, padding, type,
  colours, layout and structure are never host-injectable.
- **Precedence:** a value supplied by the selected `mode.<mode>` group wins
  over the host; otherwise an inherited token uses the live host value; a token
  not in `inherit` always uses the skin value. `paper`'s authored
  `mode.light.surface` group is therefore explicit and wins in light mode.
- **Fallback:** headless/invalid host values use the skin fallback by default.
  `fallback = "error"` fails the generation closed before publishing.
- **Identity churn:** `glass`/`paper` gain the host block and `flat`/`terminal`
  gain opt-out comments, so all four manifest files change bytes and all four
  skin hashes change. Only `glass`/`paper` change delegation semantics, but
  skin identity is content-addressed, so the first appearance/generation
  identities after this release churn for every skin. No-path/token migration
  is needed; this is a one-time content-addressed churn. The template set is
  unchanged.

`make validate-skins` enforces the allowlist through the vendored
`appearance-manifest` schema (including `items`, `minItems` and
`uniqueItems`); `make test-skins` adds positive/negative host fixtures.

### Layout defaults preserve the apps' pre-v2 window sizes

`v0.12.2` corrects two blocks that were extracted from CSS minima instead of
the apps' default window size. All four skins carry the same values, so the
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
the `[host]` policy for panel radius and border width in light mode.

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

- `skins/contracts/PIN` records `contracts=v0.9.0`, the peeled source commit
  `5c9fd615cae8d6596799bbafaeea93a05b3c3c11` and one `sha256` line per vendored
  file. Editing a vendored schema by hand is a defect; re-vendor from the
  canonical tag and update the PIN in the same change.
- The three appearance schemas are the delegates. The canonical
  `generation-manifest` schema is vendored at the same tag for contract-byte
  parity only: this class emits skin/appearance documents, not generations. The
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
make validate-skins   # vendored hashes + v2 manifests + both modes + tokens.json + template naming/expansion
make test-skins       # pytest fixtures, including parity, mode and negative cases
```

`make validate-skins` is stdlib-only and part of `make gates`. It validates
each manifest against the vendored `appearance-manifest` schema (including the
optional `[host]` allowlist and fallback), resolves it under both `dark` and
`light`, validates each resolved `tokens.json` against `appearance-json`, and
expands all eight templates for all four manifests × both modes. The frozen
`required_targets` set is compared exactly with the discovered template set, so
a missing `wlogout.gtk.css.j2` (or any other required consumer) fails the gate
instead of silently dropping a target. It checks the flattened placeholder
vocabulary two ways, rejects literal hex, transitions/animations,
structure/variant properties and layout placeholders, and verifies the unit
rule (length → `<n>px`, letter-spacing → `<n>em`, font-weight unitless).
`make test-skins` adds the positive frozen values, glass parity against today's
declarations, paper light/dark expansion, state/role coverage, host
positive/negative fixtures and the other negative fixtures.
