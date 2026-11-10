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

- [x] The generated `button` base uses `surface.card` fill/border/padding and
      `surface.panel` border-width/radius; states and span type are unchanged.
- [x] The static wlogout sheet is unchanged from `v0.15.1` and still has zero
      forbidden paint/rhythm declarations.
- [x] Expansion tests prove the card fill + panel geometry for all four skins;
      terminal is `@surface_container` with panel 1px/0px.
- [x] GTK3 `CssProvider` parses static and combined sheets; Broadway wlogout
      stays alive with no CSS warnings.
- [x] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [x] `v0.15.2` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `W-2.11`–`W-2.16` in
  `dotfiles-v3/docs/108-non-ags-skin-consumers.md`; the `surface.card` and
  `surface.panel` values in `skins/manifests/*.toml`.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; GTK3 `CssProvider` probes and the Broadway smoke recorded in
  the outcome.

## Outcome (2026-11-10)

**Worktree:** `.worktrees/req-021/` (base `v0.15.1`)
**Branch:** `ticket/req-021-wlogout-card-mapping`
**Commits:** `1c6eedb` (ticket + INDEX plan), `440990f` (template, tests, docs,
CHANGELOG + version), this closing commit (ticket outcome + INDEX done).
**Tag:** `v0.15.2` (annotated) on this closing commit; fast-forward to
`master`.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/templates/wlogout.gtk.css.j2` | button base: `surface.card.{bg,border,padding}` + `surface.panel.{border-width,radius}`; control mapping removed; state and type blocks unchanged |
| `skins/tests/test_skins.py` | wlogout token matrix updated; card/panel placeholder + per-skin expansion tests; conditional GTK3 static/combined parse test; static ownership grep retained |
| `skins/tests/fixtures/positive/wlogout.gtk.css.j2` | pinned byte-equal to the shipped template |
| `skins/schema.json` | status `populated (v0.15.2)`; note records the card/panel wlogout mapping |
| `skins/README.md` | wlogout action-card mapping, host alignment and static ownership section |
| `README.md`, `templates/README.md`, `catalog.yaml`, `CHANGELOG.md` | version, inventory wording and v0.15.2 release notes |
| `templates/wlogout/style.css.tpl` | **unchanged** from `v0.15.1` |

### Exact template diff

```diff
@@ -5,12 +5,10 @@ window {
 
 button {
     color: {{SKIN_INK_INK}};
-    background-color: {{SKIN_SURFACE_CONTROL_BG}};
-    border: {{SKIN_SURFACE_CONTROL_BORDER_WIDTH}} solid {{SKIN_SURFACE_CONTROL_BORDER}};
-    border-radius: {{SKIN_SURFACE_CONTROL_RADIUS}};
-    padding: {{SKIN_SURFACE_CONTROL_PADDING}};
-    font-size: {{SKIN_SURFACE_CONTROL_FONT_SIZE}};
-    font-weight: {{SKIN_SURFACE_CONTROL_FONT_WEIGHT}};
+    background-color: {{SKIN_SURFACE_CARD_BG}};
+    border: {{SKIN_SURFACE_PANEL_BORDER_WIDTH}} solid {{SKIN_SURFACE_CARD_BORDER}};
+    border-radius: {{SKIN_SURFACE_PANEL_RADIUS}};
+    padding: {{SKIN_SURFACE_CARD_PADDING}};
 }
 
 button:hover {
```

### Expanded values

| Skin | card fill | border (panel width + card colour) | panel radius | card padding |
| --- | --- | --- | --- | --- |
| `glass` dark | `alpha(@surface_container_high, 0.18)` | `1.5px solid alpha(@on_surface, 0.10)` | `12px` | `10px` |
| `flat` dark | `transparent` | `0px solid transparent` | `0px` | `10px` |
| `paper` dark | `@surface_container_low` | `1px solid alpha(@on_surface, 0.10)` | `6px` | `10px` |
| `terminal` dark | `@surface_container` | `1px solid alpha(@on_surface, 0.18)` | `0px` | `8px` |

### Gate and probe evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 4 manifests, 8 templates, 8 targets, 8 expansions, 57 tokens |
| Skins fixtures | `make test-skins PYTEST="<main>/.venv/bin/python -m pytest"` | **PASS** — `102 passed, 1 skipped`; skip is `gi` absent from the venv, GTK3 probe run below with system Python |
| Regression bites on the old template | restore `v0.15.1:skins/templates/wlogout.gtk.css.j2`, run the three new wlogout test groups | **FAIL** — `6 failed, 87 deselected`; passes after restore |
| Static forbidden-declaration grep | the ticket `repro:` one-liner | **0 matches** (rg rc `1`) |
| Static sheet unchanged | `git diff -- templates/wlogout/style.css.tpl` | **empty** |
| Lint | `make lint` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — every validator, lint, `hermetic: PASS` |
| GTK3 `CssProvider` static-only | static sheet + empty `appearance.css` | **PASS** — no `parsing-error` signal |
| GTK3 `CssProvider` combined | glass/flat/paper/terminal dark + static | **PASS** — no `parsing-error` for all four |
| Broadway wlogout combined terminal | `GDK_BACKEND=broadway timeout 5s wlogout -C …/terminal/style.css -l configs/wlogout/layout -p xdg` | rc `124` (stayed alive); empty log, **no CSS warnings** |
| Broadway wlogout combined glass | same with `…/glass/style.css` | rc `124` (stayed alive); empty log, **no CSS warnings** |

### Downstream pins (not part of this slice)

- **Engine assets mirror:** mirror `v0.15.2` in its own commit and regenerate
  `appearance/wlogout.css`; the wlogout template bytes changed for all four
  skins, so that target's appearance hash churns once.
- **Composition:** after the assets mirror, bump the assets pin to `v0.15.2`
  and refresh stale assets source refs; its own gate proves the mirror.
- No runtime, provisioning, composition, app or live-state change is in this
  ticket. **No apply, no live hotfix; wlogout picks up the sheet on next
  launch.**

