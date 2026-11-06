---
id: req-018
title: "Skins terminal: fourth v2 built-in (dense monospace, square/hairline)"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-018/
branch: ticket/req-018-terminal-skin
---

# Skins terminal: fourth v2 built-in (dense monospace, square/hairline)

## Why

The v2 Appearance plane ships three manifests (`glass`, `flat`, `paper`). The
approved mock for the fourth built-in is **`terminal`**: a dense monospace,
square/hairline skin — opaque `@surface` panel, `@surface_container` cards,
zero radii, 1px hairlines, tight padding, JetBrainsMono Nerd Font at weight
500 and a compact 9–14px type scale. Consumers need it as data, not as a
one-off theme in an app repository.

The same slice retires the two **cleanup-candidate layout tokens** recorded by
`req-017`: `layout.ags-capture.panel-width` and
`layout.ags-btop-studio.left-width` / `right-width` came from CSS `min-width`
values, not real TSX defaults. The apps are being corrected to their pre-v2
natural layout in parallel, so the skin class must stop declaring them rather
than keep a CSS minimum as permanent skin semantics.

Evidence: `skins/manifests/{glass,flat,paper}.toml` carry those two blocks
today; `tickets/req-017-layout-defaults/ticket.md` §"Cleanup handoff" records
them as cleanup candidates; `skins/schema.json` `frozen.required_files` names
three manifests.

## Requirement

1. Add `skins/manifests/terminal.toml` (`schemaVersion = 2`) using **only**
   palette role expressions (no literal hex), faithful to the approved
   dense-monospace, square/hairline mock:
   - `surface.panel`: bg `@surface` (opaque), border `alpha(@on_surface, 0.22)`,
     border-width `1`, radius `0`, padding `9`, shadow `none`, blur `none`;
   - `surface.card`: bg `@surface_container`, border `alpha(@on_surface, 0.18)`,
     border-width `1`, radius `0`, padding `8`;
   - `surface.cell`: bg transparent, border transparent, border-width `0`,
     radius `0`, padding `5`, hover-bg `alpha(@on_surface, 0.10)`;
   - `surface.control`: bg transparent, border `alpha(@on_surface, 0.30)`,
     border-width `1`, radius `2`, padding `3`, font-size `10`, font-weight `600`;
   - `surface.pill`: bg `alpha(@on_surface, 0.12)`,
     border `alpha(@on_surface, 0.18)`, border-width `1`, radius `2`,
     padding `1`, font-size `9`, letter-spacing `0.04`;
   - `state`: hover fill `alpha(@on_surface, 0.10)`; selected fill
     `@primary_container`, ink `@on_primary_container`, ring `@primary`; focus
     ring `@primary`; disabled fill `alpha(@on_surface, 0.06)`; every state role
     carries the schema's `fill`/`ink`/`ring` shape;
   - `type`: font-family `"JetBrainsMono Nerd Font, monospace"`, font-weight
     `500`, letter-spacing `0`, sizes caption `9` / meta `10` / body `12` /
     title `13` / display `14`;
   - `ink`: ink `@on_surface`, ink-dim `alpha(@on_surface, 0.62)`, accent
     `@primary`, accent-muted `alpha(@primary, 0.5)`, ink-over `auto`;
   - `layout`: the remaining `glass` layout groups with the same values (bar
     `312`/`4`; clipboard `260`; notifications `380`; wallpaper `960 × 640`;
     icme `1280 × 800`). No `mode` overrides: `terminal` is mode-agnostic and
     the base groups serve both modes.
2. Keep `glass`, `flat` and `paper` values otherwise untouched, and remove the
   cleanup-candidate blocks `[groups.layout.ags-capture]` (`panel-width`) and
   `[groups.layout.ags-btop-studio]` (`left-width` / `right-width`) from **all
   four** manifests. Record the app-side handoff in this ticket.
3. Extend the validator and tests: `terminal` must appear in
   `frozen.required_files`, expand for every template × both modes, resolve to
   `tokens.json` accepted by the vendored `appearance-json` schema, and use only
   palette.v1 roles (no aliases, no literal hex, no transitions). Add a
   positive fixture proving the validator accepts the terminal shape.
4. Update `skins/README.md`, `README.md`, `CHANGELOG.md`, `catalog.yaml`, this
   ticket and `tickets/INDEX.md`.
5. Tag `v0.13.0`; fast-forward merge to `master`; push `master` + the tag.

## Acceptance

- [ ] `skins/manifests/terminal.toml` is `schemaVersion = 2`, uses only
      palette role expressions and matches every value above; it has no `mode`
      block.
- [ ] `glass`, `flat` and `paper` otherwise keep their values; the
      `ags-capture` and `ags-btop-studio` layout blocks are gone from all four
      manifests.
- [ ] `skins/schema.json` requires `terminal`; `make validate-skins` expands
      all 7 templates × 4 manifests × 2 modes and validates every resolved
      token document against `appearance-json`.
- [ ] `make test-skins` covers terminal's frozen values, both-mode expansion,
      no-hex/no-transition/role vocabulary, the removed layout tokens and a
      positive terminal fixture.
- [ ] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python` and
      `make validate` pass.
- [ ] `v0.13.0` is an annotated tag on the fast-forward-merged commit; `master`
      and the tag are pushed.

## Evidence / Verify

- Evidence: the three existing manifests are the v2 shape; `skins/schema.json`
  `frozen.required_files` is the validator's manifest allow-list; the vendored
  `appearance-manifest` schema validates `layout.<app>` values as numbers and
  the vendored `appearance-json` schema validates the resolved document.
- Verify: `make validate-skins`, `make test-skins
  PYTHON=$PWD/.venv/bin/python`, `make validate`; `git cat-file -t v0.13.0`;
  `git merge-base --is-ancestor ticket/req-018-terminal-skin master`.

## Cleanup handoff

- **`layout.ags-capture.panel-width = 560`** and
  **`layout.ags-btop-studio.left-width` / `right-width = 280` / `320`** are
  removed from every manifest in this slice. `req-017` recorded them as CSS
  minima, not TSX defaults. The app repositories are being corrected to their
  pre-v2 natural layout in parallel; until those app commits land, a consumer
  that still reads the tokens falls back to the app's own default. The skin
  class no longer declares CSS geometry as skin semantics.
- **`layout.ags-clipboard.card-width = 260`** and
  **`layout.ags-notifications.card-width = 380`** stay: both are real pre-v2 TSX
  literals. **`layout.ags.panel-width = 312`** and
  **`layout.ags.bt-list-spacing = 4`/`6`** stay for the same reason.
