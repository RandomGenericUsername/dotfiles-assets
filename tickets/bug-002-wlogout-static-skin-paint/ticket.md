---
id: bug-002
title: "wlogout static stylesheet keeps glass paint over the generated terminal skin"
kind: bug
status: done
lane: 2 — bounded correction
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/bug-002/
branch: ticket/bug-002-wlogout-static-skin-paint
repro: "rg -n 'border-radius|border:|padding:|background-color:|box-shadow:|opacity:|font-size:|font-family:|^[[:space:]]*color:' templates/wlogout/style.css.tpl"
observed: "The static sheet still declares border-radius: 1em, border: 0em, padding: 0.5em, color, background-color, box-shadow, opacity, font-size and font-family. The generated appearance/wlogout.css is imported last, but properties it does not set (hover opacity/shadow/background-size/transition) and the lingering glass geometry keep wlogout glassy under the terminal skin."
expected: "The static sheet owns no skin paint, rhythm or typography: no border-radius/border paint/padding/color/background-color/box-shadow/opacity/font-size/font-family declarations. The generated appearance.css remains imported last, so terminal yields radius 2/mono and glass/paper yield their own generated values without static overrides."
---

# wlogout static stylesheet keeps glass paint over the generated terminal skin

## Repro

```bash
rg -n 'border-radius|border:|padding:|background-color:|box-shadow:|opacity:|font-size:|font-family:|^[[:space:]]*color:' templates/wlogout/style.css.tpl
```

## Observed

The static template still owns the pre-skin paint and rhythm:

- `button`: `color`, `border-radius: 1em`, `border: 0em`, `padding: 0.5em`,
  `background-color: transparent`.
- `button:focus, button:hover`: `background-color: @primary_container`,
  `opacity: 0.8`, `box-shadow: 0 0 0.9em @on_surface`.
- `button span`: `font-size: 1.2em`.
- `*`: `font-family`, `font-size`; `window`: `font-size: 1em`.

The generated `appearance/wlogout.css` is imported last and does set `color`,
`background-color`, `border`, `border-radius`, `padding` and `font-size`, but
the static hover opacity/shadow and `background-size`/transition remain, and the
static typography still competes. Under `terminal` the menu therefore still
reads glassy instead of dense monospace with a 2px radius.

## Expected

The static sheet keeps only app-owned structure: palette import, wallpaper,
icon URLs, layout IDs, background size/position/repeat, icon effect and motion
transitions/animations. All skin paint, rhythm and typography come from the
generated `appearance.css` imported last. Terminal renders radius 2 and
JetBrainsMono; glass and paper render their own generated values.

This is the W-2.6 correctness gap left by `req-019`: the generated sheet was
added and imported, but the static template was never stripped of ownership.

## Fix notes

Root cause: `templates/wlogout/style.css.tpl` predates the Appearance v2 plane
and still carries the static glass paint/rhythm block. The import order was
correct, so the missing work is deleting static paint ownership and tightening
the tests so it cannot return.

Regression coverage: a skins test strips comments from the static template and
asserts no forbidden property declarations remain, that the structural rules
(wallpaper, icons, background layout, icon effect, transitions) survive, and
that `appearance.css` is imported last. GTK3 `CssProvider` and Broadway probes
prove the combined terminal sheet parses and wins.

## Acceptance

- [x] `templates/wlogout/style.css.tpl` has no `border-radius`, border paint,
      `padding`, `color`, `background-color` (apart from an unavoidable
      structural transparent reset), `box-shadow`, `opacity`, `font-size` or
      `font-family` declaration that fights the skin.
- [x] Wallpaper, icon URLs, layout IDs, `background-size`/`position`/`repeat`,
      `-gtk-icon-effect`, transitions/animations and the palette fallback
      import remain static; `appearance.css` remains the last import.
- [x] The removed font tunables are dropped from the template's vars schema and
      from the docs; `make validate-templates` still proves contract == body.
- [x] A regression test fails on the pre-fix template and passes after.
- [x] Static and combined GTK3 `CssProvider` parse; terminal combined resolves
      radius 2/mono, glass/paper their generated values; Broadway wlogout stays
      alive with no CSS warnings.
- [x] `make validate-skins`, `make test-skins`, `make gates-ci` pass in the
      foreground.
- [x] Assets tag `v0.15.1` is annotated on the release commit, merged
      fast-forward to `master`, pushed with `master`, and published.

## Outcome (2026-11-09)

**Worktree:** `.worktrees/bug-002/` (base `v0.15.0`)
**Branch:** `ticket/bug-002-wlogout-static-skin-paint`
**Commits:** `fe78cec` (ticket + INDEX plan), `49e2cc3` (static template,
vars schema, regression test, docs, CHANGELOG + version), this closing commit
(ticket outcome + INDEX done).
**Tag:** `v0.15.1` (annotated) on this closing commit; fast-forward to
`master`.

