---
id: req-039
title: "Neovim consumes the generated skin appearance for editor chrome"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-039/
branch: ticket/req-039-nvim-appearance-loader
---

# Neovim consumes the generated skin appearance for editor chrome

## Why

`v0.21.9` loads the generated wallpaper palette, but the editor cannot tell a
translucent `glass` skin from zero-chrome `flat` or opaque `terminal`. The
active generation already publishes its resolved appearance document
(`current/appearance/tokens.json`, exposed by provisioning as
`config/nvim/lua/dotfiles-appearance.json`). Reading it lets the editor follow
the selected skin for chrome only, while syntax/LSP/diagnostics stay
palette-owned. Design: `dotfiles-v3/.worktrees/REQ-124/docs/116-neovim-skin-appearance.md`.

## Requirement

1. Add `configs/nvim/lua/dotfiles-appearance.lua`:
   - read and `vim.json.decode` `stdpath("config")/lua/dotfiles-appearance.json`
     (no host path in the corpus);
   - `load()` returns `false` (never raises) on absent/malformed JSON,
     `version ~= 2`, missing `surface.window`, or missing palette role source;
   - `resolve(tokens, roles)` supports only `@role`, `alpha(@role, n)`,
     `transparent`, `none` and records provenance plus per-token degradation;
   - use the full palette role map (`M.roles`) when present, otherwise the
     documented surface-role fallbacks (never a guessed hex);
   - `apply()` overlays only the §5.2 chrome groups (Normal background,
     NormalFloat/FloatBorder/FloatTitle, Pmenu*, StatusLine*, TabLine*,
     WinSeparator/VertSplit, Visual, CursorLine(+Nr), LineNr, SignColumn,
     Folded, ColorColumn, `winborder`); syntax/LSP/diagnostics untouched;
   - `reload()` drops state, re-reads the JSON and re-applies.
2. Call `appearance.apply()` after `palette.load()` in
   `lua/plugins/lazyvim.lua`.
3. Extend `reload_palette()` in `lua/config/autocmds.lua` so `SIGUSR1` and
   `:DotfilesColorsReload` reload the palette and then appearance; a missing
   document is palette-only and fires no `ColorScheme` event.
4. Check in `glass`/`flat`/`terminal` token fixtures, one fixed role map and
   `expected-chrome.json`; add a headless verifier that asserts resolved chrome,
   provenance, `winborder` and the missing/malformed/degraded paths.
5. No contracts/runtime/provisioning/tpr change; no tag, release, pin bump,
   package install or host apply.

## Acceptance

- [x] `resolve()` produces different chrome from the same role map for
      `glass`, `flat` and `terminal` (fixtures + headless assertions).
- [x] `winborder` is `single` for glass/terminal and `none` for flat.
- [x] Missing, malformed, wrong-version and missing-window documents return
      `false` without raising; an absent pointer leaves palette-only.
- [x] A single bad token degrades that group only; a missing full role map uses
      the documented surface alias and records the degradation.
- [x] `apply()` reads the JSON through `stdpath("config")` and sets the chrome
      groups in Neovim's real highlight table under an isolated XDG tree.
- [x] `make gates` PASS.
- [ ] Release/tag/pin bump left to the parent session; ticket stays
      `in-progress`.

## Evidence

Design contract: `dotfiles-v3/.worktrees/REQ-124/docs/116-neovim-skin-appearance.md`
§4.2 (loader), §4.3 (fallback), §4.4 (live reload), §5.2 (chrome map),
§5.3 (paint resolver), §6.2 (headless verification).

Fixtures were resolved from the checked-in manifests through
`scripts/validate-skins.py::_resolve_manifest` with the §6.1 host snapshot
(`window radius 8 / border 2`, `panel radius 8 / border 2`,
`card/control/cell radius 4`) and `dark` mode. `expected-chrome.json` was
computed independently of the Lua resolver (Python sRGB composite), so the
assertions cross-check the implementation rather than restating it.

Verification (host `nvim` v0.12.6, no UI, isolated XDG trees):

```bash
bash tests/nvim-appearance/verify.sh
```

→ exit 0; observed:

```text
resolve glass    normal=#18181e float=#1b1b21 statusline=#18181f winborder=single
resolve flat     normal=#101014 float=#101014 statusline=#101014 winborder=none
resolve terminal normal=#18181f float=#1e1e26 statusline=#18181f winborder=single
bad token    -> float_bg falls back to Normal, normal_bg preserved
role alias   -> surface_container_lowest -> surface_container_low
fallbacks    -> missing/malformed/wrong-version/missing-window all return false
apply        -> Normal=#18181e NormalFloat=#1b1b21 StatusLine=#18181f Visual=#2b4a8a winborder=single
reload       -> SIGUSR1 glass/terminal, command flat (Normal=#101014)
MISSING POINTER PASSED
NVIM APPEARANCE VERIFICATION PASSED
```

`make gates` → exit 0 (see the commit for the run).
