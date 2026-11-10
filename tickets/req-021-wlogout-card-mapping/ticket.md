---
id: req-021
title: "wlogout Phase 2b: card fill and panel-aligned button geometry"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-021/
branch: ticket/req-021-wlogout-card-mapping
---

# wlogout Phase 2b: card fill and panel-aligned button geometry

## Why

wlogout's buttons are wide action cards, not compact controls. `v0.14.0`
mapped them to `surface.control`, which is intentionally transparent for the
`terminal` skin, so the buttons stayed invisible behind the wallpaper. Phase 2b
makes the cards visibly filled and ties their outer geometry to the same
`surface.panel` radius/border-width the compositor/panel uses, without adding
runtime, provisioning, composition or app changes.

Acceptance criteria: `W-2.11`–`W-2.16` in
`dotfiles-v3/docs/108-non-ags-skin-consumers.md`. The static wlogout sheet
remains structure-only from `v0.15.1`; only the generated paint template and
its tests/docs move in this slice.

## Requirement

1. `skins/templates/wlogout.gtk.css.j2`:
   - `button` background, border colour and padding from `surface.card.*`
     (filled action cards);
   - `button` border-width and border-radius from `surface.panel.*` so the
     card geometry follows the delegated host/panel values;
   - `button:hover` / `:focus` / `:active` keep the matching `state.*` paint;
   - `button span` keeps the `type.*` typography;
   - no literal hex, transition, animation, structure/layout IDs, icons,
     wallpaper or grid.
2. `templates/wlogout/style.css.tpl` stays byte-identical to `v0.15.1`
   (structure-only: palette import, wallpaper, icons, sizing/motion, generated
   import last). No new paint or rhythm.
3. Tests:
   - template expands with the card fill and panel border/radius placeholders;
   - `terminal` button background is `@surface_container`, border/radius are
     the panel values;
   - `glass`/`paper`/`flat` expansions use their respective card fill and panel
     radius;
   - GTK3 static + combined parse and Broadway wlogout smoke emit no CSS
     warnings;
   - the static forbidden-declaration grep remains zero.
4. Update `skins/README.md`, root `README.md`, `catalog.yaml`,
   `CHANGELOG.md`, `skins/schema.json` status/notes, version references and
   the ticket/INDEX. Run `make validate-skins`, `make test-skins`, `make lint`
   and `make gates-ci` in the foreground.
5. Release `v0.15.2` as an annotated tag on the green closing commit,
   fast-forward to `master`, push `master` and the tag.

## Acceptance

- [ ] The generated `button` base uses `surface.card` fill/border/padding and
      `surface.panel` border-width/radius; states and span type are unchanged.
- [ ] The static wlogout sheet is unchanged from `v0.15.1` and still has zero
      forbidden paint/rhythm declarations.
- [ ] Expansion tests prove the card fill + panel geometry for all four skins;
      terminal is `@surface_container` with panel 1px/0px.
- [ ] GTK3 `CssProvider` parses static and combined sheets; Broadway wlogout
      stays alive with no CSS warnings.
- [ ] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [ ] `v0.15.2` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `W-2.11`–`W-2.16` in
  `dotfiles-v3/docs/108-non-ags-skin-consumers.md`; the `surface.card` and
  `surface.panel` values in `skins/manifests/*.toml`.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; GTK3 `CssProvider` probes and the Broadway smoke recorded in
  the outcome.

## Outcome (2026-11-10)

Pending implementation.