### Exact static diff

```diff
@@ -1,44 +1,30 @@
 @import url("{{COLORS_FILE_PATH}}");
 
+/* Structure only: wallpaper, icon geometry and motion stay app-owned. The
+ * generated skin owns all surface styling and is imported last. */
 * {
-    font-family: {{SYSTEM_FONT_FAMILY}};
 	transition: 20ms;
-	box-shadow: none;
-	font-size: {{FONT_SIZE_PX}}px; /* Only supports px */
-    background-image: none;
-	background: none;
+	background-image: none;
 }
 
 window {
-    background-image: none;
-	background: url("{{CURRENT_WALLPAPER_SYMLINK}}");
+	background-image: url("{{CURRENT_WALLPAPER_SYMLINK}}");
 	background-size: cover;
-    font-size: 1em;
+	background-position: center;
+	background-repeat: no-repeat;
 }
 
 button {
-    color: @on_surface;
-    border-radius: 1em;
-	border: 0em;
-    padding: 0.5em;
-    background-repeat: no-repeat;
-    background-position: center;
-    background-color: transparent;
-    background-size: 20%;
-    animation: gradient_f 20s ease-in infinite;
+	background-repeat: no-repeat;
+	background-position: center;
+	background-size: 20%;
+	animation: gradient_f 20s ease-in infinite;
 	transition: all 0.3s cubic-bezier(.55, 0.0, .28, 1.682), box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out;
-    -gtk-icon-effect: none;
+	-gtk-icon-effect: none;
 }
 
 button:focus, button:hover {
-    background-color: @primary_container;
-	opacity: 0.8;
-    background-size: 30%;
-    box-shadow: 0 0 0.9em @on_surface;
-}
-
-button span {
-    font-size: 1.2em;
+	background-size: 30%;
 }
 
 #lock {
```

### Gate and probe evidence

| Claim | Command | Result |
| --- | --- | --- |
| Static grep has no paint/rhythm/type | the ticket `repro:` one-liner | **0 matches** |
| Regression bites on the old sheet | swap in `d9cdaf4:templates/wlogout/style.css.tpl`, run the new test | **FAIL** — 13 offenders (`font-family`, `box-shadow`, `color`, `border-radius`, `padding`, `opacity`, …); passes after restore |
| Templates contract | `python3 scripts/validate-templates.py` | **PASS** — 9/9, `required=22 optional=1`, properties == reads |
| Skins gate | `make validate-skins` | **PASS** — 4 manifests, 8 templates, 8 targets, 8 expansions |
| Skins fixtures | `make test-skins PYTEST="<main>/.venv/bin/python -m pytest"` | **PASS** — `97 passed in 18.69s` |
| CI gate set (foreground) | `PATH="/tmp/opencode/bin:$PATH" make gates-ci` | **PASS** — every validator, lint, `hermetic: PASS` |
| GTK3 `CssProvider` static-only | static sheet + empty `appearance.css` | **PASS** — no CSS warnings |
| GTK3 `CssProvider` combined terminal | static + terminal generated | **PASS** — no CSS warnings; window bg `(0.0706,0.0745,0.0941,1.0)`, button `border-radius=2`, `font-size=10` |
| GTK3 `CssProvider` combined glass | static + glass generated | **PASS** — window bg alpha `0.94`, `border-radius=7`, `font-size=11` |
| GTK3 `CssProvider` combined paper (dark/light) | static + paper generated | **PASS** — `border-radius=3`, `font-size=11` |
| Terminal generated text | expand `terminal:dark` | `border-radius: 2px;` and `font-family: JetBrainsMono Nerd Font, monospace;` |
| Broadway wlogout combined | `timeout 5s wlogout -C …/terminal/dark/style.css -l configs/wlogout/layout -p xdg` | rc `124` (stayed alive); only `GtkSettings Cursor Theme` warning, **no CSS warning** |

### Version note (recorded discrepancy)

The generic README semver table calls removing a template's required variable a
MAJOR change. This slice removes the two static-only font inputs
(`SYSTEM_FONT_FAMILY`, `FONT_SIZE_PX`) and is released as the requested
**PATCH** `v0.15.1`: no path moved and `schema_major` stays `1`; the removed
inputs fed only the deleted static typography. Recorded here rather than
silently claiming the contract did not change.

### Downstream pins (not part of this slice)

- **Engine assets mirror:** mirror `v0.15.1` and pick up the 3-name wlogout
  render context (`COLORS_FILE_PATH`, `CURRENT_WALLPAPER_SYMLINK`,
  `STATE_ROOT`) in its own commit.
- **Composition:** after the assets mirror, bump the assets pin to `v0.15.1`
  and update stale assets source refs; its own gate proves the mirror.
- No runtime, provisioning, composition, app or live-state change is in this
  ticket. **No apply, no live hotfix.**
