---
id: req-019
title: "Skins wlogout consumer: paint/rhythm target, required-target gate, static import"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-019/
branch: ticket/req-019-wlogout-skin-consumer
---

# Skins wlogout consumer: paint/rhythm target, required-target gate, static import

## Why

wlogout is the first non-AGS CSS consumer of the v2 Appearance plane. Phase 1
palette parity already works: the rendered static stylesheet imports
`state/current/palette/colors.gtk.css`, so a new generation changes the palette
on the next launch.

Phase 2 makes wlogout a normal generated target without adding a runtime
adapter:

```text
skins/templates/wlogout.gtk.css.j2  ->  appearance/wlogout.css
static style.css imports appearance.css LAST
```

The static app-owned structure — wallpaper, icons, layout IDs, transitions and
grid — stays in `templates/wlogout/style.css.tpl`. The generated sheet contains
paint and rhythm only.

Acceptance criteria: `W-2.1`, `W-2.2`, `W-2.6`, `W-2.9`, `W-2.10` in
`dotfiles-v3/docs/108-non-ags-skin-consumers.md`; epic `SKIN-CONSUMERS`.
Runtime/provisioning/composition work is deliberately out of scope here.

## Requirement

1. **Required-target gate first.** `skins/schema.json` gains the frozen
   `required_targets` set (the seven existing AGS targets plus `wlogout`);
   `scripts/validate-skins.py` compares it exactly with the discovered
   `<configDir>.gtk.css.j2` set. A missing `wlogout.gtk.css.j2` must fail
   `make validate-skins`; an unregistered extra template must also fail.
2. **Add `skins/templates/wlogout.gtk.css.j2`** using only v2 token
   placeholders:
   - `window` background from `surface.panel.bg`;
   - `button` base from `surface.control.*` + `ink.ink`;
   - `button:hover` / `button:focus` / `button:active` from the matching
     `state.{hover,focus,selected}.{fill,ink,ring}` triples;
   - `button span` typography from `type.font-family`, `type.font-weight`,
     `type.letter-spacing` and `type.size-title`.
   No literal hex, `transition`, `animation`, structure/variant, layout IDs,
   icons, wallpaper, grid or margins.
3. **Static import last.** Append `@import url("appearance.css");` at the end
   of `templates/wlogout/style.css.tpl` so the generated same-specificity rules
   win the GTK3 cascade. Existing wallpaper/icon/layout/transition rules stay
   static and app-owned.
4. **Missing-target behaviour.** Keep the palette import first so a missing
   generated target leaves wlogout with palette-only styling at launch; the
   GTK3 `CssProvider` still reports a clear missing-import error, so the gap is
   never silent. Document the provisioning order that creates
   `config/wlogout/appearance.css` before launch and test the missing-target
   case.
5. **Tests/docs.** Add `wlogout` to the positive template matrix; negative
   fixtures for literal hex and structure (existing transition fixture stays);
   tests for a missing required target and a missing template. Update
   `skins/README.md`, `README.md`, `templates/README.md`, `catalog.yaml`,
   `CHANGELOG.md`, this ticket and `tickets/INDEX.md`.
6. **Release.** Tag `v0.14.0` (annotated), fast-forward merge to `master`, push
   `master` + the tag, publish the GitHub Release with only the `v0.14.0`
   artifacts. Record the one-time template-hash churn in the release notes.

## Acceptance

- [x] The gate is red before the template lands and green after: `wlogout` is a
      required target, missing template/target fails, extra target fails.
- [x] `wlogout.gtk.css.j2` expands for all four manifests × both modes and uses
      only v2 placeholders/roles; no hex/transition/structure/layout/icons/
      wallpaper/grid/margins.
- [x] `templates/wlogout/style.css.tpl` imports `appearance.css` last; GTK3
      parses the combined rendered sheet and the generated rules win the
      cascade.
