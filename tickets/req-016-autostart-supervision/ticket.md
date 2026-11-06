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

- [x] `configs/hypr/autostart.lua` has no `ags-run-locked` line for `ags` or
      `notifications`; the remaining launch lines are byte-identical.
- [x] The autostart comment names `dotfiles-ags-bar.service` and
      `dotfiles-ags-notifications.service` as the systemd owners.
- [x] `make validate-configs` fails on a re-added `--expect-instance ags` or
      `notifications` line and passes on the cleaned file.
- [x] `rg -n 'ags-run-locked' configs` shows only `capture` and `clipboard`.
- [x] `make validate`, `make validate-configs`, `make gates` pass.
- [x] `v0.12.1` is an annotated tag on the fast-forward-merged commit; nothing
      is pushed.

## Evidence / Verify

- Evidence: `configs/hypr/autostart.lua` at `v0.12.0` lines 20–44 launch the
  bar and notification instances through the wrapper; provisioning `v0.1.37`
  owns those apps as systemd user units.
- Verify: `make validate-configs`, `make validate`, `make gates`;
  `rg -n 'ags-run-locked' configs/hypr/autostart.lua`; `git cat-file -t v0.12.1`.

## Outcome (2026-11-06)

**Worktree:** `.worktrees/req-016/`
**Branch:** `ticket/req-016-autostart-supervision`
**Commits:** `070bc41` (ticket + INDEX plan), `df906b5` (autostart, validator,
docs, tag/catalog bump).
**Merge:** fast-forward into `master`.
**Tag:** `v0.12.1` (annotated) on the merged branch head; not pushed.

### Delivered

| Path | What changed |
| --- | --- |
| `configs/hypr/autostart.lua` | bar (`ags`) and `notifications` launch lines removed; comment names the two systemd user units; `capture`/`clipboard` lines unchanged |
| `scripts/validate-configs.py` | rejects an autostart launch of the `ags` or `notifications` instance, naming the owning systemd unit |
| `configs/README.md` | ownership table marks the bar/notifications as systemd units; wrapper section scoped to the overlays |
| `templates/display-manager/hypr-session.j2` | header no longer claims the bar starts from the Hyprland config |
| `README.md`, `CHANGELOG.md`, `catalog.yaml` | `v0.12.1` release note and tag |

### Evidence — commands and exact results

| Command | Result |
| --- | --- |
| `make validate-configs` | **PASS** — `autostart leaves the systemd-owned AGS instances to provisioning` |
| negative check (temporary re-added `--expect-instance ags`) | **FAIL** — `configs/hypr/autostart.lua:57: autostart launches always-on AGS instance 'ags'; provisioning owns it as dotfiles-ags-bar.service` |
| `make validate` | **PASS** — `tag=v0.12.1`, six classes, 406 files scanned |
| `make gates` | **PASS** — every gate plus hermetic; `shellcheck -> 1 script(s) clean` |
| `rg -n 'ags-run-locked' configs` | only `autostart.lua` lines for `capture` and `clipboard` |

The host has no `shellcheck`; the gate run used a temporary ShellCheck 0.10.0
binary from `/tmp/opencode/bin` on `PATH`. Without it, `validate-desktop` (and
therefore `gates`) fails with its documented "shellcheck is not installed"
message — an environment gap, not a corpus failure.
