# `skins/` — frozen skin manifests and the GTK paint template

A **skin** is a palette/ink mapping, paint and rhythm/density. It is not a
variant and it is not structure: which widget sits where, and which named
variant a host selects, belong to the app. The frozen v1 token groups are:

| Group | Tokens |
| --- | --- |
| `shape` | `radius-panel`, `radius-card`, `radius-cell`, `radius-pill`, `border-w` |
| `rhythm` | `gap`, `cell-pad` |
| `surface` | `bg-panel`, `bg-card`, `border`, `shadow`, `blur` |
| `ink` | `ink`, `ink-dim`, `accent`, `ink-over` (always `auto`) |
| `type` | `font-family`, `title-size`, `text-size` |
| `layout` | `panel-width`, `bt-list-spacing`, `bar-row-height`, `chip-min` |

There are no `structure`, `variant`, `state`, `density` or `paint` keys. A key
outside the six groups fails `make validate-skins`; the app owns everything the
tokens do not describe.

## Layout

```text
skins/
  schema.json                       pointer + the local data-only validation target
  manifests/glass.toml              default/fallback parity skin (today's ags-bar look)
  manifests/flat.toml               zero-chrome skin
  manifests/paper.toml              light/palette-axis skin
  templates/ags-bar.gtk.css.j2      settings + Bluetooth paint rules
  tests/                            pytest fixtures mirroring the validator
  tests/fixtures/invalid/           negative fixtures (hex, transition, structure, roles)
  tests/fixtures/parity/            the explicit glass-vs-source deviation record
```

## The three manifests

| Token | `glass` (default/fallback) | `flat` | `paper` |
| --- | --- | --- | --- |
| `radius-panel/card/cell/pill` | 12 / 9 / 7 / 20px | 0 / 0 / 0 / 999px | 6 / 4 / 3 / 999px |
| `border-w` | 1.5px | 0px | 1px |
| `gap` / `cell-pad` | 8px / 8px 9px | 8px / 7px 8px | 9px / 8px 10px |
| `bg-panel` | `alpha(@surface, 0.94)` | `transparent` | `@surface_container_lowest` |
| `bg-card` | `alpha(@surface_container_high, 0.18)` | `transparent` | `@surface_container_low` |
| `border` | `@primary` | `transparent` | `alpha(@on_surface, 0.22)` |
| `shadow` | `none` | `none` | `0 10px 28px rgba(0,0,0,0.22)` |
| `blur` | `none` | `none` | `none` |
| `ink` / `ink-dim` / `accent` | `@on_surface` / `alpha(@on_surface, 0.62)` / `@primary` | `@on_surface` / `@on_surface_variant` / `@primary` | same as `flat` |
| `font-family` | `inherit` | system-ui / Cantarell / Noto Sans | same as `flat` |
| `title-size` / `text-size` | 12.5px / 13px | 15px / 13px | 15px / 13px |
| `panel-width` / `bt-list-spacing` / `bar-row-height` / `chip-min` | 312 / 4 / 0 / 0px | 312 / 4 / 28 / 48px | 312 / 6 / 30 / 52px |

`glass` is the value a consumer uses when no skin is selected. Its values are a
**literal extraction** of today's `../ags-bar/style.css`, not a design-system
re-expression: panel `alpha(@surface, 0.94)` / `1.5px @primary` / `12px` / `11px`
(`:161-166`), card `alpha(@surface_container_high, 0.18)` / `9px` (`:181-186`),
row `8px 9px` / `7px` (`:378-387`), badge radius `20px` (`:422-429`), no panel
shadow, and `ink-dim = alpha(@on_surface, 0.62)` (`:413-416`). `flat` removes
every surface and border and tightens the rhythm. `paper` changes only shape,
rhythm and surface roles; it does not add a second variant.

## What the GTK template does and does not control (v1 limitations)

`templates/ags-bar.gtk.css.j2` uses a `SKIN_*` placeholder **only** where the
frozen token is a genuine global knob: panel background/border/border-width/
radius/shadow/blur, card background/radius, cell radius/padding, control radius,
pill radius, ink/ink-dim/accent, `title-size`/`text-size`, and layout metrics.