- [x] Missing-target case: GTK3 reports the missing import clearly; Broadway
      wlogout remains launchable with the palette-only fallback.
- [x] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [ ] `v0.14.0` is an annotated tag on the fast-forward-merged commit; `master`
      and the tag are pushed; the release carries only `v0.14.0` artifacts.

## Evidence / Verify

- Evidence: `W-2.1`/`W-2.2`/`W-2.6`/`W-2.9`/`W-2.10` in
  `dotfiles-v3/docs/108-non-ags-skin-consumers.md`; the static template is
  rendered by `dotfiles-provision/ansible/roles/wlogout_config`; the runtime
  derives `<configDir>.css` targets from the template set
  (`dotfiles-runtime/src/runtime/domain/models.py:173-186`).
- Verify: `make validate-skins`, `make test-skins
  PYTHON=$PWD/.venv/bin/python`, `make lint`, `make gates-ci`; GTK3
  `CssProvider` probes and the Broadway smoke recorded in the outcome.

## Outcome (2026-11-09)

**Worktree:** `.worktrees/req-019/`
**Branch:** `ticket/req-019-wlogout-skin-consumer`
**Commits:** `5737594` (ticket + INDEX plan), `4fd907e` (required-target gate,
red before the template), `7c00d92` (template, static import, tests, docs,
CHANGELOG), this closing commit (ticket outcome + INDEX done).
**Tag:** `v0.14.0` (annotated) after the green gates; fast-forward to `master`.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/schema.json` | `frozen.required_targets` names the seven AGS targets plus `wlogout`; status `populated (v0.14.0)` |
| `scripts/validate-skins.py` | exact required-target comparison: missing targets and unregistered extras fail; docstring records the new rule |
| `skins/templates/wlogout.gtk.css.j2` | new paint/rhythm template: panel → window; control/ink → button; hover/focus/selected → button states; type → button span |
| `templates/wlogout/style.css.tpl` | `@import url("appearance.css");` appended last; palette import and all static wallpaper/icon/layout/transition rules unchanged |
| `templates/wlogout/style.css.vars.schema.json` | description records the relative generated import; still five render variables |
| `skins/tests/test_skins.py` | `wlogout` in the positive matrix; paint/rhythm-only, expansion, required-target, missing-template, missing-declaration, extra-target and positive-fixture tests |
| `skins/tests/fixtures/invalid/{literal-hex,structure}.gtk.css.j2` | new negative fixtures; transition fixture remains |
| `skins/tests/fixtures/positive/wlogout.gtk.css.j2` | positive fixture pinned byte-equal to the shipped template |
| `skins/README.md`, `README.md`, `templates/README.md`, `catalog.yaml`, `CHANGELOG.md` | eight-template inventory, required-target gate, wlogout static import and the `v0.14.0` churn note |

### Exact template / static diff

Generated template (paint/rhythm only):

```css
window { background-color: {{SKIN_SURFACE_PANEL_BG}}; }
button {
    color: {{SKIN_INK_INK}};
    background-color: {{SKIN_SURFACE_CONTROL_BG}};
    border: {{SKIN_SURFACE_CONTROL_BORDER_WIDTH}} solid {{SKIN_SURFACE_CONTROL_BORDER}};
    border-radius: {{SKIN_SURFACE_CONTROL_RADIUS}};
    padding: {{SKIN_SURFACE_CONTROL_PADDING}};
    font-size: {{SKIN_SURFACE_CONTROL_FONT_SIZE}};
    font-weight: {{SKIN_SURFACE_CONTROL_FONT_WEIGHT}};
}
button:hover  { color: {{SKIN_STATE_HOVER_INK}};    background-color: {{SKIN_STATE_HOVER_FILL}};    border-color: {{SKIN_STATE_HOVER_RING}}; }
button:focus  { color: {{SKIN_STATE_FOCUS_INK}};    background-color: {{SKIN_STATE_FOCUS_FILL}};    border-color: {{SKIN_STATE_FOCUS_RING}}; }
button:active { color: {{SKIN_STATE_SELECTED_INK}}; background-color: {{SKIN_STATE_SELECTED_FILL}}; border-color: {{SKIN_STATE_SELECTED_RING}}; }
button span {
    font-family: {{SKIN_TYPE_FONT_FAMILY}};
    font-size: {{SKIN_TYPE_SIZE_TITLE}};
    font-weight: {{SKIN_TYPE_FONT_WEIGHT}};
    letter-spacing: {{SKIN_TYPE_LETTER_SPACING}};
}
```

Static diff (append only; everything above stays app-owned):

```diff
 #reboot {
     background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/reboot.svg"));
 }
