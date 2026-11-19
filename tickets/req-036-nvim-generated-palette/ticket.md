---
id: req-036
title: "Load the generated Neovim palette with a Catppuccin fallback"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-036/
branch: ticket/req-036-nvim-generated-palette
---

# Load the generated Neovim palette with a Catppuccin fallback

## Requirement

1. Change `configs/nvim/lua/plugins/lazyvim.lua` to pass a `colorscheme`
   function to LazyVim.
2. The function `pcall(require, "dotfiles-palette")`; when the module and its
   `load()` exist, call it. Otherwise `vim.cmd.colorscheme("catppuccin")`.
3. No host path in the corpus; the module name is the only contract.
4. Add a changelog entry; no release/tag/pin bump.

## Acceptance

- [x] LazyVim loads the generated palette when the module exists.
- [x] Catppuccin is the fallback when the module/pointer is absent.
- [x] `make gates` PASS.
- [x] No tag/release/pin bump.

## Evidence

- Module: `dotfiles-v3` REQ-123 / provisioning link
  `config/nvim/lua/dotfiles-palette.lua -> current/palette/colors.nvim.lua`.
- LazyVim accepts a function: `LazyVim/lua/lazyvim/config/init.lua:11-15,250-263`.
