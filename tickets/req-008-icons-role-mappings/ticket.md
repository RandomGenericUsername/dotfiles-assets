---
id: req-008
title: "Icons manifest: semantic role re-pin, real defaults, surface classes, vocabulary lint"
kind: requirement
status: in-progress
lane: 2 — openspec-single
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-008b/
branch: ticket/req-008b-icons-role-pins
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
- [x] User reviews the proposal — hard gate before Phase B. **Approved 2026-10-30:**
      all ten recommendations and every table row, exactly as proposed.

### Phase B — apply (approved 2026-10-30)

- [x] Re-pin all groups/variants: wallpaper-floating bar icons → `on_backdrop`;
      dark-glass/solid surfaces → `on_surface`/`on_primary` etc.; accents →
      `tertiary`/`primary`; caution → `error`/`warning`; badges →
      `primary_container`/`on_primary`.
- [x] `defaults.yaml` becomes real, resolvable role defaults
      (`on_surface` / `surface` / `secondary` / `primary`).
- [x] Render check with the live tpr v0.5.0 + itr v0.2.0: 4 wallpapers (2 dark-band,
      2 bright-band) in dark and light modes; before/after proof recorded below.
      (The checkbox originally said seven wallpapers; the Phase B execution scope from
      the orchestrator was four — see "Render proof".)
- [ ] Tag the corpus release after `make gates` green; consumer pin bump follows in the
      runtime/provision tickets.

## Phase A progress (2026-10-30)

**Branch (Phase A):** `ticket/req-008-icons-role-mappings` — worktree `.worktrees/req-008/`.
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

## Phase B progress (2026-10-30)

**Approval:** the user approved all ten recommendations in `ROLE-MIGRATION.md` and every
table row exactly as proposed, **2026-10-30**. No row was redesigned.
**Branch:** `ticket/req-008b-icons-role-pins` — worktree `.worktrees/req-008b/`.
**Status:** applied; validators run; render proof produced. Not tagged, pushed or merged.

### What landed

| Path | Change |
|---|---|
| `icons/mappings/icons.yaml` | 28 group-level token rows re-pinned, 38 variant overrides re-pinned, 22 group `surface:` declarations, 13 variant `surface:` overrides (`system-battery-*`, `volume/system-*`, `microphone/system-mic-*` → `dark-glass`; `power-menu-modern-with-background` → `solid`). Zero `colorN` and zero aliases as mapping values. |
| `icons/mappings/defaults.yaml` | Four real roles: `COLOR_FOREGROUND: on_surface`, `COLOR_BACKGROUND: surface`, `COLOR_SECONDARY: secondary`, `COLOR_ACCENT: primary`. |
| `icons/mappings/vocabulary.json` | `phase_a_legacy_baseline.entries` **67 → 0**; the comment now documents the empty-baseline end state, and the source note records that tpr v0.5.0 ships `on_backdrop`. The shrink-only mechanism is unchanged. |
| `icons/mappings/ROLE-MIGRATION.md` | Status is APPROVED/APPLIED; Phase B section and the verify line rewritten; the `colorN` values are labelled historical before-values. All proposal tables kept intact as the review record. |
| `icons/README.md` | Gate paragraph now states the baseline is empty and the ratchet remains. |

Comments touched only where the old text asserted the opposite of the new data
(`power-mode`, `media-transport`, `media-transport-panel`, `capture-tool` tints,
`ui/search`, `settings-panel` on/off, `bluetooth`). YAML structure and the unrelated
comments are unchanged.

### Evidence — validators and gates

| Command (in `.worktrees/req-008b/`) | Result |
|---|---|
| `make validate-icons` | **PASS** — `groups=22 variants=136 svgs=117 defaults=4 roles=51 legacy_baseline=0`; note: `58 variant(s) declare surface: wallpaper and were held to on_backdrop ink`. |
| `make validate` | **PASS** — 5 classes, 22 directories, AD-11 absence 359 files. |
| `make validate-content validate-templates validate-configs` | **PASS** each (same output as Phase A). |
| `make validate-desktop` | Python half **PASS** (6 entries, Exec/TryExec agree); then **FAIL at the shellcheck step** — see environment note. |
| `make lint` | `compileall scripts -> ok`, then **FAIL at shellcheck** for the same host reason. |
| `make hermetic` | every Python validator **PASS** with empty `HOME`/`XDG_*` and a foreign cwd, then **FAIL at shellcheck**. |
| `make gates` | **FAIL at `validate-desktop`**, the shellcheck step (it aborts before `lint`/`hermetic`). All corpus validators pass. |
| `rg -c 'color[0-9]+' icons/mappings/icons.yaml icons/mappings/defaults.yaml` | **0 matches** (exit 1). The 220 occurrences under `icons/mappings/` are all the historical before-values in `ROLE-MIGRATION.md`. |

