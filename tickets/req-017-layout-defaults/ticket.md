---
id: req-017
title: "Skins layout defaults: preserve each app's pre-v2 window size"
kind: requirement
status: in-progress
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-017/
branch: ticket/req-017-layout-defaults
---

# Skins layout defaults: preserve each app's pre-v2 window size

## Why

The v0.12.0 v2 conversion derived two `layout.*` blocks from CSS
`min-width`/`min-height` instead of the sizes the apps actually use as window
defaults. The default skin therefore changes behaviour:

- `[groups.layout.ags-icme]` is `960 × 600` (from `style.css:32-33`) but the
  app's pre-v2 default is `1280 × 800`.
- `[groups.layout.ags-wallpaper-selector]` is `920 × 600` (from
  `style.css:16-17`) but the app's pre-v2 default is `960 × 640`.

Evidence: `ags-icme@v0.3.0:ui/EditorWindow.tsx:612-613`
(`default_width={1280}`, `default_height={800}`) and
`ags-wallpaper-selector@v0.3.0:ui/WallpaperSelectorWindow.tsx:600-601`
(`default_width={960}`, `default_height={640}`). The migrated apps now read the
tokens: `ags-icme/ui/EditorWindow.tsx:88-89` feeds `default_width`/`default_height`
at `:619-620`; `ags-wallpaper-selector/ui/WallpaperSelectorWindow.tsx:83-90`
feeds the root size request at `:188`. The CSS minima still exist, but at
`960 × 600` / `920 × 600` they are below the real defaults.

## Requirement

1. Set `layout.ags-icme.root-width` / `root-height` to `1280` / `800` and
   `layout.ags-wallpaper-selector.root-width` / `root-height` to `960` / `640`
   in `glass`, `flat` and `paper`, so the default skin preserves the apps'
   pre-v2 window sizes. Other skins may override them later.
2. Audit every remaining layout block against the apps' pre-migration sources.
   Keep the real TSX literals (`layout.ags.panel-width = 312`,
   `layout.ags.bt-list-spacing = 4`, `layout.ags-clipboard.card-width = 260`,
   `layout.ags-notifications.card-width = 380`). Remove
   `layout.ags.bar-row-height` and `layout.ags.chip-min` because no app reads
   them. Record `layout.ags-capture.panel-width = 560` and
   `layout.ags-btop-studio.left-width` / `right-width = 280` / `320` as
   cleanup candidates: they came from CSS minima, but the apps read them
   today, so they are not changed in this ticket.
3. Update `skins/tests/`, both READMEs and `CHANGELOG.md`; record the audit and
   the cleanup handoff here and in `tickets/INDEX.md`.
4. Tag `v0.12.2`; fast-forward merge to `master`; do not push.

## Acceptance

- [ ] The three manifests carry `icme = 1280/800` and
      `wallpaper-selector = 960/640`, and `bar-row-height` / `chip-min` are
      gone from every manifest.
- [ ] `skins/tests/` pins the new layout defaults and the removed bar tokens.
- [ ] The audit table below is complete and every value names its source.
- [ ] `make validate-skins`, `make test-skins` and `make validate` pass.
- [ ] `v0.12.2` is an annotated tag on the fast-forward-merged commit; the
      branch is not left unmerged; nothing is pushed.

## Audit — every remaining layout block

Read-only app sources: `/home/inumaki/Development/dotfiles/ags-*` at the tags
named below. "Reads now" means the migrated app source in the working tree.

