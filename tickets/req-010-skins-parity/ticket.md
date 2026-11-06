---
id: req-010
title: "Skins fidelity: glass expands to today's ags-bar settings/Bluetooth declarations"
kind: requirement
status: in-progress
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-010/
branch: ticket/req-010-skins-parity
---

# Skins fidelity: glass expands to today's ags-bar settings/Bluetooth declarations

## Why

`v0.7.0` shipped the `skins/` class, but its `glass` manifest and GTK template are
a design-system re-expression, not a faithful extraction of today's
`../ags-bar/style.css`. The class therefore cannot keep the promise that
"glass = today's look": several declarations in the rendered template differ from
the source stylesheet without being documented as intentional.

Evidence (read-only input `../ags-bar/style.css`; line numbers from the current
tree):

| Selector | Today (`style.css`) | `v0.7.0` glass manifest/template |
| --- | --- | --- |
| `.settings-surface` | `alpha(@surface, 0.94)`, `1.5px solid @primary`, `12px`, `11px` (`:161-166`) | `alpha(@surface, 0.94)` but radius `16px`, border `alpha(@primary, 0.35)`, padding via `gap` (`12px`) |
| `.settings-card` | `alpha(@surface_container_high, 0.18)`, `1px solid alpha(@on_surface, 0.10)`, `9px`, `10px 11px` (`:181-186`) | card bg `0.88`, radius `12px`, panel border token |
| `.settings-net` | `padding: 8px 9px`, transparent bg, `border: none`, `7px` (`:378-387`) | `cell-pad = 9px 12px`, radius `8px`, border token |
| `.settings-badge` | `9.5px`, `2px 6px`, radius `20px` (`:422-429`) | pill radius `999px`, text size `13px`, gap padding |
| `.settings-rowact` | `1px solid alpha(@on_surface, 0.26)`, `7px`, `4px 8px`, `11px/600` (`:437-448`) | token border/radius/padding/font from panel-scale tokens |
| `.settings-surface` shadow | no `box-shadow` declaration (`:161-166`) | ships `0 16px 40px rgba(0,0,0,0.5)` |
| small type | net-sub `10.5px` (`:413-416`), section-label `11px/600` (`:732-739`), empty `12px` + `18px 10px` (`:637-641`), card-title `12.5px/650` (`:188-191`), tile-sub `11px` (`:206-209`) | all routed through `text-size = 13px` |
| layout | panel width `312` (`../ags-bar/settings-panel/SettingsPanel.tsx:22`), Bluetooth list spacing `4` (`../ags-bar/components/bluetooth/BluetoothContent.tsx:750` and `:798`) | `bt-list-spacing = 6px` |

## Fidelity policy for v1 (frozen 23-token contract unchanged, contracts v0.5.0)

- Templates use `{{SKIN_*}}` ONLY where the token is a genuine global knob:
  panel background/border/border-width/radius/shadow/blur; card background/radius;
  cell radius/padding/hover; control radius; pill radius; ink/ink-dim/accent;
  title-size/text-size; layout metrics.
- Component-specific detail with no matching token stays a literal copied from
  today's `style.css` (palette-role expressions only, no hex): panel padding
  `11px`; card border `{{SKIN_BORDER_W}} solid alpha({{SKIN_INK}}, 0.10)`; card
  padding `10px 11px`; tile padding `8px 11px 8px 10px`; rows transparent with
  `border: none`; rowact border `{{SKIN_BORDER_W}} solid
  alpha({{SKIN_INK}}, 0.26)`, padding `4px 8px`, font `11px/600`; badge
  `9.5px`/`letter-spacing: 0.05em`/`2px 6px`; small text literals (net-sub
  `10.5px`, section-label `11px`, empty `12px`, badge `9.5px`); scrollbar
  `5px`; slider radius `99px`.
- No `font-size` on the window root (today inherits); apply
  `font-family: {{SKIN_FONT_FAMILY}}` only.
- `title-size` applies to names/card titles (`12.5px`); `text-size` applies to
  the `13px` body contexts. Neither is used for the small literals above.
