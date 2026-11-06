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

- [x] Every manifest carries `shape.hairline-w` (`glass 1`, `flat 0`,
      `paper 1`) and the local schema + token groups declare it.
- [x] The template emits no `{{SKIN_PANEL_WIDTH}}`, `{{SKIN_BT_LIST_SPACING}}`,
      `{{SKIN_BAR_ROW_HEIGHT}}` or `{{SKIN_CHIP_MIN}}`, and the expansion
      contains no layout-driven declaration.
- [x] The expanded glass parses: panel `1.5px`, all card/control/badge/footer
      hairlines `1px`, `.settings-net` `border: none` with no
      `margin-bottom`/`min-height`.
- [x] `skins/contracts/` is byte-identical to `contracts` `v0.6.0` (token,
      manifest, skin-json) and the PIN records `contracts=v0.6.0`, the source
      commit and matching sha256; `skins/schema.json` names `v0.6.0`.
- [x] The expanded glass document validates against the vendored
      `skin-json.schema.json`; the token count grows from 23 to 24.
- [x] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python`
      and `make validate` pass; the ticket branch is fast-forward merged to
      `master` and `v0.10.0` is an annotated tag on the merged commit. Existing
      tags are not moved.

## Evidence / Verify

- Evidence: `skins/templates/ags.gtk.css.j2` currently uses the four layout
  placeholders; `ags-bar/style.css:378-387` has `min-height: 0` and no margin;
  the source hairline widths are `1px` at `:183`, `:442`, `:428`, `:433`,
  `:761` and `1.5px` at `:163`; `skins/contracts/PIN` pinned `contracts=v0.5.2`
  before this slice.
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
- **The contract amendment landed in parallel.** `contracts` REQ-014 produced
  the `v0.6.0` schemas (annotated tag object `c312e46`, commit `e512f5c`). The
  three vendored files in this tree were taken with `git show v0.6.0:<path>`
  and compared with `cmp`; the PIN names the same tag and commit.

## Outcome (2026-11-05)

**Worktree:** `.worktrees/req-013/`
**Branch:** `ticket/req-013-skins-hairline-layout`
**Commits:** `ca50b40` (ticket + INDEX plan), `1247ee5` (token, template,
vendored schemas, tests, docs/version updates).
**Merge:** fast-forward into `master` (`ca50b40..1247ee5`); the ticket branch is
not left unmerged.
**Tag:** `v0.10.0` (annotated object `50fe7c4`, commit `1247ee5`), created on the
merged commit before this close-out commit.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/manifests/{glass,flat,paper}.toml` | `shape.hairline-w` added: `1` / `0` / `1` |
| `skins/templates/ags.gtk.css.j2` | `border-w` only on `.settings-surface`; `hairline-w` on card/tile/mini/password/rowact/badge/footer; `.settings-net` keeps `border: none` and loses `margin-bottom`/`min-height`; all four layout placeholders removed |
| `skins/schema.json` | 24-token groups + `hairline-w` property; `canonical.tag: v0.6.0`; ownership/layout note |
| `skins/contracts/*.schema.json` | byte copies from `contracts` `v0.6.0` (`e512f5c`) |
| `skins/contracts/PIN` | `contracts=v0.6.0`, source commit `e512f5c…`, new sha256 per file |
| `skins/tests/test_skins.py` | 24-token stats/types, `hairline-w` frozen values, no-layout-placeholder test, resolved-glass schema check |
| `skins/tests/test_parity.py`, `fixtures/parity/deviations.json` | `1.5px` panel / `1px` hairlines, `.settings-net` `border: none` with no margin/height, empty deviation record |
| `README.md`, `skins/README.md`, `CHANGELOG.md`, `catalog.yaml`, `tickets/INDEX.md` | token split, TSX-owned layout, `v0.6.0` pin and `v0.10.0` inventory |

### Evidence — commands and exact results

| Command | Result |
| --- | --- |
| `make validate-skins` | **PASS** — `manifests=3 templates=1 targets=ags tokens=24 roles=51` |
| `make test-skins PYTHON=$PWD/.venv/bin/python` | **PASS** — `41 passed` |
| `make validate` | **PASS** — 6 classes, 27 directories, 396 files scanned, tag `v0.10.0` |
| `PATH=/tmp/opencode/shellcheck/shellcheck-v0.10.0:$PATH make gates` | **exit 0** — all 9 gates incl. shellcheck and hermetic PASS |
| `git -C ../contracts show v0.6.0:schemas/<name>.schema.json \| cmp - skins/contracts/<name>.schema.json` | byte-identical for token, manifest and skin-json |
| template expansion scan | no `SKIN_PANEL_WIDTH` / `SKIN_BT_LIST_SPACING` / `SKIN_BAR_ROW_HEIGHT` / `SKIN_CHIP_MIN`; panel `border: 1.5px solid @primary`, card/control/badge/footer `1px` |

### New PIN (verbatim)

```text
contracts=v0.6.0
source-commit=e512f5c3dc6bec6023dc9ca1552213220001b07d
sha256  6383165244ecb85c91f51bad7194d68a27881f85cada9a41c97585310a2947b5  skin-token.schema.json
sha256  82d1229cf78cd4cfec54a25677838a912de1d1ecf81d454c9318ed3af2fa64c8  skin-manifest.schema.json
sha256  fbe980af1f5b4bea961d1addc512e32039dd2d3ae25464d6d528c2445ac04ad4  skin-json.schema.json
```
