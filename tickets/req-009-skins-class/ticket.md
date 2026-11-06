---
id: req-009
title: "Skins class: frozen v1 manifests, GTK template, local validation target"
kind: requirement
status: in-progress
lane: 2 — openspec-single
links:
  openspec: skins-class
  bmad: none
worktree: .worktrees/req-009/
branch: ticket/req-009-skins-class
---

# Skins class: frozen v1 manifests, GTK template, local validation target

## Requirement

Add a sixth, data-only class `skins/` carrying the frozen skin spec v1: a
palette-role expression vocabulary (no structure/variant tokens), three shipped
manifests (`glass`, `flat`, `paper`), and one GTK stylesheet template that
expands those tokens for the Bluetooth panel and settings surfaces. The
canonical schema lives in the `contracts` repository; this repository keeps the
data-only validation target and fixture-based tests, never a runtime import of
another repository.

The frozen values are: glass is the default/fallback parity skin (today's
ags-bar look), flat is the zero-chrome skin, and paper is the light/palette
axis expressed only through `palette.v1` roles. Transitions are forbidden
because GTK 4.24 ignores them; surface, border and shadow values are
palette-role expressions, never literal hex.

## Acceptance

- [ ] `skins/schema.json` states the canonical contract location in
      `contracts` (`schemas/skin-token.schema.json`,
      `schemas/skin-manifest.schema.json`) and is the local validation target;
      no cross-repo import at runtime.
- [ ] `skins/manifests/glass.toml`, `flat.toml`, `paper.toml` carry every
      required token and the frozen v1 values.
- [ ] `skins/templates/ags-bar.gtk.css.j2` contains only `{{SKIN_*}}`
      placeholders for skin constants, has no literal hex, no transitions and
      no structure/variant vocabulary; glass expansion is pixel-equivalent to
      the recorded ags-bar values.
- [ ] `make validate-skins` proves manifest/schema validation, placeholder
      coverage and the no-hex / no-transition / no-structure rules, and the
      pytest fixtures prove each negative case fails.
- [ ] `skins/README.md` documents the light-mode dependency for `paper`.
- [ ] `catalog.yaml`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, `tickets/INDEX.md`
      and the gate set (Makefile + workflow) agree on the new class.
- [ ] `make gates` green on the commit to be tagged; annotated next-minor tag.

## Evidence / Verify

- Evidence: current canonical settings/bluetooth look rules in
  `../ags-bar/style.css` (read-only input); frozen spec values in this ticket;
  palette role list in `icons/mappings/vocabulary.json` (51 roles).
- Verify: `make validate-skins` → PASS; `make test-skins` → PASS;
  `make gates` → exit 0; `git cat-file -t <tag>` → `tag`.

## Discrepancy / judgment log

- The `contracts` repository is reachable at `v0.4.0`, but it does **not** yet
  contain `schemas/skin-token.schema.json` or
  `schemas/skin-manifest.schema.json`. This ticket therefore records a pointer
  only; it does not claim a vendored copy or byte-equality. The local
  `skins/schema.json` is the validation target until the canonical pair lands.
- `style.css` currently paints cards at `alpha(@surface_container_high, 0.18)`
  with a solid `@primary` border, while the frozen spec freezes the glass
  manifest at `0.88` and `alpha(@primary, 0.35)`. The manifest is the frozen
  source of truth; the template expands the frozen token values and the
  discrepancy is recorded instead of silently redefining either side.
- `paper` uses `surface_container_lowest` (panel) and
  `surface_container_low` (card). In `palette.v1` these are the two light-pole
  container roles: the panel is the lightest sheet and the card is one step
  off it, so a light palette reads as paper without inverting the role family.