Everything else is a component literal copied from today's `style.css`, because
the frozen 23-token contract has no token for it. A second token would be a
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
| signal cell | `30px` (`:711-715`) | row content size, not `bar-row-height = 0px` |

`gap` is manifest metadata in v1: every gap-looking declaration is a component
padding or the separate `bt-list-spacing` metric, so rewriting it to `gap`
would make glass *less* faithful. The window root gets
`font-family: {{SKIN_FONT_FAMILY}}` only — today it inherits `font-size`, so the
template deliberately emits no root `font-size`.

**One visual deviation is unavoidable.** The contract has a single `border-w`.
Today the panel is `1.5px` (`:163`) while cards (`:183`), row actions (`:442`),
badges (`:428`/`:433`) and the Wi-Fi settings top rule (`:761`) are `1px`.
`glass` keeps the panel's `1.5px`, so those hairlines render **`1.5px` instead
of `1px` (+0.5px)**. `tests/fixtures/parity/deviations.json` records each case
with its source line; `tests/test_parity.py` asserts the rendered declaration
and, when the read-only `../ags-bar` tree is present, the exact source line.
Template-only declarations with no visual change (`min-width: 312px`,
`margin-bottom: 4px` from widget spacing `4`, `min-height/min-width: 0px`,
`box-shadow: none`, `backdrop-filter: none`, `font-family: inherit`) are listed
in that fixture too.

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

## Sourcing the canonical schema

The canonical documents live in the separate `contracts` repository:
`schemas/skin-token.schema.json` and `schemas/skin-manifest.schema.json`. This
repository does **not** import them at runtime and does not vendor a copy:
`skins/schema.json` records the pointer (`canonical.paths`), sets
`canonical.tag = null` and `canonical.vendored = false`, and is itself the local
data-only validation target read by `scripts/validate-skins.py` and the fixtures
under `skins/tests/`. The local `ink` value grammar accepts the same
role-or-role-expression forms as the canonical `inkValue`, which is why glass
can carry `ink-dim = alpha(@on_surface, 0.62)` without changing the token set.
When the canonical pair is vendored it must carry the pinned `contracts` tag and
a byte-equality test; that test does not exist yet and is not claimed.

## Template rules

`skins/templates/ags-bar.gtk.css.j2` keeps the app-local selector vocabulary
(`settings-surface`, `settings-net` and its `.sel` / `.out-of-range` /
`.confirming` states, `settings-rowact` and its states, the chevron, section,
divider, connected-details, empty, level-slider, Wi-Fi settings and nav-header
classes) and substitutes a `{{SKIN_*}}` placeholder only for the genuine knobs
above. The placeholder name is the upper-snake form of the token:
`radius-panel` → `{{SKIN_RADIUS_PANEL}}`, `bg-panel` → `{{SKIN_BG_PANEL}}`.

The template has no literal hex colour, no `transition`, no `animation`, no
non-`none` shadow and no structure/variant vocabulary. State colours that are
not skin tokens (for example a selected row's `@primary_container` /
`@on_primary_container`, or a destructive action's `@tertiary`) are named
`palette.v1` roles, not literals.

**Radius clipping is the app's job.** GTK CSS has no `overflow` property. When a
radius-clipped container's children can reach its corners, the app MUST set
overflow HIDDEN on the widget carrying `.settings-surface` (and any other
radius-clipped surface). The template comment states the same requirement; the
stylesheet can set the radius but cannot apply the clip.

## Validation

```bash
make validate-skins   # manifests + schema + placeholder coverage + no-hex/no-transition/no-structure
make test-skins       # pytest fixtures, including the parity and negative cases
```

`make validate-skins` is stdlib-only and part of `make gates`. `make test-skins`
is the fixture suite and uses the repository's development pytest dependency.
`skins/tests/test_parity.py` expands `glass` through `validate-skins`' own
placeholder map and compares the result with the source declarations (with line
references), the explicit deviation fixture, and the no-shadow/no-transition/
no-hex rules.
