---
id: req-030
title: "Sound panel QA: bare icon controls and one settings surface"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-030/
branch: ticket/req-030-sound-panel-qa
---

# Sound panel QA in the `ags` target

## Requirement

Follow-up to req-028 from the live panel QA:

1. Icon-only sound controls (gear, mute, transport, carousel, read-only level,
   Mixer mute) are **bare**: transparent fill/border, only hover/active state
   paint. Device/route fields, sliders and the switch keep the role paint.
2. The settings popover has one skin surface: the template paints
   `.audio-settings` (panel role); the app resets the native popover chrome.
3. Track artwork is content: `.audio-track-art`/badge styles live here, with
   the app owning layout/geometry.
4. Extend the fixture tests: the sound selector/token coverage includes the
   thumbnail; a positive test proves the icon-only group is bare and the
   device/route fields remain control-painted.
5. Gates: `make validate-skins`, `make test-skins`, `make lint`,
   `make gates-ci` (shellcheck environment gap recorded as before).
6. Tag `v0.20.1`.

## Acceptance

- [x] The icon-only group is bare in the template; fields/sliders keep role
      paint; the thumbnail/badge classes exist.
- [x] `make validate-skins` PASS; `make test-skins` 172 passed, 3 skipped.
- [x] No `surface.window` in the sound section.
- [x] Tag `v0.20.1`.

## Evidence

- Worktree `.worktrees/req-030/`, branch `ticket/req-030-sound-panel-qa`,
  based on `8802b26` (v0.20.0).
- `skins/templates/ags.gtk.css.j2`: bare icon-only group; `.audio-track-art`,
  `.audio-track-art-image`, `.audio-track-art-fallback`, `.audio-track-badge`.
- `skins/tests/test_skins.py`: `.audio-track-art` selector coverage and
  `test_ags_icon_only_sound_controls_are_bare`.
- Live: the configured terminal-host panel shows bare gear/mute/transport;
  device/route fields and sliders stay painted.
