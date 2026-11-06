# `skins/` — frozen skin manifests and the GTK paint templates

A **skin** is a palette/ink mapping, paint and rhythm/density. It is not a
variant and it is not structure: which widget sits where, and which named
variant a host selects, belong to the app. The frozen v1 token groups are:

| Group | Tokens |
| --- | --- |
| `shape` | `radius-panel`, `radius-card`, `radius-cell`, `radius-pill`, `border-w`, `hairline-w` |
| `rhythm` | `gap`, `cell-pad` |
| `surface` | `bg-panel`, `bg-card`, `border`, `shadow`, `blur` |
| `ink` | `ink`, `ink-dim`, `accent`, `ink-over` (always `auto`) |
| `type` | `font-family`, `title-size`, `text-size` |
| `layout` | `panel-width`, `bt-list-spacing`, `bar-row-height`, `chip-min` |

`border-w` is the outer panel/frame border; `hairline-w` is the card, tile,
mini, password, row-action and badge hairline (and the Wi-Fi settings top rule).
The row/cell itself has no border.

There are no `structure`, `variant`, `state`, `density` or `paint` keys. A key
outside the six groups fails `make validate-skins`; the app owns everything the
tokens do not describe.

**The four `layout` tokens are TSX-owned.** `panel-width`, `bt-list-spacing`,
`bar-row-height` and `chip-min` stay in the manifest and in the resolved
`skin.json` because widgets read them through `skinValue()`, but a template
MUST NOT expand them into CSS (`min-width`, `margin`, `min-height`). The
widgets set the panel width, list spacing and row/chip geometry; a declaration
in both places is a second owner and breaks parity when either side changes.

## Layout

```text
skins/
  schema.json                       local envelope that delegates token types to the vendored pair
  contracts/PIN                     contracts tag + sha256 of each vendored canonical schema
  contracts/skin-token.schema.json  vendored canonical flat token vocabulary
  contracts/skin-manifest.schema.json  vendored canonical grouped manifest schema
  contracts/skin-json.schema.json   vendored canonical resolved skin.json schema
  manifests/glass.toml              default/fallback parity skin (today's ags-bar look)
  manifests/flat.toml               zero-chrome skin
  manifests/paper.toml              light/palette-axis skin
  templates/ags.gtk.css.j2          bar settings + Bluetooth paint (target configDir: ags)
  templates/ags-clipboard.gtk.css.j2          clipboard overlay (target: ags-clipboard)
  templates/ags-notifications.gtk.css.j2      notification cards (target: ags-notifications)
  templates/ags-wallpaper-selector.gtk.css.j2 selector dialog (target: ags-wallpaper-selector)
  templates/ags-capture.gtk.css.j2            capture bar/overlay/panel (target: ags-capture)
  templates/ags-icme.gtk.css.j2               icon color mapping editor (target: ags-icme)
  templates/ags-btop-studio.gtk.css.j2        btop theme studio (target: ags-btop-studio)
  tests/                            pytest fixtures mirroring the validator
  tests/fixtures/invalid/           negative fixtures (hex, transition, structure, roles, numeric string, template name)
  tests/fixtures/parity/            the glass-vs-source ownership/parity record (no border-width deviation)
```

## Template set: `<configDir>.gtk.css.j2` → `<configDir>.css`

The canonical artifact interface freezes one template per target config
directory. Every file in `skins/templates/` must be named
`<configDir>.gtk.css.j2`; the target is the prefix, so
`templates/ags.gtk.css.j2` renders `current/skins/ags.css` and the bar consumes
it as `$XDG_CONFIG_HOME/ags/skin.css`. The name is a contract, not a label: an
expander that follows `skins.md` would never find `ags-bar.gtk.css.j2`, and the
bar's `configDir` is `ags`.

At `v0.11.0` the set covers every AGS app, not only the bar:

