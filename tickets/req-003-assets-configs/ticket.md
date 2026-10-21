---
id: REQ-003
title: "S2 assets cut: configs static corpus, v0.3.0/v0.3.1"
kind: requirement
status: done
size: M
lane: bmad-advisory
links:
  openspec: assets-catalog
  bmad: none
worktree: .worktrees/s2/
branch: ticket/s2-configs-to-assets
children: []
---

# S2 assets cut: configs static corpus, `v0.3.0` / `v0.3.1`

## Requirement

Land the static config corpus in `dotfiles-assets`: 13 Hyprland Lua files, `hyprpaper/hyprpaper.conf`,
`rofi/launcher/config.rasi`, 8 Neovim files, `starship/starship.toml` and `wlogout/layout` (25 files),
imported byte-for-byte. Document the per-file boundary (static config here, Jinja sources in
`templates/` from v0.4.0, rendered output and mutable preference never assets), cut `v0.3.0`, and let
`dotfiles-v3` rewire its two roles and delete the in-tree copy in a separate commit there.

## Acceptance

- [x] 25 files imported verbatim; `diff -r` exit 0 for hypr, hyprpaper, rofi, nvim, starship and
      `diff` exit 0 for `wlogout/layout` (run before any consumer deletion); the 25 sha256 values
      match in order on both sides.
- [x] `zsh/.zshrc.j2`, `wlogout/style.css.tpl` and `btop/*` are **not** copied: templates class and
      mutable state respectively.
- [x] `configs/README.md` documents the boundary, the wlogout per-file split and the exclusions;
      `catalog.yaml` declares the six subdirectories and the real contents.
- [x] The openspec spec states the boundary with executable acceptance commands; the CHANGELOG
      records v0.3.0 (and fixes the v0.2.0 heading left under `[Unreleased]`).
- [x] `make gates`, `make gates-ci` and `make hermetic` exit 0 on a fresh clone.
- [x] Annotated `v0.3.0` + `v0.3.1` pushed and anonymously fetchable (tag object + peeled commit
      recorded below); GitHub Releases published with notes and no assets; CI green on `master`.

## Deviation: v0.3.1 (PATCH, documentation only)

`v0.3.0`'s `configs/README.md` claimed "nothing here is rendered". That is false for one file:
`hypr/hyprland.lua:7` carries `{{ compositor_configs_xdg_config_home }}` (the directory its twelve
Lua modules are loaded from) and the consumer renders it on deploy — the file's own header says so.
The corpus bytes were always right; the prose was not. Because a published tag is never moved, the
correction ships as `v0.3.1` (bytes identical to `v0.3.0`, catalog tag updated) and the consumer
pins `v0.3.1`.

The class rule is now stated as **destination + contract** rather than "no braces": `configs/`
deploys 1:1 to a fixed path; `templates/` declares its variables in a sibling
`*.vars.schema.json`. `hyprland.lua` stays in `configs/` because its destination is fixed and it
declares no contract; a `templates/` move would change an addressed path and be a MAJOR change.
The single token is documented, enumerated in the spec, covered by an acceptance grep, and a
scenario now covers a second token.

## Evidence

- Byte identity (before any consumer deletion): `diff -r` over hypr, hyprpaper, rofi, nvim and
  starship → rc 0 each; `diff wlogout/layout` → rc 0; `sha256sum` sequences of all 25 files → equal.
- `make gates` (worktree) → rc 0; fresh anonymous clone at `v0.3.1` (`2ecd7cb`) → `make gates`
  rc 0; `git cat-file -t v0.3.1` → `tag`.
- Boundary check: `grep -rn '{{' configs --exclude=README.md` → exactly
  `configs/hypr/hyprland.lua:7`; no `*.j2`/`*.tpl`, no `active-theme`, no `.zshrc` under `configs/`.
- Tag `v0.3.0`: object `6dd0385a481474de52f96e5e569f5b514552fd0b`, peeled
  `405002a4da6a8900dcf26057b9b223fe99bc6c34`. Release:
  https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.3.0 (notes only).
- Tag `v0.3.1`: object `4359b4f3d62c54fa06c3cb2c9f452252cd11854f`, peeled
  `2ecd7cb2ba4e9a1068a1fe70fc538580013ba747`. Release:
  https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.3.1 (notes only).
- CI: [run 39692979845](https://github.com/RandomGenericUsername/dotfiles-assets/actions/runs/39692979845)
  on `405002a` → success (6/6); [run 39693485641](https://github.com/RandomGenericUsername/dotfiles-assets/actions/runs/39693485641)
  on `2ecd7cb` → success (6/6: validate, validate-icons, validate-content, lint, hermetic,
  ci-gates-parity).
- Consumer: `dotfiles-v3` commits `a3220b80` (rewire) + `7d0ad759` (delete), ff-merged to master;
  runtime evidence recorded there (real v0.3.1 corpus copied byte-identically, gates 6/6).
