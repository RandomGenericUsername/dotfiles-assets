# Changelog

## v0.15.0 — host-default skin policy, contracts `v0.9.0`

### Added

- **`[host]` policy on `glass` and `paper`.** Both manifests now declare:
  ```toml
  [host]
  inherit = ["surface.panel.radius", "surface.panel.border-width"]
  fallback = "skin"
  ```
  A delegated token follows the live compositor when readable; the selected
  `mode.<mode>` group still wins, and the skin value is the headless/invalid
  fallback. `terminal` and `flat` carry an explicit opt-out comment and no
  `[host]` block: square/hairline and zero-chrome remain explicit identities.
  `[host]` is a policy object, not a token group.
- **Stdlib host enforcement.** `scripts/validate-skins.py` now implements
  `items`, `minItems` and `uniqueItems`, so the `inherit` enum, non-empty
  requirement and uniqueness are enforced without adding a dependency.
- **Host fixtures.** A positive `host.toml` plus negative empty/duplicate/
  unknown inherit, bad fallback and extra-key fixtures. Existing no-host
  manifests remain valid.
- **Contracts `v0.9.0` re-vendor.** `skins/contracts/` carries the v0.9.0
  appearance schemas and the generation manifest schema for contract-byte
  parity; `skins/contracts/PIN` records tag, peeled source commit
  `5c9fd615cae8d6596799bbafaeea93a05b3c3c11` and new sha256 hashes.

### Changed

- `skins/schema.json` names `canonical.tag = v0.9.0`, includes the vendored
  generation schema, and documents `[host]` as a policy object with
  `mode override > host > skin fallback` precedence.
- `skins/README.md`, root `README.md`, `catalog.yaml` and this changelog
  document the host policy, the four-skin opt-in matrix and the validation
  rules. The v0.14.0 wlogout template and exact `required_targets` gate are
  unchanged; all eight AGS + wlogout targets still expand.

### Notes

- **Expected manifest-hash churn.** Adding the `[host]` block changes the
  authored `glass` and `paper` manifest bytes, so their skin entry hashes
  change and therefore the first appearance/generation identities after this
  tag. `flat` and `terminal` manifests do not change. No path or token
  migration is needed; this is a one-time content-addressed churn.
- MINOR, additive corpus release. `schema_major` stays `2`; no existing token
  path, template target or resolved `tokens.json` field changed. Runtime,
  composition, provisioning and app pins land in their own tickets after this
  tag.

## v0.14.0 — wlogout paint/rhythm consumer target

### Added

- **`skins/templates/wlogout.gtk.css.j2`** — the first non-AGS CSS consumer
  target. It maps `surface.panel.bg` to `window`, `surface.control.*` and
  `ink.ink` to `button`, the `state.{hover,focus,selected}` triples to the
  button states, and `type.{font-family,font-weight,letter-spacing,size-title}`
  to `button span`. It contains paint/rhythm only: no literal hex,
  `transition`, animation, structure/variant, layout IDs, icons, wallpaper,
  grid or margins.
- **Required-target gate.** `skins/schema.json` now freezes
  `required_targets`; `scripts/validate-skins.py` compares it exactly with the
  discovered `<configDir>.gtk.css.j2` set. A missing `wlogout` template, or an
  unregistered extra target, fails `make validate-skins`.
- **Static stylesheet imports the generated sheet last.**
  `templates/wlogout/style.css.tpl` ends with
  `@import url("appearance.css");`, so the generated same-specificity paint
  rules win the GTK3 cascade. Wallpaper, icons, layout IDs and transitions stay
  static and app-owned. The palette import remains first, so a missing
  generated target leaves wlogout with palette-only styling at launch; GTK3
  still reports the missing import clearly.
- **Fixture coverage** for the wlogout template (all four manifests × both
  modes), missing required target, missing required-target declaration,
  unregistered extra target, literal hex and structure; the existing
  transition/unknown-placeholder/layout fixtures remain.

### Changed

- `skins/README.md`, root `README.md`, `templates/README.md`, `catalog.yaml`
  and `skins/schema.json` describe the eight-template set and the exact
  required-target contract.

### Notes

- **One-time template-hash churn (W-2.10).** Adding a template changes the
  canonical templates hash for every skin, so every skin entry hash changes and
  the first consumer refresh after this tag is a full appearance refresh even
  when existing AGS CSS is unchanged. Runtime, provisioning and composition
  pins are deliberately not changed in this slice; they land in their own
  tickets after this tag.
- MINOR, additive corpus release. The v2 manifest/resolved-token schemas and
  `schema_major: 2` are unchanged; no existing template value moved.

## v0.13.0 — `terminal` joins the built-in skins; cleanup-candidate layout tokens removed

### Added

- **A fourth v2 built-in: `terminal`.** `skins/manifests/terminal.toml`
  (name `"terminal"`) is the approved dense-monospace, square/hairline skin:
  opaque `@surface` panel with a `1px` `alpha(@on_surface, 0.22)` frame and zero
  radius, `@surface_container` cards, transparent/cell and control fills,
  `0/2px` radii, tight padding, `JetBrainsMono Nerd Font, monospace` at weight
  `500`, and a `9`/`10`/`12`/`13`/`14` type scale. State hover is
  `alpha(@on_surface, 0.10)`, selected is `@primary_container` on
  `@on_primary_container` with a `@primary` ring, focus uses the `@primary`
  ring, and disabled uses `alpha(@on_surface, 0.06)`. Every paint is a
  palette-role expression; there is no literal hex.
- **`terminal` is mode-agnostic.** The manifest has no `mode.dark`/`mode.light`
  overrides, so both modes resolve from the same base groups.

### Removed

- **The two cleanup-candidate layout blocks are gone from every manifest.**
  `[groups.layout.ags-capture]` (`panel-width = 560`) and
  `[groups.layout.ags-btop-studio]` (`left-width = 280`, `right-width = 320`)
  came from the apps' CSS `min-width` values, not their pre-v2 TSX defaults
  (`tickets/req-017-layout-defaults/ticket.md` §"Cleanup handoff"). The apps
  are being corrected to their pre-v2 natural layout in parallel, so `glass`,
  `flat`, `paper` and `terminal` no longer declare them. The remaining layout
  blocks stay: `layout.ags.panel-width = 312`,
  `layout.ags.bt-list-spacing = 4` (`paper` 6),
  `layout.ags-clipboard.card-width = 260`,
  `layout.ags-notifications.card-width = 380`,
  `layout.ags-wallpaper-selector = 960 × 640` and
  `layout.ags-icme = 1280 × 800`.

### Changed

