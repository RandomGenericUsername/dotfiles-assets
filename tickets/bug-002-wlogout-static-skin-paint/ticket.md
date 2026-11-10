---
id: bug-002
title: "wlogout static stylesheet keeps glass paint over the generated terminal skin"
kind: bug
status: in-progress
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

- [ ] `templates/wlogout/style.css.tpl` has no `border-radius`, border paint,
      `padding`, `color`, `background-color` (apart from an unavoidable
      structural transparent reset), `box-shadow`, `opacity`, `font-size` or
      `font-family` declaration that fights the skin.
- [ ] Wallpaper, icon URLs, layout IDs, `background-size`/`position`/`repeat`,
      `-gtk-icon-effect`, transitions/animations and the palette fallback
      import remain static; `appearance.css` remains the last import.
- [ ] The removed font tunables are dropped from the template's vars schema and
      from the docs; `make validate-templates` still proves contract == body.
- [ ] A regression test fails on the pre-fix template and passes after.
- [ ] Static and combined GTK3 `CssProvider` parse; terminal combined resolves
      radius 2/mono, glass/paper their generated values; Broadway wlogout stays
      alive with no CSS warnings.
- [ ] `make validate-skins`, `make test-skins`, `make gates-ci` pass in the
      foreground.
- [ ] Assets tag `v0.15.1` is annotated on the release commit, merged
      fast-forward to `master`, pushed with `master`, and published.
