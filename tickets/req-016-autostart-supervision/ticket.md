---
id: req-016
title: "Hypr autostart must not launch the systemd-owned always-on AGS apps"
kind: requirement
status: in-progress
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-016/
branch: ticket/req-016-autostart-supervision
---

# Hypr autostart must not launch the systemd-owned always-on AGS apps

## Why

Provisioning `v0.1.37` supervises the always-on AGS apps with systemd **user**
units: `dotfiles-ags-bar.service` and `dotfiles-ags-notifications.service`. The
assets-owned `configs/hypr/autostart.lua` still launches the same two instances
through `ags-run-locked`, so two launch paths exist for one process. The
wrapper's already-running pre-check makes the autostart line a no-op today, but
the ownership boundary must be explicit: systemd owns always-on AGS, Hypr
autostart owns the launch-on-login overlays only.

Evidence: `configs/hypr/autostart.lua:28` launches `--expect-instance ags` and
`:44` launches `--expect-instance notifications`; provisioning `v0.1.37` adds
`dotfiles-ags-bar.service` / `dotfiles-ags-notifications.service` (separate
repository, not changed here).

## Requirement

1. Remove the `ags` (bar) and `notifications` launcher entries from
   `configs/hypr/autostart.lua`, and leave a comment naming the two systemd user
   units as the owner so autostart must not launch them.
2. Keep the remaining autostart entries (`hyprpaper`, reconcile, `capture`,
   polkit, portals, gloview, `clipboard`) unchanged. Do not touch any systemd
   unit — units live in the provisioning repository.
3. Sweep the assets tree for other always-on AGS launch references and correct
   stale ownership claims in `configs/README.md` and the
   `templates/display-manager/hypr-session.j2` header. IPC requests
   (`ags request …`) and launch-on-demand keybinds stay.
4. Add a `validate-configs` regression assertion that rejects an autostart line
   launching the `ags` or `notifications` instance, so a re-add fails a gate.
5. Update `README.md`, `CHANGELOG.md`, `catalog.yaml`, this ticket and
   `tickets/INDEX.md`. Tag `v0.12.1`; fast-forward merge to `master`; do not
   push.

## Acceptance

- [ ] `configs/hypr/autostart.lua` has no `ags-run-locked` line for `ags` or
      `notifications`; the remaining launch lines are byte-identical.
- [ ] The autostart comment names `dotfiles-ags-bar.service` and
      `dotfiles-ags-notifications.service` as the systemd owners.
- [ ] `make validate-configs` fails on a re-added `--expect-instance ags` or
      `notifications` line and passes on the cleaned file.
- [ ] `rg -n 'ags-run-locked' configs` shows only `capture` and `clipboard`.
- [ ] `make validate`, `make validate-configs`, `make gates` pass.
- [ ] `v0.12.1` is an annotated tag on the fast-forward-merged commit; nothing
      is pushed.

## Evidence / Verify

- Evidence: `configs/hypr/autostart.lua` at `v0.12.0` lines 20–44 launch the
  bar and notification instances through the wrapper; provisioning `v0.1.37`
  owns those apps as systemd user units.
- Verify: `make validate-configs`, `make validate`, `make gates`;
  `rg -n 'ags-run-locked' configs/hypr/autostart.lua`; `git cat-file -t v0.12.1`.