- **The validator and fixture suite cover four manifests.** `skins/schema.json`
  `frozen.required_files` now requires `terminal`; `make validate-skins`
  expands all seven templates for four manifests × two modes (8 expansions),
  and every resolved `tokens.json` still validates against the vendored
  `appearance-json` schema. `make test-skins` pins terminal's frozen values,
  both-mode expansion, role-only/no-hex/no-transition values, the removed
  layout blocks and a positive terminal fixture under
  `skins/tests/fixtures/positive/`.
- **MINOR, additive skin.** No existing class path, template, token path,
  `schema_major` or resolved-document field changed. `terminal.toml` is a new
  manifest; the removed layout blocks are CSS minima the apps are dropping in
  their own commits.

## v0.12.2 — Layout defaults preserve the apps' pre-v2 window sizes

### Fixed

- **The default skin no longer resizes ICME or the wallpaper selector.**
  `layout.ags-icme.root-width` / `root-height` were `960 × 600` and
  `layout.ags-wallpaper-selector.root-width` / `root-height` were `920 × 600`:
  both pairs came from the apps' CSS `min-width`/`min-height`, but the apps use
  the tokens as default window sizes. Their pre-v2 TSX defaults are
  `1280 × 800` (`ags-icme@v0.3.0:ui/EditorWindow.tsx:612-613`) and
  `960 × 640`
  (`ags-wallpaper-selector@v0.3.0:ui/WallpaperSelectorWindow.tsx:600-601`).
  `glass`, `flat` and `paper` now carry those values, so a consumer on the
  default skin keeps the pre-v2 behaviour.
- **Two dead bar tokens are gone.** `layout.ags.bar-row-height` and
  `layout.ags.chip-min` are removed from all three manifests; no app source
  reads them. `layout.ags.panel-width = 312` and
  `layout.ags.bt-list-spacing = 4` remain because they are real TSX literals
  (`ags-bar@v0.3.0:settings-panel/SettingsPanel.tsx:22` and
  `components/bluetooth/BluetoothContent.tsx:750,798`).

### Notes

- **The remaining layout audit.** `layout.ags-clipboard.card-width = 260`
  (`ags-clipboard@v0.3.0:ui/ItemCard.tsx:179`) and
  `layout.ags-notifications.card-width = 380`
  (`ags-notifications@v0.3.0:ui/NotificationsWindow.tsx:60`) are real TSX
  literals and stay. `layout.ags-capture.panel-width = 560` and
  `layout.ags-btop-studio.left-width` / `right-width = 280` / `320` came from
  CSS `min-width` values, not TSX literals; the apps read them today, so they
  are kept and recorded as **cleanup candidates** in `skins/README.md` and the
  ticket. A follow-up decides whether they remain skin tokens or move back to
  TSX literals.
- **Consumer follow-up.** The migrated app fallbacks still name the old CSS
  minima (`ags-icme/ui/EditorWindow.tsx:88-89` = 960/600,
  `ags-wallpaper-selector/ui/WallpaperSelectorWindow.tsx:83-90` = 920/600).
  The `v0.12.2` default skin supplies the correct values, but the app
  repositories should align their fallbacks in their own commits.
- **PATCH, no path or schema change.** No class directory, file path,
  `schema_major` or template variable changed; `skins/tests/` pins the new
  layout defaults and the removed bar tokens.

## v0.12.1 — Hypr autostart leaves always-on AGS to systemd

### Changed

- **The AGS bar and notification apps are launched only by systemd user units.**
  Provisioning `v0.1.37` owns them as `dotfiles-ags-bar.service` and
  `dotfiles-ags-notifications.service`; `configs/hypr/autostart.lua` no longer
  starts `ags` or `notifications` through `ags-run-locked`. The wrapper's
  already-running pre-check made the old lines no-ops, but the second launch
  path is gone. The `capture` and `clipboard` overlays still start from
  autostart under the shared launch lock.
- **`make validate-configs` protects the boundary.** A re-added autostart line
  for the `ags` or `notifications` instance fails the gate, naming the systemd
  unit that owns it.
- **Ownership docs follow the change.** `configs/README.md` marks the bar and
  notifications as systemd-owned, and `templates/display-manager/hypr-session.j2`
  no longer claims the bar starts from the Hyprland config.

### Notes

- **PATCH, no path or contract change.** No class directory, file path,
  `schema_major` or template variable changed; consumers can pin `v0.12.1`
  without touching data. The systemd units themselves live in the provisioning
  repository and are not part of this corpus.

## v0.12.0 — Appearance plane v2 (schema_major 2)

### Changed

- **The skin class is now the v2 Appearance token model.** `glass`, `flat` and
  `paper` are `schemaVersion = 2` manifests with nested
  `surface.{panel,card,cell,control,pill}`, `state.{hover,selected,focus,disabled}`,
  `type`, `ink` and namespaced `layout.<app>` metrics. Per-role borders replace
  the v1 global `border-w`/`hairline-w` split; hover/selected/focus/disabled,
  the type scale and role paddings are first-class tokens.
- **`paper` declares explicit `mode.light` overrides.** The base groups remain
  the v1-equivalent dark-paper branch; the light branch is authored, so a light
  palette + `paper` reads light without guessing the palette mode.
- **All seven templates use flattened v2 placeholders.** `surface.panel.bg`
  renders through `{{SKIN_SURFACE_PANEL_BG}}`, `state.hover.fill` through
  `{{SKIN_STATE_HOVER_FILL}}`, and so on. Role borders/paddings, card/control/
  pill type and padding, state paint, small type and ink are tokenized; only
  component geometry with no token remains a literal. No template emits a
  `layout.<app>` token into CSS.
- **The canonical set is vendored at `contracts=v0.7.0`.** `skins/contracts/`
  now holds the appearance manifest/json/artifact schemas pinned by sha256 in
  `skins/contracts/PIN` (source commit `3ea6d83`); the frozen v1 skin schemas
  are kept at the same tag for provenance.
- **`make validate-skins` validates manifests, modes and tokens.json.**
  Each manifest validates against `appearance-manifest`, resolves under both
  `dark` and `light`, and the resolved document validates against
  `appearance-json`. The gate expands all seven templates for every manifest ×
  mode, enforces flattened placeholder coverage, rejects literal
  hex/transition/structure and layout placeholders, and keeps the unit rule
  (length → `<n>px`, letter-spacing → `<n>em`, font-weight unitless).
- **Parity is still the glass acceptance oracle.** The expanded bar keeps
  today's `1.5px` panel, `1px` card/control/pill hairlines, `8px 9px` cell padding, `9.5px`
  badge type and `0.05em` tracking. `skins/tests/` adds paper light/dark mode
  expansion, state/role coverage and new negative fixtures
  (unknown-surface-role, incomplete-mode, layout-placeholder).

