---
id: req-013
title: "Skins hairlines and layout ownership: hairline-w token, no layout placeholders in CSS"
kind: requirement
status: in-progress
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-013/
branch: ticket/req-013-skins-hairline-layout
---

# Skins hairlines and layout ownership: `hairline-w`, no layout placeholders in CSS

## Why

Rendering the real template and manifests against GTK exposed three defects that
`v0.9.1` still ships:

1. **Layout is double-owned.** The template expands `panel-width` into
   `min-width` (`.settings-surface`), `bt-list-spacing` into `margin-bottom`
   (`.settings-net`), and `bar-row-height`/`chip-min` into
   `min-height`/`min-width` (`.settings-net`, `.settings-rowact`). Those
   metrics are widget-owned in TSX — panel width is set by `SettingsPanel.tsx`
   and list spacing by `BluetoothContent.tsx` — so the template adds geometry
   on top of the widget and breaks parity. Measured `.settings-net` row
   allocation was 54px against the source's 50px; the extra 4px is the
   template's `margin-bottom: 4px`, which the source does not declare.
2. **One `border-w` cannot split panel from hairlines.** The source panel is
   `1.5px` (`ags-bar/style.css:163`) while cards (`:183`), row actions
   (`:442`), badges (`:428`/`:433`), the password field (`:559`) and the Wi-Fi
   settings top rule (`:761`) are `1px`. Keeping the panel at `1.5px` forces
   every hairline to `1.5px`.
3. **The missing distinction is a real token, not a literal.** The contract is
   being amended at `v0.6.0`: a new numeric `hairline-w` shape token, and the
   four layout tokens are declared TSX-owned so templates MUST NOT emit them.
   Until the template stops consuming layout tokens, a skin change can move
   widget geometry the app already sets.

Evidence: `skins/templates/ags.gtk.css.j2:63` (`min-width` from
`panel-width`), `:150` (`min-height` from `bar-row-height`), `:152`
(`margin-bottom` from `bt-list-spacing`), `:212-213` (`chip-min` /
`bar-row-height` on `.settings-rowact`); `ags-bar/style.css:378-387` (source
row has `min-height: 0`, no margin, `border: none`), `:161-166` (panel
`1.5px`), `:183`, `:442`, `:428`, `:433`, `:761` (source `1px` hairlines).

## Requirement

1. Add the numeric `hairline-w` token to `[shape]` in every manifest:
   `glass = 1`, `flat = 0`, `paper = 1` (unitless numbers, like `border-w`).
2. `skins/templates/ags.gtk.css.j2`:
   - `.settings-surface` keeps `border: {{SKIN_BORDER_W}} solid
     {{SKIN_BORDER}}` (glass `1.5px`) and drops `min-width`;
   - `.settings-card`, `.settings-tile`, `.settings-mini`,
     `.settings-password`: `border: {{SKIN_HAIRLINE_W}} solid
     alpha({{SKIN_INK}}, 0.10)`;
   - `.settings-rowact`: `border: {{SKIN_HAIRLINE_W}} solid
     alpha({{SKIN_INK}}, 0.26)`;
   - `.settings-badge`: `border: {{SKIN_HAIRLINE_W}} solid
     alpha({{SKIN_INK}}, 0.14)`; `.settings-badge.conn`:
     `alpha({{SKIN_ACCENT}}, 0.45)`;
   - `.settings-wifi-settings-row` top rule: `{{SKIN_HAIRLINE_W}}`;
   - `.settings-net`: `border: none`, no `margin-bottom`, no `min-height`
     from `bar-row-height`; keep padding/radius/background;
   - remove every layout-token placeholder: `{{SKIN_PANEL_WIDTH}}`,
     `{{SKIN_BT_LIST_SPACING}}`, `{{SKIN_BAR_ROW_HEIGHT}}`,
     `{{SKIN_CHIP_MIN}}`. Non-layout literals (signal `30px`, etc.) keep the
     source value. The layout tokens remain in the manifests/`skin.json` for
     `skinValue()` consumers.