+
+/* Generated skin appearance is imported LAST so its same-specificity paint
+ * rules win the cascade. The palette import at the top keeps wlogout usable
+ * with palette-only styling if the generated target is not present yet. */
+@import url("appearance.css");
```

### Gate evidence — commands and exact results

| Command | Result |
| --- | --- |
| `make validate-skins` after the gate, before the template | **FAIL** — `skins/templates/: missing required target(s) ['wlogout']`; `templates=7` |
| `make validate-skins` after the template | **PASS** — `manifests=4 templates=8 targets=ags,…,wlogout expansions=8`; required targets exact |
| `make test-skins PYTHON=$PWD/.venv/bin/python` | **PASS** — `89 passed in 12.08s` |
| `make lint` | **PASS** after supplying a temporary shellcheck 0.11.0 wrapper (`uvx --from shellcheck-py`); host has no `shellcheck`, so the bare target first failed with `shellcheck is not installed`. No repository change. |
| `make gates-ci` | **PASS** — all nine gates (`validate`, icons, content, templates, configs, desktop, skins, lint, hermetic); `hermetic: PASS` |
| `make ci-gates-parity` | **PASS** — `GATES (9)` vs workflow jobs `(10)`; every job accounted for |
| GTK3 `CssProvider` — generated | **PASS** |
| GTK3 `CssProvider` — static-only | **PASS** |
| GTK3 `CssProvider` — combined (generated imported last) | **PASS** |
| GTK3 `CssProvider` — missing `appearance.css` | **FAIL clearly** — `Failed to import: Error opening file …/appearance.css: No such file or directory` |
| Cascade probe (Broadway) | static-only `window bg (0.0,0.0,0.0,0.0)`; combined `window bg (0.0706,0.0745,0.0941,1.0)` — generated rules win |
| Broadway wlogout — combined | rc `124` (stayed alive); no CSS warnings (only `Falling back to xdg protocol`) |
| Broadway wlogout — missing target | rc `124` (stayed alive); no CSS warnings; palette-only fallback |

### Missing-target behaviour

The static palette import stays first; `appearance.css` is imported last. If the
generated target is absent, wlogout remains launchable with palette-only
styling, while GTK3 `CssProvider` names the missing import explicitly. The
provisioning slice must create `config/wlogout/appearance.css` before launch
(`state_links` runs after `runtime-seed`); this ticket records the order and
tests both the GTK3 failure and the Broadway fallback.

### Remaining questions for the next slices

- **Runtime:** prove the v3 `GenerationStore` writes `appearance/wlogout.css`
  and the manifest target from a fixture copied from this tag; W-2.4 stays
  there (embedded v0.8.0 schema), not in this slice.
- **Provisioning:** own
  `config/wlogout/appearance.css -> state/current/appearance/wlogout.css`,
  verify the raw target/name/resolution, and assert the rendered static sheet
  imports `appearance.css` last.
- **Composition:** pin assets `v0.14.0` only after this tag; update both the
  `assets.tag` and every stale `assets/v0.12.2/...` source ref; do not pin a
  branch or SHA.
- **Release:** record the one-time full appearance refresh caused by the
  template-hash churn (W-2.10) in the assets release notes.