| Template | Target `configDir` | Canonical source |
| --- | --- | --- |
| `ags.gtk.css.j2` | `ags` | bar settings/Bluetooth |
| `ags-clipboard.gtk.css.j2` | `ags-clipboard` | clipboard overlay |
| `ags-notifications.gtk.css.j2` | `ags-notifications` | notification cards |
| `ags-wallpaper-selector.gtk.css.j2` | `ags-wallpaper-selector` | selector dialog |
| `ags-capture.gtk.css.j2` | `ags-capture` | capture bar/overlay/panel |
| `ags-icme.gtk.css.j2` | `ags-icme` | icon color mapping editor |
| `ags-btop-studio.gtk.css.j2` | `ags-btop-studio` | btop theme studio |

`scripts/validate-skins.py` enforces
`^[a-z0-9][a-z0-9_-]*\.gtk\.css\.j2$`, rejects any other file in
`skins/templates/`, derives every target from the prefix, prints all targets in
its summary, and expands every template through `glass`, `flat` and `paper`.

## Value convention: numbers are unitless, `px` is added at render time

The canonical contract types radii, `border-w`, `hairline-w`, `gap`,
`title-size`, `text-size` and the four layout tokens as JSON **numbers**, not
`"12px"` strings. A manifest
stores `radius-panel = 12`; the GTK template expands that token as
`border-radius: 12px`. `cell-pad` is the only length-valued **string** token
(`"Npx Npx"`) and is emitted verbatim, which is why it keeps its `px` units in
TOML. Paint, ink and `font-family` values are strings and render verbatim.

That rule is mechanical in both directions: `scripts/validate-skins.py` rejects
`radius-panel = "12px"` against the vendored canonical schema (AGS would reject
it at startup), and it expands each manifest through every template with the
number → `<n>px` rule so a green gate means the rendered CSS is length-correct.

## The three manifests

Numbers below are stored unitless; the `px` shown in prose is what the template
renders.

| Token | `glass` (default/fallback) | `flat` | `paper` |
| --- | --- | --- | --- |
| `radius-panel/card/cell/pill` | 12 / 9 / 7 / 20 | 0 / 0 / 0 / 999 | 6 / 4 / 3 / 999 |
| `border-w` (panel/frame) | 1.5 | 0 | 1 |
| `hairline-w` (card/control/badge) | 1 | 0 | 1 |
| `gap` / `cell-pad` | 8 / `8px 9px` | 8 / `7px 8px` | 9 / `8px 10px` |
| `bg-panel` | `alpha(@surface, 0.94)` | `transparent` | `@surface_container_lowest` |
| `bg-card` | `alpha(@surface_container_high, 0.18)` | `transparent` | `@surface_container_low` |
| `border` | `@primary` | `transparent` | `alpha(@on_surface, 0.22)` |
| `shadow` | `none` | `none` | `0 10px 28px rgba(0,0,0,0.22)` |
| `blur` | `none` | `none` | `none` |
| `ink` / `ink-dim` / `accent` | `@on_surface` / `alpha(@on_surface, 0.62)` / `@primary` | `@on_surface` / `@on_surface_variant` / `@primary` | same as `flat` |
| `font-family` | `inherit` | system-ui / Cantarell / Noto Sans | same as `flat` |
| `title-size` / `text-size` | 12.5 / 13 | 15 / 13 | 15 / 13 |
| `panel-width` / `bt-list-spacing` / `bar-row-height` / `chip-min` | 312 / 4 / 0 / 0 | 312 / 4 / 28 / 48 | 312 / 6 / 30 / 52 |

`glass` is the value a consumer uses when no skin is selected. Its values are a
**literal extraction** of today's `../ags-bar/style.css`, not a design-system
re-expression: panel `alpha(@surface, 0.94)` / `1.5px @primary` / `12px` / `11px`
(`:161-166`), card `alpha(@surface_container_high, 0.18)` / `9px` (`:181-186`),
row `8px 9px` / `7px` (`:378-387`), badge radius `20px` (`:422-429`), no panel
shadow, and `ink-dim = alpha(@on_surface, 0.62)` (`:413-416`). `flat` removes
every surface and border and tightens the rhythm. `paper` changes only shape,
rhythm and surface roles; it does not add a second variant.

## What the GTK template does and does not control (v1 limitations)

`templates/ags.gtk.css.j2` uses a `SKIN_*` placeholder **only** where the
frozen token is a genuine global knob: panel background/frame border/
`border-w`/`hairline-w`/radius/shadow/blur, card background/radius, cell
radius/padding, control radius, pill radius, ink/ink-dim/accent,
`title-size`/`text-size`. It does **not** consume the layout tokens.

