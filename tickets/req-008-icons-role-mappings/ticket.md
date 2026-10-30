---
id: req-008
title: "Icons manifest: semantic role re-pin, real defaults, surface classes, vocabulary lint"
kind: requirement
status: in-progress
lane: 2 — openspec-single
links:
  openspec: none
  bmad: none
worktree: none
branch: none
---

# Icons manifest: semantic re-pin + vocabulary lint

## Requirement

`icons/mappings/icons.yaml` currently pins ~80% of placeholders to legacy
carrier indices (`color13`, `color15`, `color6`, `color0`, …) whose meaning
belongs to CSG's 16-color list. Under tpr the same indices resolve to different
roles (e.g. `color13` = `surface_container` `#1f1f25`), which is why icons read
muted and why "same colors" symptoms appear. `defaults.yaml` maps to keys CSG
never emitted (`accent`, `accent-muted`), so it was dead and pins did all the
work.

Decision (2026-10-30): no compatibility layer. ITR resolves any named scheme
key already (`icon-templates-renderer/.../file_color_scheme_loader.py`), so this
is a data change plus validation — no engine change.

### Phase A — proposal (no render change)

- [ ] `icons/mappings/ROLE-MIGRATION.md`: one row per group/variant/placeholder
      with `current token → proposed role → surface class → rationale`.
- [ ] `surface:` field (enum `wallpaper | dark-glass | solid`) added to
      `icons/schema.json` and declared for every variant.
- [ ] `icons/mappings/vocabulary.json`: the declared role list (50 Material +
      `on_backdrop`, from tpr v0.5.0) with source/version note.
- [ ] `validate-icons` rejects any referenced token that is not a declared
      role (including all `colorN`), and validates the schema change.
- [ ] User reviews the proposal — hard gate before Phase B.

### Phase B — apply (after sign-off)

- [ ] Re-pin all groups/variants: wallpaper-floating bar icons → `on_backdrop`;
      dark-glass/solid surfaces → `on_surface`/`on_primary` etc.; accents →
      `tertiary`/`primary`; caution → `error`/`warning`; badges →
      `primary_container`/`on_primary`.
- [ ] `defaults.yaml` becomes real, resolvable role defaults.
- [ ] Render check across the seven wallpapers in light and dark modes; record
      before/after samples.
- [ ] Tag the corpus release after `make gates` green; consumer pin bump
      follows in the runtime/provision tickets.

## Acceptance

- [ ] No `colorN` token remains in icons/defaults mappings (validator proves).
- [ ] Every `surface: wallpaper` variant's foreground resolves to
      `on_backdrop`.
- [ ] `make gates` green; user visual sign-off recorded in the ticket.
- [ ] Tag `v0.6.3` (or next) with the re-pinned corpus.

## Evidence / Verify

- Evidence: current pins in `icons/mappings/icons.yaml`; `defaults.yaml`
  references `accent`/`accent-muted`, absent from a CSG `colors.yaml` but present
  in tpr's; ITR loader preserves top-level keys
  (`src/icon_templates_renderer/adapters/file_color_scheme_loader.py`).
- Verify: `make validate-icons`; `rg 'color[0-9]+' icons/mappings` → 0 matches;
  `itr render` on the seven wallpapers.
