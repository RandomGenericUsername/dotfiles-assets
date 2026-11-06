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
  manifests/glass.toml              default/fallback parity skin
  manifests/flat.toml               zero-chrome skin
  manifests/paper.toml              light/palette-axis skin
  templates/ags-bar.gtk.css.j2      settings + Bluetooth paint rules
  tests/                            pytest fixtures mirroring the validator
  tests/fixtures/invalid/           negative fixtures (hex, transition, structure, roles)
```

## The three manifests

| Token | `glass` (default/fallback) | `flat` | `paper` |
| --- | --- | --- | --- |
| `radius-panel/card/cell/pill` | 16 / 12 / 8 / 999px | 0 / 0 / 0 / 999px | 6 / 4 / 3 / 999px |
| `border-w` | 1.5px | 0px | 1px |
| `gap` / `cell-pad` | 12px / 9px 12px | 8px / 7px 8px | 9px / 8px 10px |
| `bg-panel` | `alpha(@surface, 0.94)` | `transparent` | `@surface_container_lowest` |
| `bg-card` | `alpha(@surface_container_high, 0.88)` | `transparent` | `@surface_container_low` |
| `border` | `alpha(@primary, 0.35)` | `transparent` | `alpha(@on_surface, 0.22)` |
| `shadow` | `0 16px 40px rgba(0,0,0,0.5)` | `none` | `0 10px 28px rgba(0,0,0,0.22)` |
| `blur` | `none` | `none` | `none` |
| `ink` / `ink-dim` / `accent` | `@on_surface` / `@on_surface_variant` / `@primary` | same | same |
| `title-size` / `text-size` | 15px / 13px | 15px / 13px | 15px / 13px |
| `panel-width` / `bt-list-spacing` / `bar-row-height` / `chip-min` | 312 / 6 / 30 / 52px | 312 / 4 / 28 / 48px | 312 / 6 / 30 / 52px |

`glass` is the value a consumer uses when no skin is selected. `flat` removes
every surface and border and tightens the rhythm. `paper` changes only shape,
rhythm and surface roles; it does not add a second variant.

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
repository does **not** import them at runtime and does not currently vendor a
copy: the reachable `contracts` tag (`v0.4.0`, 2026-11-05) has no skin schema.
It would be a false claim to call a local file "vendored".

`skins/schema.json` therefore records the pointer (`canonical.paths`), sets
`canonical.tag = null` and `canonical.vendored = false`, and is itself the local
data-only validation target read by `scripts/validate-skins.py` and the fixtures
under `skins/tests/`. When the canonical pair lands, a copy may be vendored only
with the pinned `contracts` tag and a test that proves byte equality; that test
does not exist yet and is not claimed.

## Template rules

`skins/templates/ags-bar.gtk.css.j2` keeps the app-local selector vocabulary
(`settings-surface`, `settings-net` and its `.sel` / `.out-of-range` /
`.confirming` states, `settings-rowact` and its states, the chevron, section,
divider, connected-details, empty, Wi-Fi settings and nav-header classes) and
replaces every visual constant with a `{{SKIN_*}}` placeholder. The placeholder
name is the upper-snake form of the token: `radius-panel` →
`{{SKIN_RADIUS_PANEL}}`, `bg-panel` → `{{SKIN_BG_PANEL}}`.

The template has no literal hex colour, no `transition`, no `animation` and no
structure/variant vocabulary. State colours that are not skin tokens (for
example a selected row's `@primary_container` / `@on_primary_container`) are
named `palette.v1` roles, not literals.

**Radius clipping is the app's job.** GTK CSS has no `overflow` property. When a
radius-clipped container's children can reach its corners, the app MUST set
overflow HIDDEN on the widget carrying `.settings-surface` (and any other
radius-clipped surface). The template comment states the same requirement; the
stylesheet can set the radius but cannot apply the clip.

## Validation

```bash
make validate-skins   # manifests + schema + placeholder coverage + no-hex/no-transition/no-structure
make test-skins       # pytest fixtures, including the negative cases
```

`make validate-skins` is stdlib-only and part of `make gates`. `make test-skins`
is the fixture suite and uses the repository's development pytest dependency.
