---
id: req-040
title: "Use absolute line numbers in Neovim"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-040/
branch: ticket/req-040-absolute-line-numbers
---

# Use absolute line numbers

## Why

LazyVim defaults to `relativenumber=true`, which shows 11…1 above and 1…26
below the cursor. The owner wants absolute line numbers.

## Requirement

1. `configs/nvim/lua/config/options.lua` sets `number=true` and
   `relativenumber=false`.
2. No other option or skin behavior changes.
3. `make gates` passes.
4. Release only when authorized.

## Acceptance

- [x] Absolute line numbers configured.
- [x] `make gates` PASS.
- [ ] Release/tag (pending green).