### Notes

- **`schema_major` 1 → 2 is a breaking contract change.** The task fixes the
  corpus tag at `v0.12.0`; the repository is pre-1.0, so this 0.x minor is the
  breaking lane. Consumers must select by `schemaVersion`/`version: 2` and read
  `tokens.json`; v1 manifests are never reinterpreted as v2.
- **Asymmetric padding is partially literal.** The contract stores one numeric
  `padding` per surface role, so a pair such as card `10px 11px` keeps its
  second value in the template; the token carries the first/vertical value.

## v0.11.0 — skins templates for every non-bar AGS app

### Added

- **One extracted GTK template per non-bar app.** `skins/templates/` now holds
  `ags-clipboard.gtk.css.j2`, `ags-notifications.gtk.css.j2`,
  `ags-wallpaper-selector.gtk.css.j2`, `ags-capture.gtk.css.j2`,
  `ags-icme.gtk.css.j2` and `ags-btop-studio.gtk.css.j2`, named for each app's
  real `configDir` and rendered as `<configDir>.css`. Each template keeps the
  selectors and class vocabulary of that app's canonical `style.css`.
- **Fidelity extraction, not a second design system.** `{{SKIN_*}}` is used
  only for genuine global knobs (panel background/border/border-width/radius/
  shadow/blur, card background/radius, cell radius/padding, control radius,
  pill radius, hairlines via `hairline-w`, ink/ink-dim/accent and title/text
  sizes). Component paddings, small type, thumbnail radii, selection rings and
  the recording red stay source literals expressed as `palette.v1`
  roles/alpha derivatives.
- **Per-app checks.** `skins/tests/test_skins.py` expands every template through
  `glass`, `flat` and `paper`, asserts placeholder coverage, rejects literal hex,
  transitions/animations and layout placeholders, and names the expected
  top-level selectors for all seven targets.

### Changed

- **`make validate-skins` reports the full template set.** Its summary prints
  `templates=7` and every target, and its notes record that each template
  expanded for all three manifests. The gate still enforces the PIN hashes,
  canonical numeric types, palette roles, naming and unit-rule expansion.
- **README, `skins/README.md`, `catalog.yaml` and the ticket** record the
  seven-target template set and the `v0.11.0` inventory.

### Notes

- **MINOR, additive only.** No token changes, no class path moves and
  `schema_major` stays `1`; the shared `glass`/`flat`/`paper` values now paint
  the new app surfaces through the same 24-token vocabulary.

## v0.10.0 — skins hairline token and TSX-owned layout

### Added

- **`hairline-w` is the 24th skin token, in `[shape]`.** It is a unitless
  numeric token like `border-w`: `glass = 1`, `flat = 0`, `paper = 1` (the
  expander renders `<n>px`). `border-w` is now only the outer panel/frame
  border (`1.5px` in glass); `hairline-w` is the card, tile, mini, password,
  row-action and badge hairline (`1px` in glass/paper), and the Wi-Fi settings
  top rule. This removes the `v0.9.1` deviation where a single `border-w`
  forced every source `1px` hairline to `1.5px`.
- **The template never emits a layout token.** `.settings-surface` no longer
  emits `min-width` from `panel-width`; `.settings-net` no longer emits
  `margin-bottom` from `bt-list-spacing` or `min-height` from `bar-row-height`;
  `.settings-rowact` no longer emits `min-width` from `chip-min` or
  `min-height` from `bar-row-height`. Those metrics stay in the manifest and
  resolved `skin.json` for `skinValue()` and are owned by the TSX widgets
  (panel width, list spacing, row/chip geometry). The template keeps the
  source's component literals (for example the `30px` signal glyph).
- **Row parity is restored.** `.settings-net` keeps `border: none` (no
  transparent border), no `margin-bottom` and no layout `min-height`, so its
  allocated height matches the source's 50px instead of the 54px the template
  overlay produced.

### Changed

- **The canonical set is re-vendored at `contracts=v0.6.0`.** `skins/contracts/`
  holds byte copies of `skin-token.schema.json`,
  `skin-manifest.schema.json` and `skin-json.schema.json` from the
  hairline/layout-ownership release. `skins/contracts/PIN` records
  `contracts=v0.6.0`, source commit `e512f5c` and the three sha256 values;
  `skins/schema.json` names `canonical.tag: v0.6.0`, requires `hairline-w` in
  the local envelope, and states the ownership split and the layout rule.
- **`make validate-skins` reports 24 tokens.** The gate still validates the
  PIN hashes, canonical `$ref` delegation, numeric-string rejection,
  placeholder coverage and unit-rule expansion; it now also accepts
  `hairline-w` and reports the layout tokens as declared-but-not-templated.
- **Parity tests assert the split.** Expanded glass has a `1.5px` panel border
  and `1px` hairlines, `.settings-net` has `border: none` with no
  `margin-bottom`/`min-height`, no layout placeholder is emitted, and there is
  no literal hex or transition. The parity deviation fixture is now empty: the
  border widths match the source.
- **README, `skins/README.md`, `catalog.yaml` and the ticket** record the new
  token, the TSX-owned layout rule, the `v0.6.0` pin and the `v0.10.0`
  inventory.

### Notes

- **MINOR, additive vocabulary.** `hairline-w` is a new shape token; no other
  token changes, no class path moves, and `schema_major` stays `1`. The four
  layout tokens are unchanged in the data plane and still appear in
  `skin.json`; only the template stops consuming them.

## v0.9.1 — skins template naming and the resolved skin.json schema

### Fixed

- **The GTK template now has the contract name.** `skins/templates/ags-bar.gtk.css.j2`
  is renamed to `skins/templates/ags.gtk.css.j2` (`git mv`, body unchanged).
  `contracts` `v0.5.2` freezes one template per target config directory, named
  `<configDir>.gtk.css.j2` and rendered as `<configDir>.css`; the bar's
  `configDir` is `ags`. The old prefix was a name an expander following
  `skins.md` would never find, so the target was unreachable even with a green
  gate.
- **`scripts/validate-skins.py` enforces the naming convention.** Every file in
  `skins/templates/` must match
  `^[a-z0-9][a-z0-9_-]*\.gtk\.css\.j2$`; the target is the prefix. An unexpected
  file is an error, and the summary now prints `templates=<n>` and
  `targets=<configDir>` (`targets=ags` for this corpus). A stale
  `ags-bar.gtk.css.j2` fixture proves the check bites.

### Changed

