---
id: req-032
title: "Sound-panel icons: media controls and settings gear"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-032/
branch: ticket/req-032-sound-icons
---

# Sound-panel icons

Owner round-two art is integrated through the real icons corpus:

- `media-controls`: shuffle, shuffle-active, repeat, repeat-once, repeat-off.
  Dark-glass surface; inactive `on_surface`, active `primary`; the once/off
  shapes are the owner's baked shapes.
- `settings`: new gear art for the bar (wallpaper, `on_backdrop`).
- `settings-panel.settings`: the Output gear on the audio panel
  (`on_surface`).
- `ROLE-MIGRATION.md`, icons README and tests updated.
- `make validate-icons` and the icon tests pass; no skin retune.

## Live

Installed as assets `v0.21.0`. The runtime rendered
`media-controls-shuffle(-active)`, `repeat`, `repeat-once`, `repeat-off`,
`settings-panel-settings` and the new `status-bar-settings` into
`current/icons`. Terminal-host uses on_surface/primary fills; glass
generation `06799bd0442b...` renders active `#b9c3ff` and inactive `#e3e1e9`.
Bootstrap verify `ok=337 failed=0`.