Everything else is a component literal copied from today's `style.css`, because
the frozen 24-token contract has no token for it. A second token would be a
contract change, and a "density"/"structure" token is explicitly forbidden.
The literals are:

| Component detail | Literal (source) | Why it is not a token |
| --- | --- | --- |
| panel padding | `11px` (`:165`) | not the same thing as the `gap` rhythm; padding is component geometry |
| card/tile/mini/password padding | `10px 11px`, `8px 11px 8px 10px`, `10px` (`:185`, `:198`, `:263`) | asymmetric component padding |
| row background/border | `transparent` + `border: none` (`:381-383`) | the row is a bare list cell; the skin supplies radius/padding only |
| row-action padding/font | `4px 8px`, `11px/600` (`:439-441`) | control typography, not the 13px body size |
| badge type/padding | `9.5px`, `letter-spacing: 0.05em`, `2px 6px` (`:423-425`) | small component type |
| small text | net-sub `10.5px`, tile-sub/section-label `11px`, empty `12px`, mini-title `12px`, detail `11px`, Wi-Fi note `10px`, arrow `14px` | these are deliberately below `text-size = 13px` |
| scrollbar | `5px` (`:175-176`) | fixed widget detail |
| level-slider pill/thumb | `99px`, `50%`, `15px` (`:350-371`) | fixed control geometry; the native switch is app-owned |
| back button/nav header | `26px`, `8px`, `18px`, `13.5px`, `7px` (`:287-325`) | header measurements have no matching token |
| signal cell | `30px` (`:711-715`) | row content size; `bar-row-height` is TSX-owned/not a template knob |

`gap` and the four layout tokens are manifest metadata: every gap-looking
declaration is a component padding, and row height/list spacing/panel width are
set by the widgets. Rewriting them into the template would make glass *less*
faithful and double-own the geometry. The window root gets
`font-family: {{SKIN_FONT_FAMILY}}` only — today it inherits `font-size`, so the
template deliberately emits no root `font-size`.

**There is no border-width deviation.** `border-w` is the outer panel/frame
border: `1.5px` in glass (`style.css:163`). `hairline-w` is the card,
row-action, badge and password hairline and the Wi-Fi settings top rule: `1px`
in the source (`:183`, `:442`, `:428`/`:433`, `:559`, `:761`). The expanded
glass therefore matches the source widths exactly. `.settings-net` keeps
`border: none`; it has no `margin-bottom` and no layout `min-height`, so its
allocated row height matches the source's 50px rather than the 54px produced by
the former template overlay. `tests/fixtures/parity/deviations.json` records
the split and the nonvisual rules (shadow/blur `none`, `font-family: inherit`);
`tests/test_parity.py` asserts the rendered declarations and, when the read-only
`../ags-bar` tree is present, the exact source lines.

## `paper` is a palette-mode axis, not a baked light theme

`paper` sets `bg-panel = @surface_container_lowest` and
`bg-card = @surface_container_low`. Both are `palette.v1` roles. In a **light**
palette, `surface_container_lowest` is the lightest sheet and
`surface_container_low` is one step off it, so the panel reads as paper with a
slightly separated card. In a **dark** palette the same two roles are dark
sheets: the skin still applies, but the *appearance* is dark because the palette
mode is dark.

