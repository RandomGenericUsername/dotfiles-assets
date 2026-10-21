---
id: REQ-003
title: "S2 assets cut: configs static corpus, v0.3.0"
kind: requirement
status: in-progress
size: M
lane: bmad-advisory
links:
  openspec: assets-catalog
  bmad: none
worktree: .worktrees/s2/
branch: ticket/s2-configs-to-assets
children: []
---

# S2 assets cut: configs static corpus, `v0.3.0`

## Requirement

Land the static config corpus in `dotfiles-assets`: 13 Hyprland Lua files, `hyprpaper/hyprpaper.conf`,
`rofi/launcher/config.rasi`, 8 Neovim files, `starship/starship.toml` and `wlogout/layout` (25 files),
imported byte-for-byte. Document the per-file boundary (static config here, Jinja sources in
`templates/` from v0.4.0, rendered output and mutable preference never assets), cut `v0.3.0`, and let
`dotfiles-v3` rewire its two roles and delete the in-tree copy in a separate commit there.

## Acceptance

- [ ] 25 files imported verbatim; `diff -r` exit 0 for hypr, hyprpaper, rofi, nvim, starship and
      `diff` exit 0 for `wlogout/layout` (run before any consumer deletion).
- [ ] `zsh/.zshrc.j2`, `wlogout/style.css.tpl` and `btop/*` are **not** copied: templates class and
      mutable state respectively.
- [ ] `configs/README.md` documents the boundary, the wlogout per-file split and the exclusions;
      `catalog.yaml` declares the six subdirectories and the real contents.
- [ ] The openspec spec states the boundary with executable acceptance commands; the CHANGELOG
      records v0.3.0 (and fixes the v0.2.0 heading left under `[Unreleased]`).
- [ ] `make gates`, `make gates-ci` and `make hermetic` exit 0 on a fresh clone.
- [ ] Annotated `v0.3.0` pushed and anonymously fetchable (tag object + peeled commit recorded
      below); GitHub Release published with notes and no assets; CI green on `master`.

## Evidence

Filled in after the tag and the CI run.
