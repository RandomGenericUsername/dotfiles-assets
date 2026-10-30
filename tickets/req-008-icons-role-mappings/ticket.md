---
id: req-008
title: "Icons manifest: semantic role re-pin, real defaults, surface classes, vocabulary lint"
kind: requirement
status: in-progress
lane: 2 — openspec-single
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-008/
branch: ticket/req-008-icons-role-mappings
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

- [x] `icons/mappings/ROLE-MIGRATION.md`: one row per group/variant/placeholder
      with `current token → proposed role → surface class → rationale` — 22 groups,
      136 variants, 232 placeholder occurrences (complete inventory), 10 judgment
      calls.
- [x] `surface:` field (enum `wallpaper | dark-glass | solid`) added to
      `icons/schema.json` (optional at group level, overridable per variant) and to
      `vocabulary.json`. **Values are declared in Phase B**: setting one is a render
      input, and Phase A must not change renders. The validator reports undeclared
      surfaces as a note and enforces the wallpaper→`on_backdrop` rule only for
      declared surfaces.
- [x] `icons/mappings/vocabulary.json`: the declared role list (50 Material +
      `on_backdrop`, from tpr v0.5.0 / theme-producer REQ-022) with source/version
      note, the alias table, and the shrink-only Phase A legacy baseline.
- [x] `validate-icons` rejects any mapping value that is not a declared role
      (including all `colorN` and the `foreground`/`accent`/`accent-muted`/
      `warning` aliases), validates the schema change, and requires the proposal to
      name every group and variant.
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

## Phase A progress (2026-10-30)

**Branch:** `ticket/req-008-icons-role-mappings` — worktree `.worktrees/req-008/`.
**Commits:** `c569ec2` (Phase A deliverable) and the ticket-record commit on top.
**Pins changed: none.** `git diff master -- icons/mappings/icons.yaml
icons/mappings/defaults.yaml` is empty (verified at `c569ec2`).
**Phase B is blocked on user review.**

### What landed

| Path | What it is |
|---|---|
| `icons/mappings/ROLE-MIGRATION.md` | The proposal: 22 group rows, 28 group-level token rows, 38 variant overrides, 4 `defaults.yaml` rows, and a 232-row complete inventory (one row per variant per placeholder), each with current value → proposed role → surface → rationale → contrast note. Ten judgment calls the user must decide are listed in it. |
| `icons/mappings/vocabulary.json` | 51 declared roles (50 Material + `on_backdrop`), source note (`theme-producer` REQ-022, target v0.5.0), alias→role table with the four non-role aliases, the three surface classes, and `phase_a_legacy_baseline` (67 exact pre-migration pin values). |
| `icons/schema.json` | Optional `surface` on group and variant entries, the `surface_classes` contract, `paths.vocabulary` / `paths.role_proposal`, and the "mapping value is a declared role" rule. `schema_major` stays 1 (additive, optional field). |
| `scripts/validate-icons.py` | Rejects any mapping value that is not a declared role (`colorN` and aliases included); tolerates only an exact baseline entry; fails a baseline entry with no live pin (shrink-only ratchet); validates the `surface` enum; holds `surface: wallpaper` ink to `on_backdrop`; requires `ROLE-MIGRATION.md` to name every group and variant. |
| `icons/README.md`, `catalog.yaml`, `Makefile` | Describe the two new companion files and the expanded gate; no code or pin change. |

### Evidence — commands and results

| Command (in `.worktrees/req-008/`) | Result |
|---|---|
| `make validate-icons` | **PASS** — `groups=22 variants=136 svgs=117 defaults=4 roles=51 legacy_baseline=67`; notes: 67 pre-migration pins remain, 158 group/variants declare no surface yet. |
| `make validate` | **PASS** — 5 classes, 22 directories, AD-11 absence 359 files. |
| `make validate-content validate-templates validate-configs` | **PASS** each (tarball default.png; 9 templates/9 schemas; configs token rule). |
| `python3 scripts/validate-desktop.py` | **PASS** — 6 entries parse, Exec/TryExec agree. |
| `make validate-desktop` | **FAIL at the shellcheck step only** — `shellcheck is not installed`. The Python half printed PASS first. |
| `make lint` | `compileall scripts -> ok`, then **FAIL** at shellcheck for the same host reason. |
| `make hermetic` | every Python validator **PASS** with empty `HOME`/`XDG_*` and a foreign cwd, then **FAIL** at the shellcheck step. |
| `make gates` | **FAIL at `validate-desktop`**, the shellcheck step (it aborts before `lint`/`hermetic`). |
| `make ci-gates-parity` | **PASS** — 9 workflow jobs, 0 exclusions. |
| AST compare of `vocabulary.json` roles vs tpr `MaterialRole` | `engine set == vocabulary minus on_backdrop: True` — 50 enum roles + `on_backdrop`, no missing/extra name. |