That is deliberate. The skin vocabulary has no `mode` token, no light/dark
variant and no literal colour, so a consumer selects the palette mode first and
the skin second. If a host needs a literal paper look it must pair `paper` with
a light palette; the skin cannot override the palette's mode. `make
validate-skins` enforces role membership, not a mode.

## Vendoring and pinning the canonical schema

The canonical documents live in the separate `contracts` repository:
`schemas/skin-token.schema.json`, `schemas/skin-manifest.schema.json` and
`schemas/skin-json.schema.json`. This repository still does **not** import them
at runtime; it vendors byte-for-byte copies under `skins/contracts/` so the gate
validates the same types a consumer will parse.

- `skins/contracts/PIN` records `contracts=<tag>`, the source commit, and one
  `sha256` line per vendored file. Editing a vendored schema by hand is a
  defect; re-vendor from the canonical tag and update the PIN in the same
  change.
- `skins/schema.json` sets `canonical.vendored: true`, `canonical.tag`, and
  `canonical.pin`. It carries the frozen local envelope (`schema_major` + the six
  flat groups) and **delegates every token value type by external `$ref`** to
  `skins/contracts/skin-manifest.schema.json`; it has no local `px`/dimension
  lookalike grammar. `canonical.resolved_document` names the vendored
  `skins/contracts/skin-json.schema.json`, the schema for the runtime-emitted
  `current/skin.json` (`version: 1` plus the six groups, numeric tokens as raw
  JSON numbers).
- `scripts/validate-skins.py` and `skins/tests/` assert the recorded hashes, the
  delegation (every token property is a canonical `$ref`), the canonical numeric
  types, the unit-rule expansion, the template naming rule, and that a resolved
  glass `skin.json` validates against the vendored `skin-json` schema.

At `v0.11.0` the vendored set is still pinned at `contracts=v0.6.0`, the
hairline/layout-ownership release. It adds the numeric `hairline-w` shape token
(24 tokens total), keeps the `v0.5.1` unit convention, and declares the four
layout tokens TSX-owned: they remain in the manifest/`skin.json` for
`skinValue()` but templates MUST NOT expand them into CSS. Do not claim a tag
whose bytes are not present; re-vendor from the tag and update the PIN hashes in
the same change.

## Template rules

Every template keeps its app-local selector vocabulary and substitutes a
`{{SKIN_*}}` placeholder only for the genuine knobs above. The bar template,
for example, keeps `settings-surface`, `settings-net` and its `.sel` /
`.out-of-range` / `.confirming` states, `settings-rowact` and its states, the
chevron, section, divider, connected-details, empty, level-slider, Wi-Fi
settings and nav-header classes. The non-bar templates keep the same contract
for their own windows: the clipboard kind/head/card classes, the notification
card/tile/chip and progress-card classes, the selector panel/card/crumb/LIVE
classes, the capture bar/overlay/field/recording classes, the icme pane/tree/
card/inspector classes, and the studio rail/tree/stage/diff classes.

Component-specific values (paddings, small font sizes, thumbnail radii,
selection rings and per-element state colours) stay as literals copied from
that app's `style.css`, expressed only as `palette.v1` roles or alpha
derivatives. No template has a literal hex colour, a `transition`, an
`animation`, a layout placeholder or structure/variant vocabulary. The
placeholder name is the upper-snake form of the token: `radius-panel` →
`{{SKIN_RADIUS_PANEL}}`, `bg-panel` → `{{SKIN_BG_PANEL}}`.

**Radius clipping is the app's job.** GTK CSS has no `overflow` property. When a
radius-clipped container's children can reach its corners, the app MUST set
overflow HIDDEN on the widget carrying `.settings-surface` (and any other
radius-clipped surface). The template comment states the same requirement; the
stylesheet can set the radius but cannot apply the clip.

## Validation

```bash
make validate-skins   # vendored hashes + template naming/targets + canonical types + unit expansion + placeholder coverage
make test-skins       # pytest fixtures, including the parity, resolved-document and negative cases
```

`make validate-skins` is stdlib-only and part of `make gates`. `make test-skins`
is the fixture suite and uses the repository's development pytest dependency.
`skins/tests/test_skins.py` checks the PIN hashes, the canonical `$ref`
delegation, all seven template targets, unitless numeric values, the
numeric-string rejection, and a resolved glass `skin.json` against the vendored
`skin-json` schema. Its per-app cases expand every template for `glass`, `flat`
and `paper`, assert the expected top-level selectors and genuine placeholder
coverage, and reject literal hex, transitions/animations and layout tokens.
`skins/tests/test_parity.py` expands `glass` through `validate-skins`' own
unit-rule expander and compares the result with the source declarations (with
line references): the `1.5px` panel vs `1px` hairlines, `.settings-net` with
`border: none` and no layout margin/height, no emitted layout placeholder, the
empty deviation fixture, and the no-shadow/no-transition/no-hex rules.
