---
id: req-022
title: "wlogout Phase 2c: card state fill correctness"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-022/
branch: ticket/req-022-wlogout-card-state
---

# wlogout Phase 2c: card state fill correctness

## Why

`v0.15.2` made wlogout's buttons filled action cards, but their `:hover` and
`:focus` rules still replaced the card background with `state.hover.fill` /
`state.focus.fill`. Those are compact-control state paints; `terminal`, `glass`
and `paper` declare the focus fill as `transparent`, so a focused card lost its
surface and the wallpaper showed through. Phase 2c keeps the card background for
base/hover/focus, moves only the ring and ink on interaction, and reserves the
selected fill for the deliberate `:active` press.

Acceptance criteria: `W-2.17`–`W-2.19` in
`dotfiles-v3/docs/108-non-ags-skin-consumers.md`. The static wlogout sheet
remains structure-only from `v0.15.1`; only the generated paint template and
its tests/docs move in this slice.

## Requirement

1. `skins/templates/wlogout.gtk.css.j2`:
   - `button` keeps the `v0.15.2` card base: `surface.card` background,
     border colour and padding; `surface.panel` border-width and radius;
   - `button:hover` and `button:focus` keep the **card background** and use
     `state.hover.ring`/`state.hover.ink` and `state.focus.ring`/`state.focus.ink`
     for border and colour; they must not read `state.hover.fill` or
     `state.focus.fill` as a background;
   - `button:active` uses `state.selected.fill`/ink/ring as the deliberate
     selected paint;
   - `button span` keeps the `type.*` typography;
   - no literal hex, transition, animation, structure/layout IDs, icons,
     wallpaper or grid.
2. `templates/wlogout/style.css.tpl` stays structure-only with no new paint
   (palette import, wallpaper, icons, sizing/motion, generated import last).
3. Tests:
   - expanded `terminal`/`glass`/`paper`/`flat`: focused and hovered cards
     retain the card background and change ring/ink;
   - active uses the selected fill/ink/ring;
   - GTK3 static + combined parse; Broadway wlogout smoke; static
     forbidden-declaration grep stays zero;
   - a focused-card visual/provider probe proves the background remains the
     card value;
   - the pinned positive fixture stays byte-equal to the shipped template.
4. Update `skins/README.md`, root `README.md`, `catalog.yaml`, `CHANGELOG.md`,
   `skins/schema.json` status/notes, version references and the ticket/INDEX.
   Run `make validate-skins`, `make test-skins`, `make lint` and
   `make gates-ci` in the foreground.
5. Release `v0.15.3` as an annotated tag on the green closing commit,
   fast-forward to `master`, push `master` and the tag.

## Acceptance

- [ ] Base/hover/focus `button` rules keep the card background; hover/focus
      change only ring and ink, with no hover/focus fill as background.
- [ ] `button:active` uses `state.selected.fill`/ink/ring.
- [ ] Expansion tests prove card-background retention and ring/ink changes for
      all four skins; a focused-card provider probe proves the card value.
- [ ] GTK3 `CssProvider` parses static and combined sheets; Broadway wlogout
      stays alive with no CSS warnings.
- [ ] Static wlogout sheet remains structure-only with zero forbidden paint and
      is unchanged from `v0.15.2`.
- [ ] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [ ] `v0.15.3` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `W-2.17`–`W-2.19` in
  `dotfiles-v3/docs/108-non-ags-skin-consumers.md`; card/state values in
  `skins/manifests/*.toml`; the focused-card probe recorded in the outcome.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; GTK3 `CssProvider` probes and the Broadway smoke recorded in
  the outcome.
