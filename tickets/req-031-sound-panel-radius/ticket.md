---
id: req-031
title: "Sound panel feedback: remove the dead muted-note selector"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-031/
branch: ticket/req-031-sound-panel-radius
---

# Remove the dead sound muted-note selector

Owner feedback round 1, item 4: the `Muted — the level is kept.` element and
text are gone, but the `ags` target still groups `.audio-hero-note` with the
dim caption text. Delete the dead selector; no visual change.

## Acceptance

- [x] `.audio-hero-note` absent from `skins/templates/ags.gtk.css.j2`.
- [x] `validate-skins` PASS; `test-skins` 183 passed, 3 skipped;
      `lint` and `gates-ci` clean with **shellcheck 0.11.0** available.
- [x] No skin retune; the target still paints `.audio-settings`/`.tray-surface`
      with `surface.panel` radius.
- [x] Tag `v0.20.2`.