**The `make gates` failure is pre-existing and environmental, not this change.**
`command -v shellcheck` finds nothing on this host. On `master`
(`/home/inumaki/Development/dotfiles/dotfiles-assets`) the same target prints the
identical `FAIL -- shellcheck is not installed but desktop/scripts holds script(s)` and
exits 2. CI installs shellcheck; the corpus half of every gate is green here.

### Evidence — the gate bites after the baseline is empty

Run against throwaway copies, never the branch:

| Mutation | Observed |
|---|---|
| `battery.COLOR_ACCENT: primary` → `color13` (baseline empty) | `FAIL -- 1`: "`COLOR_ACCENT` maps to `color13`, which is not a declared role ... and not an exact `phase_a_legacy_baseline` entry -- `colorN` is the legacy positional carrier list" (exit 1). |
| Add `{"scope":"battery","token":"COLOR_ACCENT","value":"color13"}` to the empty baseline while the pin is `primary` | `FAIL -- 1`: "baseline entry ('battery', 'COLOR_ACCENT', 'color13') matches no live pin -- the baseline is shrink-only; delete the migrated entry" (exit 1). |

The second case proves emptying the list did not weaken the ratchet: the mechanism is
alive, the end state is simply zero entries.

### Render proof

`/tmp/opencode/icon-rerender.html` (self-contained, ≈135 KB): 8 grids — 4 wallpapers ×
dark/light — with 112 inlined SVGs, columns = `battery-100`,
`battery-100-charging`, `wifi-full-default`, `power-menu-default`,
`settings-panel-wifi`, `wlogout-lock`, `media-transport-play`, rows = OLD
(`HEAD:icons/mappings/*.yaml` written to a temp mappings dir) vs NEW. Each glyph sits
on the surface its `surface:` class declares: the wallpaper's measured top-band colour
for `wallpaper`, `surface_container` for `dark-glass`, `surface_container_high` for
`solid`. Machine-readable companion: `/tmp/opencode/icon-rerender-sanity.json`.

Wallpapers: `white_tailed_eagle.png` (dark band), `yasuke-dark-…jpg` (dark band),
`garuda_eagle.jpg` (bright band), `abstract.jpg` (bright saturated band), each rendered
with `tpr generate <image> -o <absolute dir> --mode dark|light` (default formats, so
`colors.yaml` is included) and `itr render` with
`ICON_RENDERER__COLOR_SCHEME__PATH` / `__TEMPLATES__DIR` / `__OUTPUT__OUTPUT_DIR`.
Each render produced 136 SVGs; OLD and NEW used the same palettes.

| Palette | surface | on_surface | on_backdrop | primary | tertiary | error | band | min NEW ink contrast vs band |
|---|---|---|---|---|---|---|---|---|
| wte dark | `#1a110e` | `#f1dfd9` | `#f1dfd9` | `#ffb59a` | `#d5c68e` | `#ffb4ab` | `#541b09` | 10.6:1 |
| wte light | `#fff8f6` | `#231a16` | `#ffffff` | `#8f4c33` | `#695e2f` | `#ba1a1a` | `#541b09` | 13.66:1 |
| yasuke dark | `#1a1110` | `#f1dedc` | `#f1dedc` | `#ffb3ad` | `#e1c28c` | `#ffb4ab` | `#431418` | 12.0:1 |
| yasuke light | `#fff8f7` | `#231918` | `#ffffff` | `#984a45` | `#725b2e` | `#ba1a1a` | `#431418` | 15.53:1 |
| garuda dark | `#19120c` | `#efe0d5` | `#130d07` | `#ffb878` | `#c3cb9e` | `#ffb4ab` | `#d9dee5` | 14.27:1 |
| garuda light | `#fff8f5` | `#221a14` | `#221a14` | `#87521b` | `#5a6238` | `#ba1a1a` | `#d9dee5` | 12.67:1 |
| abstract dark | `#191114` | `#eedfe3` | `#130c0f` | `#feb0d2` | `#f2bb98` | `#ffb4ab` | `#df3e8e` | 4.8:1 |
| abstract light | `#fff8f8` | `#21191c` | `#21191c` | `#894a68` | `#7f5539` | `#ba1a1a` | `#df3e8e` | 4.27:1 |

`on_backdrop` is band-driven, not mode-driven: on the bright garuda/abstract bands it is
a near-black ink by design (maximum contrast against the band). The sanity check
therefore tests **ink by contrast** and **accents by luminance**, which is the actual
bug the migration fixes:

