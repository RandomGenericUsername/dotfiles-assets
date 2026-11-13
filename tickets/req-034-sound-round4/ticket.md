---
id: req-034
title: "Sound panel round four: app-owned artwork, per-player identity"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-034/
branch: ticket/req-034-sound-round4
---

# Sound panel round four

- The skin no longer paints any artwork tile. `.audio-track-art`,
  `.audio-artwork.audio-app-tile`, `.audio-strip-art.audio-app-tile`, the app
  tile container/image/badge paint and their skin radii are gone. The app owns
  a transparent, borderless, shadowless container; only the thumbnail/app
  fallback is visible. Fallback ink/type remains skin-owned.
- Added text-only `.audio-player-identity` / `.audio-tray-player-identity`
  styles for the per-player MPRIS identity. No artwork paint is reintroduced.
- Gate: `test_ags_artwork_tiles_are_app_owned_not_skin_painted` rejects the
  artwork tile selectors and keeps the fallback text rules.