| Layout block (`glass` value) | Pre-v2 source of truth | Reads the token now | Verdict |
| --- | --- | --- | --- |
| `layout.ags.panel-width = 312` | Real TSX literal: `ags-bar@v0.3.0:settings-panel/SettingsPanel.tsx:22` (`width: 312`); v0.4.0 converts it to `skinValue("layout.panel-width", 312)` (`:23`) | `ags-bar/settings-panel/SettingsPanel.tsx:24`, `:33` | **Keep** — 312 is a TSX-owned default, not a CSS minimum |
| `layout.ags.bt-list-spacing = 4` | Real TSX literal: `ags-bar@v0.3.0:components/bluetooth/BluetoothContent.tsx:750` and `:798` (`spacing={4}`); v0.4.0 converts it to `skinValue("layout.bt-list-spacing", 4)` (`:38`) | `ags-bar/components/bluetooth/BluetoothContent.tsx:40`, `:761`, `:809` | **Keep** — 4 is a TSX-owned list rhythm |
| `layout.ags.bar-row-height = 0` (`flat` 28, `paper` 30) | No pre-v2 TSX literal and no CSS source; the v1 manifests carried it as an unused knob | No app source reads it: `rg 'bar-row-height\|chip-min' ags-bar ags-clipboard ags-notifications ags-wallpaper-selector ags-capture-tool ags-icme ags-btop-theme-studio --glob '*.tsx' --glob '*.ts' --glob '*.css' --glob '*.mjs' --glob '*.js'` → no matches (exit 1); only `ags-platform`'s generic key table/tests and bar migration prose mention the name | **Remove** — dead token |
| `layout.ags.chip-min = 0` (`flat` 48, `paper` 52) | Same as above: no pre-v2 TSX literal, no CSS source | Same grep → no app source reads it | **Remove** — dead token |
| `layout.ags-clipboard.card-width = 260` | Real TSX literal: `ags-clipboard@v0.3.0:ui/ItemCard.tsx:179` (`card.set_size_request(260, -1)`; also `v0.2.0:ui/ItemCard.tsx:179`); v0.4.0 converts it to `appearance.value("layout.ags-clipboard.card-width", 260)` | `ags-clipboard/app.tsx:27` | **Keep** — 260 is the app's fixed card request |
| `layout.ags-notifications.card-width = 380` | Real TSX literal: `ags-notifications@v0.3.0:ui/NotificationsWindow.tsx:60` (`const CARD_WIDTH = 380`, used at `:269`, `:400`, `:637`); v0.4.0 converts it to the token | `ags-notifications/app.tsx:75` | **Keep** — 380 is the app's fixed card width |
| `layout.ags-capture.panel-width = 560` | CSS only: `ags-capture-tool@v0.5.0:style.css:793` (`.capture-panel min-width: 560px`) and `:997` (`.settings-page min-width: 560px`). The pre-v2 TSX window sizes itself by measuring the panel (`ui/classic/ClassicWindow.tsx:224-226`), so there is no `560` TSX literal | `ags-capture-tool/app.tsx:50`; `ui/classic/SettingsPage.tsx:344` (`widthRequest={panelWidth.peek()}`) | **Cleanup candidate** — keep 560 now to preserve current layout; follow-up decides whether a CSS-derived panel width belongs in a skin token |
| `layout.ags-btop-studio.left-width = 280` | CSS only: `ags-btop-theme-studio@v0.3.0:style.css:42` (`.studio-left-scroll min-width: 280px`); no pre-v2 TSX literal | `ags-btop-theme-studio/ui/StudioWindow.tsx:197`, `:371` (`leftScroll.set_size_request`) | **Cleanup candidate** — keep 280 now; follow-up decides whether a CSS-derived rail width belongs in a skin token |
| `layout.ags-btop-studio.right-width = 320` | CSS only: `ags-btop-theme-studio@v0.3.0:style.css:241` (`.studio-right min-width: 320px`); no pre-v2 TSX literal | `ags-btop-theme-studio/ui/StudioWindow.tsx:198`, `:784` (`right.set_size_request`) | **Cleanup candidate** — keep 320 now; follow-up decides whether a CSS-derived rail width belongs in a skin token |
| `layout.ags-wallpaper-selector.root-width = 920` | CSS minimum `ags-wallpaper-selector@v0.3.0:style.css:16` (`min-width: 920px`), but the app's pre-v2 window default is the TSX literal `960` (`ui/WallpaperSelectorWindow.tsx:600`) | `ags-wallpaper-selector/ui/WallpaperSelectorWindow.tsx:83-86`, `:188` | **Fix to 960** — default window size, not the CSS minimum |
| `layout.ags-wallpaper-selector.root-height = 600` | CSS minimum `:17` (`min-height: 600px`), but the app's pre-v2 window default is `640` (`ui/WallpaperSelectorWindow.tsx:601`) | `ags-wallpaper-selector/ui/WallpaperSelectorWindow.tsx:87-90`, `:188` | **Fix to 640** — default window size, not the CSS minimum |
| `layout.ags-icme.root-width = 960` | CSS minimum `ags-icme@v0.3.0:style.css:32` (`min-width: 960px`), but the app's pre-v2 window default is the TSX literal `1280` (`ui/EditorWindow.tsx:612`) | `ags-icme/ui/EditorWindow.tsx:88`, `:619` | **Fix to 1280** — default window size, not the CSS minimum |
| `layout.ags-icme.root-height = 600` | CSS minimum `:33` (`min-height: 600px`), but the app's pre-v2 window default is `800` (`ui/EditorWindow.tsx:613`) | `ags-icme/ui/EditorWindow.tsx:89`, `:620` | **Fix to 800** — default window size, not the CSS minimum |

## Cleanup handoff

- **`ags-capture.panel-width` (560)** and **`ags-btop-studio.left/right-width`
  (280/320)** are kept as-is because the migrated apps read them today
  (`app.tsx:50` / `SettingsPage.tsx:344`; `StudioWindow.tsx:197-198`, `:371`,
  `:784`). They are cleanup candidates because their only pre-v2 source was a
  CSS minimum, not a TSX literal. A follow-up should decide whether these
  values stay skin tokens (an authored metric) or move back to TSX literals;
  changing them here would alter live layout without a pre-v2 default to
  preserve.
- **Consumer follow-up (outside this repo):** the migrated app fallbacks still
  name the CSS minima (`ags-icme/ui/EditorWindow.tsx:88-89` = 960/600,
  `ags-wallpaper-selector/ui/WallpaperSelectorWindow.tsx:83-90` = 920/600).
  With `v0.12.2` the default skin supplies 1280/800 and 960/640, but the
  fallbacks should be aligned in the app repositories so a missing appearance
  generation does not reintroduce the shrink.

## Evidence / Verify

- Evidence: the pre-v2 TSX defaults and the CSS minima are cited per row above;
  the retired bar tokens have no reader in any app source (grep exit 1).
- Verify: `make validate-skins`, `make test-skins`, `make validate`;
  `git cat-file -t v0.12.2`; `git merge-base --is-ancestor
  ticket/req-017-layout-defaults master`.