- NEW wallpaper ink is `on_backdrop` on all 58 `surface: wallpaper` variants; minimum
  contrast against the measured band is **4.27:1** (abstract light).
- NEW wallpaper accents resolving near-black on a dark palette: **0** across all 8
  palettes. OLD: **236** accent-role resolutions (59 per dark palette,
  `color13 → surface_container`, luminance ≈ 0.014), i.e. the near-black charging bolt,
  network cross/warning and power-menu arc.
- Scan of the actual rendered NEW SVGs on the four dark palettes: the only fill below
  luminance 0.05 is `on_backdrop` itself on the two bright bands (`#130d07` garuda,
  `#130c0f` abstract) — correct by construction; on the dark bands (wte, yasuke) no
  rendered fill is below 0.05 at all.
- The OLD `settings-panel/wifi` tint (`color13` on a `surface_container` sheet) is
  **#271d1a on #271d1a** on the wte dark grid — the invisible cell in the proof.

Discrepancy recorded: the Phase B checkbox asked for seven wallpapers; the Phase B
execution instruction from the orchestrator specified four (including a dark-band and a
bright one). Four × dark/light are rendered; the remaining three are not claimed.

### Discretionary decisions when applying the proposal

1. `wlogout`, `email-client` and `wallpaper-selector` had **no group-level
   `COLOR_FOREGROUND` row** in the group table (they inherited `foreground` from
   `defaults.yaml`; the inventory shows `foreground (defaults)`). Once the defaults
   became `on_surface`, a `surface: wallpaper` group without an explicit pin fails the
   validator. Added `COLOR_FOREGROUND: on_backdrop` at group level to all three —
   judgment call 7's rule applied to the other two, exactly as the inventory's proposed
   role says.
2. Kept the redundant-but-tabulated overrides: `battery/plugged`
   (`on_backdrop`, may be dropped) and `ui/search` (`on_surface`, may be dropped).
   Dropping them was optional; keeping them matches the reviewed table.
3. `power-menu-modern-with-background`: variant `surface: solid` + `COLOR_FOREGROUND:
   on_primary_container`; the group's `COLOR_BACKGROUND: primary_container` stays. The
   inventory lists the variant's per-token surface column inconsistently (BACKGROUND
   says `wallpaper`), but the variant's effective surface is the declared `solid`.
4. Moved the misplaced `settings-panel/wifi-signal-low` comment (it sat inside that
   variant's `color_mappings`, above `COLOR_FOREGROUND`) to its intended `info-caution`
   neighbour. No mapping value changed; the YAML parsed the key as belonging to
   `wifi-signal-low` before and after.
5. Rewrote comments that asserted the old polarity (see "What landed"); no unrelated
   reformatting. Added the four judgment-call rationales (wlogout, variant surface,
   media-transport surface) as short comments where the data now contradicts the old
   prose.

### Not done (orchestrator owns)

Tag, push and merge; the v0.6.3 release and the consumer pin bump. `make gates` cannot
be green on this host because `shellcheck` is absent (same failure on `master`); CI
installs it.


## Acceptance

- [x] No `colorN` token remains in icons/defaults mappings (validator proves;
      `legacy_baseline=0`).
- [x] Every `surface: wallpaper` variant's foreground resolves to
      `on_backdrop` (58 variants, validator-enforced).
- [ ] `make gates` green; user visual sign-off recorded in the ticket.
      Host cannot run shellcheck; all corpus validators pass, render proof at
      `/tmp/opencode/icon-rerender.html` awaits visual sign-off.
- [ ] Tag `v0.6.3` (or next) with the re-pinned corpus.

## Evidence / Verify

- Evidence: current role pins in `icons/mappings/icons.yaml` (22 groups, 136
  variants, 22 group surfaces, 13 variant surface overrides); four real roles in
  `icons/mappings/defaults.yaml`; empty `phase_a_legacy_baseline` in
  `icons/mappings/vocabulary.json`; the reviewed tables in
  `icons/mappings/ROLE-MIGRATION.md`; the live render proof at
  `/tmp/opencode/icon-rerender.html` + `/tmp/opencode/icon-rerender-sanity.json`.
- Verify (Phase A, historical): `make validate-icons` → PASS (`roles=51 groups=22
  variants=136 legacy_baseline=67`); `git diff master -- icons/mappings/icons.yaml
  icons/mappings/defaults.yaml` → empty (at `c569ec2`).
- Verify (Phase B): `make validate-icons` → PASS with `legacy_baseline=0` and
  `58 variant(s) ... held to on_backdrop ink`;
  `rg -c 'color[0-9]+' icons/mappings/icons.yaml icons/mappings/defaults.yaml` →
  0 matches; `itr render` over the four palettes in the render-proof section.
