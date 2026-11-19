---
id: req-035
title: "Refresh lazy-lock.json to the resolved LazyVim set"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-035/
branch: ticket/req-035-nvim-lock-refresh
---

# Refresh lazy-lock.json to the resolved LazyVim set

## Why

`v0.21.6` committed a `lazy-lock.json` generated before LazyVim finished
resolving every plugin. On the first real host launch, six plugin commits moved
to the versions LazyVim actually checks out; the resolved lock then stayed
stable across a second `Lazy! sync`. Committing the stale lock would make the
next provision flip those plugins again.

## Requirement

1. Replace `configs/nvim/lazy-lock.json` with the stable resolved lock
   (`sha256 0117667e…`).
2. Add a `0.21.7` changelog entry naming the refreshed lock.
3. No config behavior change: same LazyVim starter, Catppuccin, Snacks, bashls.
4. Tag/release `v0.21.7`.

## Acceptance

- [x] The committed lock equals the host's stable resolved lock.
- [x] `make gates` PASS.
- [x] `v0.21.7` tagged/pushed/released.
- [x] No host apply/install in this ticket.


- Release: https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.21.7