- **The canonical set is re-vendored at `contracts=v0.5.2`.** `skins/contracts/`
  now holds byte copies of `skin-token.schema.json`,
  `skin-manifest.schema.json` and the resolved-document
  `skin-json.schema.json`; `skins/contracts/PIN` records `contracts=v0.5.2`, the
  source commit `320ad69` and the sha256 of all three. The token/manifest bytes
  are unchanged from `v0.5.1`, so only the pin tag and the new file change.
- **`skins/schema.json` names the current interface and the resolved document.**
  `canonical.tag` moves to `v0.5.2`, `canonical.resolved_document` names
  `skins/contracts/skin-json.schema.json`, and the note states that the runtime
  emits one shared `current/skin.json` (`version: 1` plus the six groups, numeric
  tokens as raw JSON numbers). Token/manifest delegation is unchanged.
- **The test suite validates the document the platform parses.** A resolved glass
  document built from the manifest (`version: 1` + the six groups, raw numbers)
  is validated against the vendored `skin-json` schema; a numeric string in that
  document is rejected. The suite also asserts the template target and the PIN's
  source commit.
- **README, `skins/README.md`, `Makefile`, `catalog.yaml` and the ticket** record
  the `<configDir>.gtk.css.j2` rule, the `ags` target, the `v0.5.2` pin and the
  resolved-document schema.

### Notes

- **PATCH, no token or `schema_major` change.** The 23-token vocabulary, six
  groups, all manifest values and `schema_major: 1` are unchanged. The class
  path `skins/templates/` did not move; only the template filename changed to
  the name the contract freezes. Existing tags are not moved.

## v0.9.0 — skins value types (unitless numbers, vendored canonical schemas)

### Fixed

- **Skin numeric tokens are unitless TOML numbers, not `"12px"` strings.** The
  canonical `contracts` schema types `radius-panel`, `radius-card`,
  `radius-cell`, `radius-pill`, `border-w`, `gap`, `title-size`, `text-size`,
  `panel-width`, `bt-list-spacing`, `bar-row-height` and `chip-min` as JSON
  numbers; AGS rejects the string form at startup. `glass`, `flat` and `paper`
  now store `12` / `1.5` / `8` / `12.5` / `312` etc. Only `cell-pad` remains a
  length string (`"Npx Npx"`), and only paint/ink/`font-family` remain strings.
  Glass keeps every `v0.8.0` parity value; this is a representation fix.
- **The canonical pair is vendored and pinned.** `skins/contracts/` holds
  byte-for-byte copies of `skin-token.schema.json` and
  `skin-manifest.schema.json` at `v0.5.1`, the unit-convention patch.
  `skins/contracts/PIN` records `contracts=v0.5.1`, the source commit and each
  file's sha256. `skins/schema.json` now sets `canonical.vendored: true`,
  `canonical.tag: v0.5.1`, and delegates every token value type by external
  `$ref` to the vendored manifest schema — the local `px`/`dimension` lookalike
  grammar is gone.

### Changed

- **`scripts/validate-skins.py` validates canonical types and expands the unit
  rule.** It checks the PIN hashes and the `$ref` delegation, rejects a numeric
  string (`radius-panel = "12px"` → must be a number), and expands every
  manifest through the template with number → `<n>px` (numeric tokens in CSS
  length positions) while emitting `cell-pad` verbatim.
- **`skins/tests/` covers the new contract.** Added PIN byte-equality,
  vendored-type, delegation, numeric-string fixture and unit-expansion tests;
  the parity suite still asserts the expanded glass contains
  `border-radius: 12px`, `border: 1.5px solid @primary`, `padding: 8px 9px`,
  `border-radius: 20px`, `font-size: 12.5px` and `min-width: 312px`.
- **`skins/README.md` and root `README.md`** document the value convention
  (number = unitless, `px` at render time) and the vendoring/pin rule. The
  `skins/` class now lists `contracts/` among its subdirectories.

### Notes

- **MINOR, no path or token change.** The 23-token vocabulary, six groups and
  `schema_major: 1` are unchanged; only the value representation and the
  validation source moved. `flat` keeps `0/0/0/999` radii, `0` border, `8` gap,
  `15`/`13` type and `312/4/28/48` layout; `paper` keeps `6/4/3/999`, `1`
  border, `9` gap, `15`/`13` type and `312/6/30/52` layout. `paper`'s shadow,
  role expressions and `cell-pad` strings are untouched.
- **Canonical tag honesty.** `v0.5.1` became reachable in the local `contracts`
  checkout during this work, so the vendored bytes were re-taken from that tag
  rather than from the older `v0.5.0` checkout. The PIN records the actual tag
  and hashes. The skin schemas are unchanged again at `v0.5.2`, but the pin stays
  on `v0.5.1`, the tag that defines the unit convention.

## v0.8.0 — skins fidelity (glass = today's ags-bar)

### Fixed

- **`glass` is now a literal parity extraction of `../ags-bar/style.css`, not a
  design-system re-expression.** Panel `12px` radius / `11px` padding /
  `1.5px @primary` hairline / no shadow, card `alpha(@surface_container_high,
  0.18)` / `9px` / `10px 11px`, row `8px 9px` padding / `7px` radius, badge
  `20px` radius / `9.5px` type, and the 10.5–12px small-text values all match
  the source. `bt-list-spacing` is `4px`, `bar-row-height` and `chip-min` are
  `0px`, and `title-size`/`text-size` are `12.5px`/`13px`.
- **`skins/templates/ags-bar.gtk.css.j2`** now uses `{{SKIN_*}}` only where the
  frozen token is a genuine global knob. Component padding, small type,
  scrollbar/slider geometry, row borderlessness, nav-header measurements and
  badge type stay literal, expressed with `palette.v1` roles only. The window
  root applies `font-family` but no `font-size` (today inherits it).
- **`skins/tests/test_parity.py`** expands glass through the validator's own
  placeholder map and asserts every source declaration (with line references),
  no non-`none` shadow, no transition/animation, no hex, and the explicit
  deviations. `fixtures/parity/deviations.json` records the five hairline cases.

### Changed

- **`skins/README.md`** documents the v1 limitations: which component details
  are not skin-controlled and why, and the one unavoidable visual deviation.
  The local schema's `ink`/`ink-dim`/`accent` now accept the same
  role-or-role-expression grammar as the canonical contracts `inkValue`; the
  23-token set is unchanged.
- **`flat`/`paper`** keep their own values under the corrected template
  semantics; `flat` remains transparent/borderless and `paper` remains
  role-based.

### Notes

