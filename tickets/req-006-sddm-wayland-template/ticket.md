---
id: REQ-006
title: "SDDM config template carries the Wayland greeter compositor (v0.6.0)"
kind: requirement
status: in-progress
size: S
lane: 2 — openspec-single (bounded template/schema change)
links:
  openspec: sddm-wayland-template
  bmad: none
worktree: .worktrees/req-006/
branch: ticket/req-006-sddm-wayland-template
children: []
---

# SDDM config template carries the Wayland greeter compositor (`v0.6.0`)

## Requirement

`templates/display-manager/sddm.conf.j2` SHALL render an explicit `[Wayland]` section with
`CompositorCommand={{ display_manager_sddm_compositor_command | default('weston --shell=kiosk') }}`
so the rendered SDDM config never relies on SDDM's implicit fallback. The sibling vars schema SHALL
declare `display_manager_sddm_compositor_command` as an **optional** string (no schema `default`);
`schema_major` SHALL stay `1` because the addition is optional and additive. `make validate-templates`
SHALL assert the rendered body contains `[Wayland]` and `CompositorCommand`, including the
`weston --shell=kiosk` fallback and an explicit override. Installing `weston`, passing the role var
and bumping the consumer pin remain the consumer's Wave 2 work.

## Baseline evidence (host, 2026-10-26, before this change)

- `cat /etc/sddm.conf.d/10-dotfiles.conf` → `DisplayServer=wayland` and
  `GreeterEnvironment=QT_QPA_PLATFORM=wayland`, but **no `[Wayland]` section**.
- `command -v weston` → exit 1 (not installed).
- `journalctl -b -u sddm | grep -c "falling back to DisplayServer=x11-user"` → `4`.
- `journalctl -b -u sddm | grep -c "Session started false"` → `3`.

## Triage

`/triage` → `kind: requirement`; `lane: 2 — openspec-single`. One bounded contract addition
(template body + optional schema var + validator assertion + catalog/docs), fully specified by the
plan, no architectural unknowns; it fits one proposal/spec/design/tasks slice. Evidence:
`/home/inumaki/.opencode/plan/03-assets-req-006-sddm-wayland-template.md` §2–§6. Verify:
`sed -n '23,62p' /home/inumaki/.opencode/plan/03-assets-req-006-sddm-wayland-template.md`.
Worktree created with `bash scripts/worktree-guard.sh create req-006 sddm-wayland-template` after
`bash scripts/worktree-guard.sh check-clean` → exit 0.

## Acceptance

- [ ] `templates/display-manager/sddm.conf.j2` has a `[Wayland]` section after `[General]` with
      `CompositorCommand=` defaulting to `weston --shell=kiosk`; the existing comments are kept.
- [ ] `templates/display-manager/sddm.conf.vars.schema.json` adds
      `display_manager_sddm_compositor_command` as an optional string; `required` still names only
      `display_manager_sddm_display_server`; `additionalProperties: false` and `schema_major: 1`
      stay; no schema `default` keyword is introduced.
- [ ] Red proof: with the new validator assertion and the old template, `make validate-templates`
      exits non-zero naming the missing `[Wayland]`; green after the template lands.
- [ ] `make validate-templates` asserts the rendered fallback and an explicit override; rendering
      with only the required variable works (dogfood with Jinja2).
- [ ] `catalog.yaml`, `README.md`, `templates/README.md` and `CHANGELOG.md` record 24 required /
      1 optional, the optional SDDM compositor, and the `v0.6.0` tag; no consumer destination is
      named and no package/service ownership moves into this repo.
- [ ] `make validate`, `make validate-templates`, `make gates`, `make gates-ci`, `make hermetic` and
      `make ci-gates-parity` exit 0 in the worktree; `openspec validate sddm-wayland-template`
      and `openspec validate --specs` exit 0.
- [ ] Fresh anonymous clone at `v0.6.0` passes `make gates` and reports the new contract.
- [ ] Merge to the default branch only when green; annotated `v0.6.0` is pushed and anonymously
      fetchable; GitHub Release published with notes and no assets; tag is never moved or deleted.
- [ ] Ticket closeout carries Evidence:/Verify: lines and `tickets/INDEX.md` is updated in the same
      commit as each status change.

## Evidence

- Pending implementation; red/green and gate outputs land in the closeout commit.