3. Re-vendor `skins/contracts/{skin-token,skin-manifest,skin-json}.schema.json`
   byte-for-byte from `contracts` `v0.6.0`; update `skins/contracts/PIN`
   (`contracts=v0.6.0`, source commit, sha256 per file) and
   `skins/schema.json`'s `canonical.tag`. Validate the expanded glass document
   against the vendored schemas.
4. Parity tests prove: no layout placeholders are emitted by expanding glass;
   `.settings-net` has `border: none` and no `margin-bottom`; row
   height-driving declarations match the source (no border); hairlines are
   `1px` for cards/controls/badges and `1.5px` for the panel; no literal hex
   and no transition.
5. README, `skins/README.md`, CHANGELOG, `catalog.yaml`, this ticket and
   `tickets/INDEX.md` record the token and the layout ownership rule; tag the
   next minor `v0.10.0`; fast-forward merge to `master`, never work on `main`.

## Acceptance

- [ ] Every manifest carries `shape.hairline-w` (`glass 1`, `flat 0`,
      `paper 1`) and the local schema + token groups declare it.
- [ ] The template emits no `{{SKIN_PANEL_WIDTH}}`, `{{SKIN_BT_LIST_SPACING}}`,
      `{{SKIN_BAR_ROW_HEIGHT}}` or `{{SKIN_CHIP_MIN}}`, and the expansion
      contains no layout-driven declaration.
- [ ] The expanded glass parses: panel `1.5px`, all card/control/badge/footer
      hairlines `1px`, `.settings-net` `border: none` with no
      `margin-bottom`/`min-height`.
- [ ] `skins/contracts/` is byte-identical to `contracts` `v0.6.0` (token,
      manifest, skin-json) and the PIN records `contracts=v0.6.0`, the source
      commit and matching sha256; `skins/schema.json` names `v0.6.0`.
- [ ] The expanded glass document validates against the vendored
      `skin-json.schema.json`; the token count grows from 23 to 24.
- [ ] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python`
      and `make validate` pass; the ticket branch is fast-forward merged to
      `master` and `v0.10.0` is an annotated tag on the merged commit. Existing
      tags are not moved.

## Evidence / Verify

- Evidence: `skins/templates/ags.gtk.css.j2` currently uses the four layout
  placeholders; `ags-bar/style.css:378-387` has `min-height: 0` and no margin;
  the source hairline widths are `1px` at `:183`, `:442`, `:428`, `:433`,
  `:761` and `1.5px` at `:163`; `skins/contracts/PIN` currently pins
  `contracts=v0.5.2`.
- Verify: `rg 'SKIN_(PANEL_WIDTH|BT_LIST_SPACING|BAR_ROW_HEIGHT|CHIP_MIN)'
  skins/templates` → no matches; `make validate-skins` → PASS;
  `make test-skins PYTHON=$PWD/.venv/bin/python` → PASS; `make validate` →
  PASS; `git cat-file -t v0.10.0` → `tag`; `git merge-base --is-ancestor
  ticket/req-013-skins-hairline-layout master` → exit 0.

## Discrepancy / judgment log

- **MINOR, not MAJOR.** A new token is additive vocabulary; no class path
  moves and the local `schema_major` stays `1`. Consumers that ignore
  `hairline-w` keep working with `border-w`; the runtime/manifest readers
  accept the extra shape key only after the vendored schema is updated.
- **Layout tokens are not deleted from the data plane.** `panel-width`,
  `bt-list-spacing`, `bar-row-height` and `chip-min` remain in the manifests
  and resolved `skin.json` because `skinValue()` consumes them. Only the
  template loses them: geometry is TSX-owned.
- **The row-parity number is structural.** The 54px vs 50px measurement came
  from rendering the expanded template; the committed test asserts the cause
  (no `margin-bottom`, no `min-height`, `border: none`) rather than a GTK
  pixel read, so it runs on a fresh clone.
- **Hairline 0 for `flat`.** `flat` is zero chrome; `hairline-w = 0` keeps
  every control border at `0px` even though the template still emits a border
  declaration. `glass` and `paper` are `1`.