- **MINOR, no path or token change.** The frozen v1 23-token contract is
  unchanged (`contracts` `v0.5.0`). The remaining visual deviation is the single
  `border-w` token: the panel needs `1.5px`, so the source's `1px` card, row,
  badge and Wi-Fi-footer hairlines render `1.5px` (+0.5px). A second
  border-width token would break the frozen contract, so the deviation is
  recorded rather than hidden.
- **No transition declarations.** GTK 4.24 ignores them; the source's switch
  transitions and switch shadows remain app-owned and are not copied into the
  skin template.

## v0.7.0 — skins class (frozen v1)

### Added

- **The sixth class, `skins/`.** A skin is a palette/ink mapping, paint and
  rhythm/density — never structure or a variant. The frozen v1 token groups are
  `shape` (`radius-panel/card/cell/pill`, `border-w`), `rhythm` (`gap`,
  `cell-pad`), `surface` (`bg-panel`, `bg-card`, `border`, `shadow`, `blur`),
  `ink` (`ink`, `ink-dim`, `accent`, `ink-over`), `type` (`font-family`,
  `title-size`, `text-size`) and `layout` (`panel-width`, `bt-list-spacing`,
  `bar-row-height`, `chip-min`).
- **Three manifests.** `skins/manifests/glass.toml` is the default/fallback
  parity skin (16/12/8/999px radii, 1.5px border, 312px panel, 30px bar row);
  `flat.toml` removes every surface/border and tightens rhythm; `paper.toml` is
  the light/palette axis expressed with `@surface_container_lowest` (panel) and
  `@surface_container_low` (card), so its appearance depends on the palette mode
  rather than a baked literal.
- **`skins/templates/ags-bar.gtk.css.j2`.** The Bluetooth-panel and settings
  selectors (`settings-surface`, `settings-net` + selected/out-of-range/
  confirming, `settings-rowact` + disabled/danger/subtle, chevron, section,
  divider, connected-details, empty, Wi-Fi settings and nav-header classes) now
  expand `{{SKIN_*}}` tokens. No literal hex, no transitions, no animation, and
  the radius-clipping comment states that the app must set overflow HIDDEN.
- **`make validate-skins` + `skins/tests/`.** The stdlib gate proves the local
  schema pointer is honest, the manifest token set is exact, every role is
  `palette.v1` (no aliases), surface values are role expressions, and template
  placeholders cover the schema two ways. The pytest fixtures prove the no-hex,
  no-transition, no-structure, unknown-role, missing-token, unknown-placeholder
  and false-vendoring cases fail.
- **`skins/schema.json`** is the data-only validation target and names the
  canonical `contracts` paths (`schemas/skin-token.schema.json`,
  `schemas/skin-manifest.schema.json`). The reachable `contracts` tag has no
  skin schema, so the file records `canonical.tag: null` and
  `canonical.vendored: false`; no copy or byte-equality claim is made.

### Changed

- **`catalog.yaml` now declares six classes**, `skins` is schema-bearing at
  `schema_major: 1`, and `make validate` asserts the class set both ways. The
  five pre-existing class paths did not move.
- **`make gates`** adds `validate-skins`; CI has the matching job, so
  `make ci-gates-parity` still compares the two sets in both directions.
  `make test-skins` is the fixture suite and needs the development pytest
  dependency, so it is not a member of the fresh-clone gate set.

### Notes

- **MINOR, no existing path change.** The class is additive at
  `schema_major: 1`; no icons/templates/configs/content/desktop path or contract
  moved. The consumer pin bump is a separate commit in its own repository.
- **Recorded discrepancy:** `../ags-bar/style.css` paints cards at
  `alpha(@surface_container_high, 0.18)` with a solid `@primary` border, while
  the frozen v1 glass manifest is `0.88` and `alpha(@primary, 0.35)`. The
  frozen spec wins; the template expands the frozen values rather than silently
  redefining the stylesheet.
- **Out of scope:** changing the ags-bar app, adding light/dark variants or
  structure tokens, and installing/pinning anything in a consumer.

## v0.6.4 — static configs on semantic roles

- `configs/rofi/launcher/config.rasi`: migrate from CSG carrier tokens to
  `palette.v1` roles (rasi identifiers hyphenated): frame `@surface-container`,
  content `@surface`, field `@surface-container-high`, accent/border
  `@primary`, selected row `@primary-container`/`@on-primary-container`, ink
  `@on-surface`, placeholder `@on-surface-variant`. `@color01` was the Material
  **error** role in every palette, which is why rofi's window never changed
  color with the wallpaper.
- `templates/wlogout/style.css.tpl`: role names (`@on_surface`,
  `@primary_container`) instead of `@color_15`/`@color_12`/`@color_07`.
- No geometry or behavior changes; rendered rofi parses cleanly and resolves
  role variables.

Notable changes to `dotfiles-assets`. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved). This repository ships no build artifacts: a
release is a tag with notes, and the corpus is the source.

## [0.6.2] — 2026-10-27

### Changed

- **Every AGS cold start takes the shared launch lock.** `configs/hypr/autostart.lua` now starts
  the bar, capture, notifications and clipboard instances through the provisioned
  `ags-run-locked` wrapper with `--expect-instance` (`ags`, `capture`, `notifications`,
  `clipboard`), replacing four bare `ags run` lines. AGS 3.1.0 bundles into one
  `$XDG_RUNTIME_DIR/ags.js`, so login-time starts raced each other and the runtime's restart lane
  (AD-28). The 2/3/4 s staggers stay: the wrapper releases the lock when the expected instance
  registers on the AGS bus, not when the process exits, so login is ordered but never deadlocked.
  The wrapper is installed by the consumer's `cli_tools` role; autostart invokes
  `$HOME/.local/bin/ags-run-locked` explicitly, like `gloview-activate`, so startup does not
  depend on a login-shell PATH.
- **The clipboard overlay is `clipboard`, not `hypr-pano`.** Autostart starts
  `~/.config/ags-clipboard` as instance `clipboard` with `clipboard.log`, and the `SUPER + V`
  bind invokes `clipboard-ui` (description unchanged, “Open clipboard history”), per the AD-35
  rename owned by `ags-apps` REQ-009. Comments in `configs/hypr/env-variables.lua`,
  `configs/README.md` and `desktop/README.md` carry the new launcher name.
- **`configs/README.md` documents the AGS launch discipline** — the lock lifecycle, the
  per-surface identity table, and a rename note that points at the REQ-007 acceptance grep
  proving no live retired name remains under `configs/` or `desktop/`.

### Notes

- **PATCH, no inventory change.** Same paths, same file count, no schema change, so
  `catalog.yaml` stays at `v0.6.0` (the inventory tag); the consumer pin bump is a separate
  commit in its own repository.
