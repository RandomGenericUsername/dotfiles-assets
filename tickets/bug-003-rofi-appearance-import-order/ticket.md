---
id: bug-003
title: "rofi static config imports the generated appearance above static radii"
kind: bug
status: done
lane: 2 — bounded correction
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/bug-003/
branch: ticket/bug-003-rofi-appearance-import-order
repro: "rofi -no-config -theme ~/.config/rofi/launcher/config.rasi -dump-theme | grep -A8 -E '^(window|mainbox|inputbar|element) '"
observed: "window border-radius 16px, mainbox 8px, inputbar 5px, element 5px while the generated appearance is the terminal skin (panel/card/cell 0px, control 2px)"
expected: "window 0px, mainbox 0px, inputbar 2px, element 0px — the generated appearance geometry wins over the static fallback"
---

# rofi static config imports the generated appearance above static radii

## Why

`configs/rofi/launcher/config.rasi` defines static fallback geometry for
`window`, `mainbox`, `inputbar` and `element` after its imports. The generated
`appearance.rasi` (rendered from `skins/templates/rofi.rasi.j2`) owns
panel/card/control/cell radii and must load last so those generated values win.
wlogout already does this: its static sheet imports the generated appearance
sheet last. rofi does not, so the static 16/8/5/5 radii override every skin.
A host-rounded `terminal-host` or any other theme therefore renders with
glass-era geometry.

## Repro

With the generated appearance present at `~/.config/rofi/appearance.rasi` and
`~/.config/rofi/colors.rasi` (the deployed layout):

```bash
rofi -no-config -theme ~/.config/rofi/launcher/config.rasi -dump-theme \
  | grep -A8 -E '^(window|mainbox|inputbar|element) '
```

Before the fix the import block is:

```rasi
@import "../colors.rasi"
@import "../appearance.rasi"
```

and the generated sheet is parsed before the static radius declarations below
it.

## Observed

With the `terminal` skin generated (authored panel/card/control/cell radii
`0/0/2/0`), `-dump-theme` prints:

```text
window { ... border-radius: 16px ; }
mainbox { ... border-radius: 8px ; }
inputbar { ... border-radius: 5px ; }
element { ... border-radius: 5px ; }
```

## Expected

The generated appearance wins:

```text
window { ... border-radius: 0px ; }
mainbox { ... border-radius: 0px ; }
inputbar { ... border-radius: 2px ; }
element { ... border-radius: 0px ; }
```

## Fix notes

Root cause: import order. The static radius declarations are intentional
fallbacks for a missing generated sheet, so they stay in place; the generated
`appearance.rasi` import moves to the end of the static file, after every
selector declaration. The palette import stays first so the generated sheet's
role references resolve at parse time.

Regression tests render `terminal` and `terminal-host` appearance sheets into a
temporary deployed layout, run `rofi -no-config -theme ... -dump-theme`, assert
the four selector radii, and require clean stderr. A negative case omits the
generated appearance and proves the palette-only static fallback still parses.

## Outcome (2026-11-11)

**Worktree:** `.worktrees/bug-003/` (base `v0.18.0`)
**Branch:** `ticket/bug-003-rofi-appearance-import-order`
**Commits:** `349e524` (ticket + INDEX plan), `1df566e` (import-order fix,
`validate-configs` guard and render-order tests), `f697f38` (docs/version),
this closing commit (ticket outcome + INDEX done).
**Tag:** `v0.18.1` (annotated) on this closing commit; fast-forward to
`master`, push `master` + tag.

### Delivered

| Path | What changed |
| --- | --- |
| `configs/rofi/launcher/config.rasi` | palette import stays first; static fallback geometry stays in place; generated `../appearance.rasi` import is now the last non-empty line |
| `scripts/validate-configs.py` | new import-order guard: exactly `colors.rasi` then `appearance.rasi`, with the generated import last |
| `skins/tests/test_skins.py` | deployed-layout probe renders `rofi.rasi.j2`, runs `rofi -dump-theme` and asserts the four radii, clean stderr, the pill exclusion and the static fallback |
| `configs/README.md`, `README.md`, `skins/README.md`, `Makefile` | document palette-first/generated-last order and the gate |
| `CHANGELOG.md`, `catalog.yaml`, `skins/schema.json` | `v0.18.1` release metadata |

No runtime, provisioning, composition, contract, template, manifest or live
state changed. `git diff v0.18.0 -- skins/templates skins/manifests
skins/contracts` is empty.

### Import-order and radii proof

`configs/rofi/launcher/config.rasi` now has:

```rasi
@import "../colors.rasi"   /* first */
...
@import "../appearance.rasi"  /* last non-empty line */
```

Rendered deployed layout, `rofi -no-config -theme … -dump-theme`:

| Skin / input | `window` | `mainbox` | `inputbar` | `element` |
| --- | ---: | ---: | ---: | ---: |
| `terminal` (authored) | 0 | 0 | 2 | 0 |
| `terminal-host`, host probe 9 | 9 | 9 | 9 | 9 |
| `flat` (authored) | 0 | 0 | 0 | 0 |
| `paper` (authored) | 6 | 4 | 3 | 3 |
| appearance missing (static fallback) | 16 | 8 | 5 | 5 |

The `terminal-host` dump printed `stderr_bytes=0` and exit `0`, so the
generated sheet's palette roles resolve after the palette-first import.
`terminal-host` keeps its authored pill radius (`2`) while the four rectangles
delegate.

Before the fix, the same `terminal` layout dumped `16/8/5/5`; restoring the
old single-import config makes the new tests fail `5` times, which proves the
regression guard bites.

### Gate evidence

| Claim | Command | Result |
| --- | --- | --- |
| Config boundary | `python3 scripts/validate-configs.py` | **PASS** — includes “rofi imports the palette first and the generated appearance last” |
| Skins gate | `make validate-skins` | **PASS** — 5 manifests, 11 templates, rofi rasi artifact, host probe |
| Fixture suite | `.venv/bin/python -m pytest skins/tests -q` | **PASS** — `163 passed, 3 skipped` (pre-existing GTK `gi` skips) |
| Lint | `PATH="<uv-shellcheck-bin>:$PATH" make lint` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — rc `0`; every validator, lint and `hermetic: PASS` |

### Downstream pins

- **Engine assets mirror:** update to `dotfiles-assets v0.18.1` so the deployed
  `~/.config/rofi/launcher/config.rasi` gets the generated-last import. The
  current live file still carries a manually added top import; this ticket
  does not edit live state.
- **Composition:** later slice, after the assets mirror; no composition edit
  here.
- No provisioning, runtime, contract or app change is needed: the
  `appearance.rasi` link already exists, and only the static consumer file's
  import order changes.
