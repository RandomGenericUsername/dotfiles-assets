---
id: req-038
title: "Reload the generated Neovim palette on SIGUSR1"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-038/
branch: ticket/req-038-nvim-signal-reload
---

# Reload the generated Neovim palette on SIGUSR1

## Why

`v0.21.8` loads `dotfiles-palette` once at startup. After the runtime/provisioning
seed republishes the module, a running Neovim keeps the cached palette until it
is restarted. A signal (and a user command for the same path) lets the seed
reapply colors without a polling timer or a host path in the corpus.

## Requirement

1. Add `reload_palette()` to `configs/nvim/lua/config/autocmds.lua`: clear
   `package.loaded["dotfiles-palette"]`, `pcall(require, "dotfiles-palette")`,
   call `palette.load()` when present, fire
   `vim.api.nvim_exec_autocmds("ColorScheme", { pattern = "dotfiles" })`, then
   `vim.cmd.redraw()`.
2. A missing module (fresh host before the first seed) no-ops without error.
3. Register a `Signal` autocmd on `SIGUSR1` and a `DotfilesColorsReload` user
   command, both calling `reload_palette`.
4. No polling timer; no host path; no package install/apply.
5. Add an Unreleased changelog entry; no release/tag/pin bump.

## Acceptance

- [x] `:DotfilesColorsReload` reapplies a palette module rewritten after first load.
- [x] `SIGUSR1` reapplies a palette module rewritten after first load.
- [x] Missing-module path returns without error and fires no `ColorScheme` event.
- [x] `make gates` PASS.
- [ ] No tag/release/pin/apply; ticket closed by the parent session.

## Evidence

- Module contract from req-036: `configs/nvim/lua/plugins/lazyvim.lua` requires
  `dotfiles-palette` and calls `palette.load()` when present.
- Verification (isolated XDG dirs, host `nvim` v0.12.6):
  `bash /tmp/opencode/req-038-verify.sh` → `ALL VERIFICATION PASSED`
  (`command: first=v1 second=v2 colorscheme=v2`, `signal: initial=v1 result=v2`,
  `missing: colorscheme-state exists=no`).
- `make gates` → exit 0; every class `PASS`, `hermetic: PASS -- the corpus
  validates with no HOME, no XDG state and a foreign cwd`.


- Release: v0.21.9