- **Provision follow-up, not in this repo:** `clipboard-ui` and the `~/.config/ags-clipboard`
  config link are rendered by the consumer's `cli_tools`/`config_links` roles, and the app is
  `ags-apps` REQ-009. Until that cutover deploys, the new autostart/keybind lines name launchers
  this corpus does not install — by design: no destination or installed binary is named here.
- Historical `hypr-pano` mentions remain only in this changelog and the REQ-007
  ticket/INDEX record; no live reference remains under `configs/` or `desktop/`.

## [0.6.1] — 2026-10-26

### Fixed

- **wlogout Logout no longer tears down the user.** `configs/wlogout/layout:15` now runs
  `uwsm stop` instead of `loginctl terminate-user $USER`. The old action ended every session of
  the user, including the systemd user manager; logind's SIGHUP killed the SDDM helper, and SDDM
  0.21.0 read that exit code as an authentication error and skipped the greeter restart, leaving a
  black VT with a cursor (provision `BUG-005`, upstream SDDM [#1908](https://github.com/sddm/sddm/issues/1908)).
  `uwsm stop` stops the compositor unit and lets the helper exit normally, so SDDM returns to the
  Pixie greeter. The action is user-approved (2026-10-26); the VM matrix was waived and the host
  5-cycle logout acceptance runs after the consumer re-provision.
- **`make validate-configs` pins the logout action.** The gate now parses `configs/wlogout/layout`
  as a sequence of JSON tiles and fails unless the single Logout tile's action is exactly
  `uwsm stop`, so a future edit cannot silently restore `terminate-user`.

### Notes

- **PATCH, no inventory change.** Same paths and no schema change, so `catalog.yaml` stays at
  `v0.6.0` (the inventory tag); the consumer pin bump is a separate commit in its own repository.

## [0.6.0] — 2026-10-26

### Added

- **An explicit SDDM Wayland greeter compositor.** `templates/display-manager/sddm.conf.j2` now
  renders a `[Wayland]` section after `[General]`:
  `CompositorCommand={{ display_manager_sddm_compositor_command | default('weston --shell=kiosk') }}`.
  The rendered config no longer relies on SDDM's implicit `Weston` default; a host that sets
  `DisplayServer=wayland` and does not install `weston` can now be failed at deploy time instead of
  falling back to `DisplayServer=x11-user` at the greeter.
- **Optional `display_manager_sddm_compositor_command`** in
  `templates/display-manager/sddm.conf.vars.schema.json`: a non-empty string, listed in `optional`
  only, with **no schema-level default** — the fallback lives in the template body. `required` still
  names only `display_manager_sddm_display_server`; `schema_major` stays **1** because the addition
  is optional and additive.
- **`make validate-templates` asserts the SDDM contract.** The gate fails when the `[Wayland]`
  section, the `CompositorCommand` line or the `weston --shell=kiosk` fallback disappears, or when
  the variable stops being optional. When `jinja2` is importable it renders the body with the
  required variable only (fallback) and with the override (consumer value); the stdlib-only run
  still asserts the section and the exact default expression.

### Changed

- `catalog.yaml` records **24 required variables and 1 optional** for `templates/` and moves the
  corpus tag to `v0.6.0`; `README.md`, `templates/README.md` and the OpenSpec capability spec carry
  the new inventory and the SDDM scenario.

### Not here, on purpose

No `weston` package, role variable, SDDM service change or pin bump: the consumer's
`display_manager` role installs the package, passes the optional value and updates its own mirrors
to `v0.6.0`. No rendered `sddm.conf` is committed.

## [0.5.1] — 2026-10-22

### Added

- **`scripts/validate-configs.py` / `make validate-configs` (R-05/R-06).** A new `GATES` member
  with its own CI job: no `*.j2`/`*.tpl` source under `configs/`, no mutable preference
  (`active-theme`, `theme-map.yaml`) or rendered output (`.zshrc`, `kitty.conf`, `btop.conf`,
  `settings.toml`, `icons.json`, `style.css`), every file non-empty, and exactly one render token
  at `configs/hypr/hyprland.lua:7` (`{{ compositor_configs_xdg_config_home }}`). A second token
  fails naming both files and lines; a stray `.j2` fails naming the file. This turns the four
  release-time manual commands in `configs/README.md` into an executable release gate.

### Notes

- **No corpus bytes changed.** This is a validator/gate PATCH; consumers pinned at `v0.5.0` see
  the same corpus. Per the release-runbook rule (R-12), a docs/gate-only correction ships as a
  new tag and does not force a consumer pin bump when the corrected file is not a consumed
  surface.

## [0.5.0] — 2026-10-22

### Added

- **`desktop/` corpus, imported verbatim.** Six `.desktop` entries in `desktop/applications/` and
  `toggle-touchpad` in `desktop/scripts/` (mode `0755` preserved), copied from the consumer corpus.
  `cmp` returns 0 for the script; each entry differs from its source by exactly **one added line**,
  its `TryExec=`, which layer 1 requires and the pre-split corpus never carried. Every packaged
  `Exec`, comment, category, MIME type and startup hint is unchanged.
- **`TryExec=` on all six entries.** A launcher probes `TryExec` to decide whether an application is
  installed; without it a missing binary still produced a listed, dead menu entry. The value is the
  binary `Exec` launches — the IDE/TIDAL binary for the four overrides, `kitty` for the two
  kitty-hosted CLIs.
- **`desktop/desktop.yaml`, the class contract** (`schema_major: 1`): one record per entry,
  `{file, requires, optional}`. `requires` is the entry's own launcher (`basename(Exec argv[0])`,
  which is also its `TryExec`); `optional` is the payload a wrapper entry runs inside that launcher
  (`codex`, `copilot`). The consumer resolves `requires` before it deploys — a missing one fails the
  run naming entry and binary — and reports/skips an entry whose `optional` binary is absent. The
  corpus never decides whether a package is installed.
- **`scripts/validate-desktop.py` / `make validate-desktop`** (`validate-desktop` is a `GATES`
  member with its own CI job). Layer 1 of AD-10: every entry parses as a Desktop Entry
  (`[Desktop Entry]`, `Type`, `Name`, `Exec`, `Icon`), `Exec` is tokenized with the spec's quoting
  rules and its argv[0] basename must be a declared `require`, `TryExec` must be present and name
  that same binary, the contract must equal the `.desktop` set exactly in both directions, and every
  script must be executable with a `#!` shebang. The same target runs `shellcheck` over
  `desktop/scripts/*` (and `make lint` stays the class-independent sweep).
- **`desktop/README.md`** — the three validation layers and their owners, the `TryExec` rationale,
  the `requires`/`optional` derivation, the scope boundary (the Jinja launcher wrappers stay with
  the consumer's `cli_tools` role) and the vacuity proof.

### Changed

- **`catalog.yaml` declares `desktop` schema-bearing** (`desktop/desktop.yaml`, `schema_major: 1`)
  and records the real contents. `desktop/` is no longer "empty in a later tag": all five classes
  are populated at this tag.
- **`validate-catalog.py` reads a YAML contract as well as a JSON one.** The class contract for
  `desktop` is YAML, so the `schema_major` rule (AD-12) is applied through the same strict subset
  parser rather than a JSON-only path. The subset gained sequence-of-mappings items
  (`- file: x.desktop`) so a record list parses; anything outside the subset is still a hard error.
- **`make lint` is no longer vacuous.** `desktop/scripts/` holds `toggle-touchpad`, so
  `shellcheck` now has a real subject; the vacuous-pass message remains for a future empty class.

### Not here, on purpose

No launcher wrappers (`rofi-ui`, `capture-ui`, `hypr-pano-ui`, `wallpaper-selector-ui`,
`icon-color-mapping-editor`, `btop-theme-studio`): they are Jinja-rendered by the consumer's
`cli_tools` role because they bake in installed-binary paths (AD-10 scope boundary). No installed
binaries, no `mimeapps.list`, no launcher database: a declared binary is not an installed package,
and derived state belongs to the host.

## [0.4.0] — 2026-10-22

### Added

- **`templates/` corpus, imported verbatim.** Nine Jinja sources in five group directories, copied
  byte-for-byte from the consumer corpus with their bodies unchanged: `zsh/.zshrc.j2`,
  `wlogout/style.css.tpl`, `kitty/kitty.conf.j2`, `btop/btop.conf.j2` and the five
  `display-manager/{sddm.conf,config.toml,regreet.toml,regreet.css,hypr-session}.j2`. `diff` against
  the consumer's sources returned 0 for every file before the consumer deleted its copies.
- **Nine `*.vars.schema.json` contracts, one beside every template.** Each is a draft 2020-12
  object schema with `schema_major: 1`, the sibling `template`, typed `properties`, disjoint
  `required`/`optional` and `additionalProperties: false`. Together they declare **24 required
  variables and zero optional** — every name is one the body actually reads.
- **`scripts/validate-templates.py` / `make validate-templates`** (`validate-templates` is a
  `GATES` member, with its own CI job). It asserts: complete pairing in both directions; every read
  appears in `properties` and every property is read (**contract equals body**, so a required name
  the template never reads cannot exist); `required ∪ optional == properties`; no `default(` on a
  required variable; `required` non-empty whenever the template reads something; and every keyword
  is a real 2020-12 keyword (or an `x-` extension) with a correctly typed value. Stdlib-only; when
  `jsonschema` is importable it additionally validates each schema against the 2020-12 metaschema
  and proves the closed-world / required-missing claims with negative instances, and says so when
  that mode is skipped.
- **`catalog.yaml`** — `templates` declares its five group subdirectories, its real contents and a
  **glob** contract (`templates/**/*.vars.schema.json`); `validate-catalog.py` learned to hold every
  glob match to the catalog's `schema_major` instead of one arbitrary representative file.

### Changed

- **`{{ }}` is not the whole contract.** The validator reads `{% %}` expressions too, so
  `display-manager/config.toml.j2` requires **two** names (`display_manager_greeter_type` in its
  `{% if %}`, `display_manager_greeter_user` in the `[default_session]` line). The plan's "1 var"
  figure came from a `{{ }}`-only grep and under-counted the branch variable.
- **Three display-manager templates are contracts, not live renders.** `regreet.toml.j2`,
  `regreet.css.j2` and `hypr-session.j2` are retained for the consumer's greetd+regreet fallback
  (spine AD-9); the default login path is SDDM + Pixie. Their schemas describe the values that path
  would need, and two of them are legitimately variable-free (`required: []`).
- **`templates/example.vars.schema.json` removed.** The shape file is retired now that nine real
  contracts exist; `templates/README.md` carries the schema shape, the inventory and the rules.
- **`wlogout/style.css.tpl` keeps its source mode.** The imported file is `100755` in the consumer
  repository; the mode came along with `cp -a`. Content (not mode) is the contract.

### Not here, on purpose

No rendered `.zshrc`, `style.css`, `kitty.conf` or `btop.conf`: the templates and their contracts
ship, the values stay with the consumer (AD-8/AD-11). `make validate` fails on any of those names.

## [0.3.1] — 2026-10-21

### Fixed

- **The `configs/` boundary prose was wrong for `hypr/hyprland.lua`.** The v0.3.0 README claimed
  "nothing here is rendered"; in fact `hyprland.lua:7` carries one consumer-resolved token
  (`{{ compositor_configs_xdg_config_home }}`, the directory its twelve modules are loaded from)
  and the consumer renders it on deploy — the file says so in its own header. The class is now
  described as **deployment-fixed** rather than "static": the rule is the fixed destination and the
  absent variable contract, not the absence of braces. The documented exception, the one-token
  acceptance grep and a scenario for a second token were added to `configs/README.md` and the
  spec. Corpus bytes are identical to v0.3.0 — this is a documentation correction, and the tag is
  new rather than moved.

## [0.3.0] — 2026-10-21

### Added

- **`configs/` corpus, imported verbatim.** 25 static config files in six tool directories: 13
  Hyprland Lua files, `hyprpaper/hyprpaper.conf`, `rofi/launcher/config.rasi`, 8 Neovim files,
  `starship/starship.toml` and `wlogout/layout`. Copied byte-for-byte — `diff -r` returned 0 for all
  six directories before the consumer deleted its copy — so every consumer destination keeps the
  bytes it had. `configs/README.md` documents the per-file boundary and the exclusions.
- **wlogout is one file, not a directory.** `layout` is static config and ships here; `style.css` is
  rendered from a five-variable Jinja source whose values (palette path, runtime state root, current
  wallpaper, font family, font size) only exist on a provisioned host. The source is the `templates`
  class (v0.4.0) and the rendered file is the consumer's. A directory copy would have carried both
  halves together — the boundary failure this split removes.

### Changed

- `catalog.yaml` — `configs` declares its six subdirectories and its real contents, and `tag` moves
  to `v0.3.0`. The class enumerates no schema file (`schema_major: null`, deliberate).
- `openspec/specs/assets-catalog/spec.md` — a requirement for the static-config boundary, with the
  three acceptance commands that prove it.
- `README.md` — the status line names `configs` as populated, and the contracts section states that
  this class's contract is a boundary rather than a schema document.
- **`[0.2.0]` heading corrected.** The v0.2.0 corpus entry was still filed under `[Unreleased]` in
  the tagged tree; it now carries the version it actually shipped as. Documentation only — the
  tag's bytes are untouched.

## [0.2.0] — 2026-10-21

### Added

- **`icons/` corpus, imported verbatim.** 117 SVGs in 12 template directories, copied
  byte-for-byte from the dotfiles corpus. `icons/mappings/defaults.yaml` is the group-independent
  `COLOR_*` vocabulary, **not** a group map; `icons/mappings/icons.yaml` is the one group map.
  `icons/README.md` documents the group/template/output shape and the placeholder merge order.
- **Six stale duplicate mapping files retired (deviation from the verbatim import).**
  `battery.yaml`, `email-client.yaml`, `network.yaml`, `power-menu.yaml`,
  `wallpaper-selector.yaml` and `wlogout.yaml` were removed instead of imported. Evidence: the ITR
  loader takes a single YAML path and the runtime and `sync-icons-manifest` read `icons.yaml` only,
  so nothing loaded them; they duplicated groups owned by `icons.yaml` and had drifted
  (`network.yaml` referenced 12 templates deleted in the network rework, and `battery.yaml` /
  `power-menu.yaml` carried different variant sets or `color_mappings`). `icons.yaml` and
  `defaults.yaml` remain byte-identical to the source. `make validate-icons` now fails if any other
  `*.yaml` appears under `icons/mappings/`, so the split cannot recur.
- **`content/` corpus, imported verbatim.** `content/wallpapers/wallpapers.tar.gz` is the original
  archive, **not repacked** (its bytes are the contract; the runtime derives a hash from them) and
  holds a top-level `default.png`. `content/btop-themes/` holds authored themes only — empty today —
  and never the mutable active-theme preference (spine AD-11). `content/README.md` says why.
- **`scripts/validate-icons.py` / `make validate-icons`** — the gate the corpus never had: every
  mapping `template:` resolves under the templates root (honouring a group's `template_dir`), every
  `{{COLOR_*}}` token used by a template is declared in `defaults.yaml` or that group's / variant's
  `color_mappings`, every SVG parses as XML, variant names are unique per group, `output` is a bare
  file name, and `mappings/` holds exactly one group map plus the vocabulary. It reports unused
  tokens and unreferenced templates without failing the tag.
- **`scripts/validate-content.py` / `make validate-content`** — the tarball contains a top-level
  `default.png`, every `*.theme` is non-empty, and no archive member escapes the archive root.
- **`icons/schema.json` extended** to the concrete consumer shape: `group → color_mappings →
  variants[{name, template, output}]`, variant paths relative to the group's template root, the
  group/consumer metadata fields, and the lowest-to-highest merge order. It also corrects the
  skeleton's "a group is a directory" statement: a group is a top-level key, and only
  `template_dir` selects a directory.
- **`Makefile` / `.github/workflows/gates.yml`** — `GATES` is now `validate validate-icons
  validate-content lint hermetic`, with one CI job per gate and `ci-gates-parity` still comparing
  the two lists in both directions. `hermetic` runs both class validators with empty `HOME`/`XDG_*`
  from a foreign cwd.
- **`catalog.yaml`** — `content/` declares its `wallpapers` and `btop-themes` subdirectories, and
  every class states what it actually holds at this cut.

## [0.1.0] — skeleton — 2026-10-21

First release, deliberately empty. The point of tagging an empty corpus is to prove the release
ritual (gates green → changelog → annotated tag → CI green → anonymous clone passes) before the
expensive migration depends on it.

### Added

- **Five class directories** with the layout consumers will address literally: `icons/templates/`,
  `icons/mappings/`, `templates/`, `configs/`, `content/`, `desktop/applications/`,
  `desktop/scripts/`. Each is `.gitkeep`-backed so it survives a clone. `catalog.yaml` records all
  five with `contents: empty in v0.1.0` and a `schema_major` for the two schema-bearing classes.
- **`icons/schema.json`** (`schema_major: 1`) — the icons contract: a group's `variants[]` carry
  `{name, template, output}` with `template` relative to the templates root, plus the
  `{{COLOR_*}}` placeholder vocabulary rules. New work: no schema file existed in the corpus
  before this repository.
- **`templates/README.md` + `templates/example.vars.schema.json`** (`schema_major: 1`,
  `required[]` / `optional[]`) — the shape every `*.vars.schema.json` takes once the templates
  land. The `example.` prefix marks it as the shape, not a live contract.
- **`scripts/validate-catalog.py`** — one stdlib-only validator for the corpus envelope: catalog
  ⇄ class-dir agreement (including undeclared subdirectories), schema JSON well-formedness and
  `schema_major` agreement, and the mechanical **absence check** for generated/mutable artifacts
  (`icons.json`, `settings.toml`, rendered `kitty.conf` / `btop.conf` / `.zshrc`, `active-theme`).
  Stdlib-only on purpose: `make gates` must pass on a fresh clone with no virtualenv and no network.
- **`Makefile`** — `help validate lint gates gates-ci ci-gates-parity hermetic`, all anchored on
  `$(CURDIR)`. `lint` runs shellcheck over `desktop/scripts/**` (a vacuous pass that says so out
  loud while the directory is empty) and `compileall` over `scripts/` with bytecode written outside
  the tree. `hermetic` re-runs the checks with `env -i`, empty `HOME`/`XDG_*` and a foreign cwd.
- **`.github/workflows/gates.yml`** — one job per `make gates` target plus `ci-gates-parity`, which
  compares the workflow's job keys against the Makefile's `GATES` in both directions so the two
  lists cannot drift.
- **mu-strict harness, byte-identical to `mu`**: `scripts/worktree-guard.sh`, `skills-lock.json`,
  `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/LIFECYCLE.md`, `tickets/_template/`,
  `tickets/_fixtures/`. `AGENTS.md` carries mu's evidence rule, routing, worktree and
  planning-vs-code rules verbatim, with only the charter (§2) and the repo-specific gates (§4)
  retargeted; `CLAUDE.md` is a symlink to it.
- **`openspec/`** — the `assets-catalog` capability spec plus the `repo-birth` change that produced
  this release, and `tickets/REQ-001` recording the birth.

### Not here, on purpose

No `src/`, no importable package, no `[project.scripts]`, no engine, no build, install or sync
verb. `pyproject.toml` is dev-only tooling (`package = false`, no build system) for the class
validators that arrive with their corpora.
