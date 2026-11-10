---
id: req-022
title: "wlogout Phase 2c: card state fill correctness"
kind: requirement
status: done
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

- [x] Base/hover/focus `button` rules keep the card background; hover/focus
      change only ring and ink, with no hover/focus fill as background.
- [x] `button:active` uses `state.selected.fill`/ink/ring.
- [x] Expansion tests prove card-background retention and ring/ink changes for
      all four skins; a focused-card provider probe proves the card value.
- [x] GTK3 `CssProvider` parses static and combined sheets; Broadway wlogout
      stays alive with no CSS warnings.
- [x] Static wlogout sheet remains structure-only with zero forbidden paint and
      is unchanged from `v0.15.2`.
- [x] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [x] `v0.15.3` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `W-2.17`–`W-2.19` in
  `dotfiles-v3/docs/108-non-ags-skin-consumers.md`; card/state values in
  `skins/manifests/*.toml`; the focused-card probe recorded in the outcome.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; GTK3 `CssProvider` probes and the Broadway smoke recorded in
  the outcome.

## Outcome (2026-11-10)

**Worktree:** `.worktrees/req-022/` (base `v0.15.2`)
**Branch:** `ticket/req-022-wlogout-card-state`
**Commits:** `065f118` (ticket + INDEX plan), `762ab8d` (template, tests, docs,
CHANGELOG + version), this closing commit (ticket outcome + INDEX done).
**Tag:** `v0.15.3` (annotated) on this closing commit; fast-forward to
`master`.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/templates/wlogout.gtk.css.j2` | `button:hover`/`:focus` keep `surface.card.bg` and change only state ring/ink; `:active` keeps selected fill/ink/ring; base card and `span` type unchanged |
| `skins/tests/test_skins.py` | wlogout token matrix drops hover/focus fill; per-skin expansion asserts hover/focus retain card fill, active uses selected paint, plus a conditional GTK3 style-context focus probe |
| `skins/tests/fixtures/positive/wlogout.gtk.css.j2` | pinned byte-equal to the shipped template |
| `skins/schema.json` | status `populated (v0.15.3)`; note records card state ownership |
| `skins/README.md` | hover/focus card-surface ownership, active selected paint and the GTK3 focus probe |
| `README.md`, `templates/README.md`, `catalog.yaml`, `CHANGELOG.md` | version, inventory wording and v0.15.3 release notes |
| `templates/wlogout/style.css.tpl` | **unchanged** from `v0.15.2` |

### Exact template diff

```diff
@@ -13,13 +13,13 @@ button {
 
 button:hover {
     color: {{SKIN_STATE_HOVER_INK}};
-    background-color: {{SKIN_STATE_HOVER_FILL}};
+    background-color: {{SKIN_SURFACE_CARD_BG}};
     border-color: {{SKIN_STATE_HOVER_RING}};
 }
 
 button:focus {
     color: {{SKIN_STATE_FOCUS_INK}};
-    background-color: {{SKIN_STATE_FOCUS_FILL}};
+    background-color: {{SKIN_SURFACE_CARD_BG}};
     border-color: {{SKIN_STATE_FOCUS_RING}};
 }
```

### Expanded focus state

| Skin | base/hover/focus background | hover/focus ink | hover/focus ring | active background/ink |
| --- | --- | --- | --- | --- |
| `glass` dark | `alpha(@surface_container_high, 0.18)` | `@on_surface` | `@primary` | `@primary_container` / `@on_primary_container` |
| `flat` dark | `transparent` | `@on_surface` | `@primary` | `@primary` / `@on_primary` |
| `paper` dark | `@surface_container_low` | `@on_surface` | `@primary` | `@primary_container` / `@on_primary_container` |
| `terminal` dark | `@surface_container` | `@on_surface` | `@primary` | `@primary_container` / `@on_primary_container` |

### Gate and probe evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 4 manifests, 8 templates, 8 targets, 8 expansions, 57 tokens |
| Skins fixtures | `make test-skins PYTEST="<assets>/.venv/bin/python -m pytest"` | **PASS** — `102 passed, 2 skipped`; skips are `gi` absent from the venv (GTK3 parse + focus probe run below with system Python) |
| Static forbidden-declaration grep | comment-stripped declaration regex over `templates/wlogout/style.css.tpl` | **0 matches** |
| Static sheet unchanged | `git diff --exit-code -- templates/wlogout/style.css.tpl` | **rc 0** (empty) |
| Lint | `make lint` (shellcheck from the uv cache on `PATH`) | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — every validator, lint, `hermetic: PASS` |
| GTK3 `CssProvider` static-only | rendered static sheet + real palette/wallpaper/icon paths | **PASS** — no `parsing-error` |
| GTK3 `CssProvider` combined | glass/flat/paper/terminal dark + static | **PASS** — no `parsing-error` for all four |
| GTK3 focused-card style probe | terminal card under Broadway: `get_background_color(NORMAL/FOCUSED)` + `get_border_color(FOCUSED)` | **PASS** — normal and focused both `rgb(32,40,48)` (the terminal card fill); focused ring `rgb(136,170,255)` (`@primary`) |
| Broadway wlogout combined terminal | `GDK_BACKEND=broadway timeout 5s wlogout -C …/terminal/style.css -l configs/wlogout/layout -p xdg` | rc `124` (stayed alive); no CSS warning, only the backend cursor-theme warning |
| Broadway wlogout combined glass | same with `…/glass/style.css` | rc `124` (stayed alive); no CSS warning, only the backend cursor-theme warning |

### Downstream pins (not part of this slice)

- **Engine assets mirror:** mirror `v0.15.3` in its own commit and regenerate
  `appearance/wlogout.css`; the wlogout template bytes changed for all four
  skins, so that target's appearance hash churns once.
- **Composition:** after the assets mirror, bump the assets pin to `v0.15.3`
  and refresh stale assets source refs; its own gate proves the mirror.
- No runtime, provisioning, composition, app or live-state change is in this
  ticket. **No apply, no live hotfix; wlogout picks up the sheet on next
  launch.**
