---
id: req-028
title: "Skin the AGS sound panel from the v3 roles"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-028/
branch: ticket/req-028-sound-panel-skin
---

# Skin the AGS sound panel from the v3 roles

## Why

`ags-bar` REQ-005 shipped the anchored sound panel, tray dropdown, bar strip and
settings popover with the glass chrome baked into `audio/audio-panel.css`
(`alpha(@surface, .72)`, 18px, shadow, palette ink). No built-in skin could
paint it. Doc 113 W-10 makes the AGS overlay `surface.panel` (never
`surface.window`), and the v3 skin roles are the only paint/type authority.

## Requirement

1. Add the sound selectors to `skins/templates/ags.gtk.css.j2` using only v3
   placeholders: panel surface/border/border-width/radius/padding/shadow/blur
   for the popover, tray dropdown and settings popover; `surface.card` for the
   Playing page; `surface.cell` for Mixer/tray/menu/settings rows; `surface.control`
   for device/route/icon/transport/level controls; `surface.pill` for
   muted/live/switch/mode badges; `state.hover/selected/focus/disabled`;
   `ink`/`type` for text. No `surface.window` and no literal hex.
2. Reduce `ags-bar/audio/audio-panel.css` to structural/layout/content rules
   (dimensions, spacing, layout, content art, the semantic live green). Remove
   the glass paint/radius/shadow/panel literals; the runtime-selected skin
   paints the panel. The widths stay app-owned: panel 352, tray 300, settings
   280 (border-box), with skin padding inside.
3. Extend the fixture tests: the `ags` selector/token coverage includes the
   sound classes; every manifest × mode expands; the audio app stylesheet has
   no paint role/hex/radius/shadow/backdrop-filter.
4. Render the real panel, mixer, tray and settings under all five skins from
   the expanded appearance CSS (palette + skin) and record the sizes.
5. Gates: `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
   in `dotfiles-assets`; the bar's `make gates` after its app CSS change.
6. No manifest value changes and no composition tuple/pin changes. Tag proposal
   recorded in the report.

## Acceptance

- [x] `ags.gtk.css.j2` paints every sound class from v3 roles for all five
      skins and both modes; no `surface.window`, no literal colour.
- [x] The bar's `audio-panel.css` is structural only and still lays out the
      approved composition; the live green is the only literal colour.
- [x] Fixture coverage and negative checks pass; all five skin renders are
      attached with actual sizes.
- [x] `make validate-skins` and `make test-skins` pass; the bar gates stay
      green. `make lint`/`make gates-ci` stop at the environment's missing
      `shellcheck` (validate-desktop), an unrelated tool gap; every Python
      validator before it passed.

## Notes

- The paper mock is the glass *preview*; the shipped chrome is the selected
  skin's role values. The glass manifest's panel role is the parity skin
  (0.94 paint, 1.5px `@primary` frame, 12px, no shadow/blur), so the glass
  render follows those values. A numeric retune of the glass panel role would
  affect settings/Bluetooth/clipboard/wallpaper and is a separate skin-design
  decision, not part of this slice.

## Evidence

- Worktree `.worktrees/req-028/`, branch `ticket/req-028-sound-panel-skin`,
  based on `044dd0c` (v0.19.0).
- `skins/templates/ags.gtk.css.j2` gains the `/* ── Sound — REQ-005 */`
  section: panel paint/frame/radius/padding/shadow/blur for `.audio-surface`,
  `.tray-surface`, `.audio-settings` and `.audio-menu > contents`; card for
  `.audio-playing-page`; cell for `.audio-mixer-row`, `.audio-tray-player`,
  `.audio-menu-option`, `.audio-consumer`, `.audio-settings-row`; control for
  the device/route/icon/transport/level controls; pill for muted/live/switch;
  `state.*` for hover/selected/focus/disabled; ink/type for text. The section
  has no `SKIN_SURFACE_WINDOW` placeholder and no literal hex.
- `skins/tests/test_skins.py` extends the `ags` selector/token coverage with
  the sound classes and adds two positive tests: the panel role's paint and
  radius reach the sound surfaces in all five manifests, and no sound selector
  consumes `surface.window`. The existing terminal-host host-probe test now
  checks the panel radius on all four panel-role surfaces rather than counting
  one occurrence.
- `skins/README.md` and this ticket's CHANGELOG entry name the sound surface
  in the `ags` target.
- All-skins renders (the bar's real widgets over the live wallpaper, using
  each manifest's expanded skin plus the live palette) are recorded in the
  `ags-bar` REQ-005 evidence: `skin-<skin>-panel.png`, `-mixer.png`,
  `-tray.png`, `-strip.png`, `-settings.png` for glass, flat, paper, terminal
  and terminal-host under `/tmp/opencode/req005/`.

### Glass caveat

The mock in the bar's REQ-005 paper is the glass *preview* (18px, 1px
hairline, 0.70 paint, soft shadow). The shipped `glass` manifest's panel role
is the parity skin: `alpha(@surface, 0.94)`, 1.5px `@primary` frame, 12px,
`shadow = none`, `blur = none`. The glass render therefore follows the glass
role, not the mock's numbers. A glass panel-role retune would also change the
settings panel, Bluetooth, clipboard and wallpaper-selector paints and breaks
the `test_parity.py` glass-parity contract; it is a separate skin-design
decision, not part of this slice. The other four skins visibly adapt.

## Gates

Run in this worktree:

```text
make validate-skins   -> PASS (all five manifests x both modes x 12 templates)
make test-skins       -> 181 passed, 3 skipped (venv python)
make lint             -> FAIL: shellcheck is not installed (environment gap)
make gates-ci         -> FAIL at validate-desktop: shellcheck is not installed;
                         validate, validate-icons, validate-content,
                         validate-templates, validate-configs and
                         validate-desktop's Python parse all passed first
```

## Tag proposal

- `dotfiles-assets` **v0.20.0** (minor: new sound paint on the `ags` target; no schema or
  manifest value change).
- `ags-bar` **v0.6.3** (sound panel shipped skin-agnostic).
- The composition program tuple is **not** touched: it remains
  `ags-platform v1.0.1 / contracts v0.11.0 / dotfiles-assets v0.18.1`. A
  program-wide cutover must move the tuple to the new assets tag (and the bar
  tag) after both releases; it is not a single-app pin bump.