**The `make gates` failure is pre-existing and environmental, not this change.**
`command -v shellcheck` → nothing on this host; the same target on `master`
(`/home/inumaki/Development/dotfiles/dotfiles-assets`, branch `master`) prints the
identical `FAIL -- shellcheck is not installed but desktop/scripts holds script(s)`
and exits 2. No sudo and no cached package are available here, so the gate cannot be
made green on this host; CI installs shellcheck. The corpus half of every gate passes.

### Evidence — the validator actually bites (not a vacuous pass)

Each case was run against a throwaway copy of the worktree in `/tmp/opencode/req008/neg`
(so the branch is untouched), `python3 scripts/validate-icons.py --root .`:

| Mutation | Observed |
|---|---|
| Add `wlogout.color_mappings.COLOR_FOREGROUND: color13` | `FAIL -- 1` — "`COLOR_FOREGROUND` maps to `color13`, which is not a declared role ... not an exact `phase_a_legacy_baseline` entry -- `colorN` is the legacy positional carrier list" |
| Migrate `battery.COLOR_ACCENT` to `primary`, leave its baseline entry | `FAIL -- 1` — "baseline entry ('battery', 'COLOR_ACCENT', 'color13') matches no live pin -- the baseline is shrink-only" |
| `battery.surface: glass` | `FAIL` — "`surface` is 'glass'; must be one of ['wallpaper', 'dark-glass', 'solid']" |
| `system-battery-0.surface: wallpaper` with ink `foreground` | `FAIL` — "surface is `wallpaper` but COLOR_FOREGROUND resolves to 'foreground'; a wallpaper glyph's ink must be `on_backdrop`" |
| Remove a role from `vocabulary.json` (50 left) | `FAIL` — "50 role(s) declared; expected 51 (50 Material roles + `on_backdrop`)" |

### Discrepancy with the requirement text (evidence wins)

The requirement says `defaults.yaml` "maps to keys CSG never emitted (`accent`,
`accent-muted`), so it was dead". That is true for CSG, but **not** for tpr: both are
stable aliases that resolve (`accent` → `primary`, `accent-muted` → `secondary`,
`foreground` → `on_surface`) — `theme-producer/src/theme_producer/domain/services.py:54-62`
and `adapters/projections/registry.py:56-71`. The defaults were therefore *alive but
misleading*: `COLOR_SECONDARY: accent` resolved to `primary`, contradicting the token
name. This proposal removes the aliases for intent, not because resolution failed.

### Sequencing gate for Phase B

`on_backdrop` is not shipped yet: `theme-producer` tags end at `v0.4.0`, REQ-022 is
unimplemented at `HEAD` (its worktree is at the same commit), so a Phase B pin of
`on_backdrop` would resolve an unknown key **until tpr v0.5.0 lands**. Phase B
therefore needs both the user's sign-off and the tpr release.

### Judgment calls for the reviewer (details in ROLE-MIGRATION.md)

1. Badge ink: proposal uses `on_primary_container` (container pair), not the
   shorthand's `on_primary` — `on_primary` is not contrast-safe on
   `primary_container` in light mode.
2. `network.COLOR_CROSS` → `error` (hue) vs `on_backdrop` (shape only).
3. `battery.COLOR_ACCENT` → `primary` on the wallpaper (two-tone risk) vs `surface`
   knock-out.
4. `ui` declared `solid` (field/card), although it is in the runtime's current bar
   allowlist.
5. `media-transport` declared `dark-glass` although its comment calls it bar-facing.
6. `settings-panel.info-caution` → `tertiary`: the comment and the old pin disagreed.
7. `wlogout` is `wallpaper` (full-screen wallpaper, transparent buttons), so Phase B
   must pin it explicitly instead of inheriting defaults.
8. `on_backdrop` timing (above).
9. `power-menu-modern-with-background` → `surface: solid` + container pairs.
10. The 67-entry baseline as a ratchet instead of a red Phase A gate.

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
- Verify (Phase A): `make validate-icons` → PASS (`roles=51 groups=22 variants=136
  legacy_baseline=67`); `git diff master -- icons/mappings/icons.yaml
  icons/mappings/defaults.yaml` → empty; negative-case matrix in "Phase A progress".
- Verify (Phase B): `make validate-icons` → PASS with `legacy_baseline=0`;
  `rg 'color[0-9]+' icons/mappings` → 0 matches; `itr render` on the seven
  wallpapers.