- No transitions (GTK 4.24 ignores them), no literal hex, no structure/variant
  keys.

## Acceptance

- [ ] `skins/manifests/glass.toml` carries the corrected parity values
      (`radius-panel/card/cell/pill = 12/9/7/20px`, `border-w 1.5px`, `gap 8px`,
      `cell-pad 8px 9px`, panel/card/border/shadow/blur/ink values as specified,
      `title-size 12.5px`, `text-size 13px`, `bt-list-spacing 4px`,
      `bar-row-height 0px`, `chip-min 0px`); `flat`/`paper` stay valid and remain
      transparent/borderless or role-based where their own tokens say so.
- [ ] `skins/templates/ags-bar.gtk.css.j2` is a literal extraction of today's
      settings/Bluetooth declarations, uses tokens only for genuine knobs, and
      documents the fidelity policy plus every remaining deviation in its header.
- [ ] `skins/tests/test_parity.py` expands glass through the validator's own
      placeholder map and asserts the expected declaration strings (with source
      line references), no non-`none` shadow, no transition and no hex; a fixture
      encodes the card-border deviation.
- [ ] `skins/README.md` lists the component details that are not skin-controlled
      in v1, with the reason, and the CHANGELOG records the correction.
- [ ] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python` and
      `make validate` pass; the ticket branch is fast-forward merged to `master`
      (no unmerged ticket branch) and `v0.8.0` is an annotated tag on the merged
      commit. Existing tags are not moved.

## Evidence / Verify

- Evidence: source declarations and line numbers in `../ags-bar/style.css`
  (`:161-166`, `:181-191`, `:194-209`, `:378-448`, `:637-641`, `:732-739`),
  panel width `../ags-bar/settings-panel/SettingsPanel.tsx:22`, list spacing
  `../ags-bar/components/bluetooth/BluetoothContent.tsx:750` and `:798`.
- Verify: `make validate-skins` → PASS; `make test-skins
  PYTHON=$PWD/.venv/bin/python` → PASS; `make validate` → PASS;
  `git cat-file -t v0.8.0` → `tag`; `git merge-base --is-ancestor
  ticket/req-010-skins-parity master` → exit 0.

## Discrepancy / judgment log

- **One `border-w` cannot split panel from hairline.** Today the panel is
  `1.5px` (`:163`) while cards (`:183`), row actions (`:442`), badges
  (`:428`) and the Wi-Fi settings top rule (`:761`) are `1px`. The frozen v1
  contract has one `border-w`; glass keeps the panel's `1.5px`, so those
  hairlines render `0.5px` thicker (`1.5px` vs `1px`). This is the only visual
  deviation in the tokenized declarations; the alternative (a second
  border-width token) would break the frozen 23-token contract.
- **Local `ink` grammar follows the canonical contract.** `contracts` `v0.5.0`
  defines `inkValue` as a palette role *or* a role expression. The local
  `skins/schema.json` now points `ink`, `ink-dim` and `accent` at its existing
  `roleExpression` definition, so glass can carry
  `ink-dim = alpha(@on_surface, 0.62)` (today's `style.css:415`) without
  changing the 23 token names, groups or manifest shape. This is a value-grammar
  alignment, not a new token.
- **`gap` is not consumed by the GTK template.** Today every gap-looking
  declaration is a component padding (`11px`, `10px 11px`, etc.) or the
  widget-level Bluetooth list spacing (`4`). Those stay literal/`bt-list-spacing`
  rather than being rewritten to `gap = 8px`, so `gap` remains manifest
  metadata for v1.
- **Template-only declarations with no visual change:** `min-width: 312px` on
  `.settings-surface` (today the width is set by `SettingsPanel.tsx:22`),
  `margin-bottom: 4px` on `.settings-net` (today the box spacing is `4` in
  `BluetoothContent.tsx`), `min-height/min-width: 0px` from the layout tokens
  where today has `min-height: 0` or no declaration, `box-shadow: none` and
  `backdrop-filter: none` from the `shadow`/`blur` tokens where today has no
  declaration, and `font-family: inherit` (glass) on the window root where today
  inherits without a declaration.
