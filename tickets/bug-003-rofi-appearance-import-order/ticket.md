---
id: bug-003
title: "rofi static config imports the generated appearance above static radii"
kind: bug
status: in-progress
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
the four selector radii, and require clean stderr. A negative case removes the
appearance import/file and proves the palette-only static fallback still
parses.
