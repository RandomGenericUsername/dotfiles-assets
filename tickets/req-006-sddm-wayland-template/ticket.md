---
id: REQ-006
title: "SDDM config template carries the Wayland greeter compositor (v0.6.0)"
kind: requirement
status: done
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

- [x] `templates/display-manager/sddm.conf.j2` has a `[Wayland]` section after `[General]` with
      `CompositorCommand=` defaulting to `weston --shell=kiosk`; the existing comments are kept.
- [x] `templates/display-manager/sddm.conf.vars.schema.json` adds
      `display_manager_sddm_compositor_command` as an optional string; `required` still names only
      `display_manager_sddm_display_server`; `additionalProperties: false` and `schema_major: 1`
      stay; no schema `default` keyword is introduced.
- [x] Red proof: with the new validator assertion and the old template, `make validate-templates`
      exits non-zero naming the missing `[Wayland]`; green after the template lands.
- [x] `make validate-templates` asserts the rendered fallback and an explicit override; rendering
      with only the required variable works (dogfood with Jinja2).
- [x] `catalog.yaml`, `README.md`, `templates/README.md` and `CHANGELOG.md` record 24 required /
      1 optional, the optional SDDM compositor, and the `v0.6.0` tag; no consumer destination is
      named and no package/service ownership moves into this repo.
- [x] `make validate`, `make validate-templates`, `make gates`, `make gates-ci`, `make hermetic` and
      `make ci-gates-parity` exit 0 in the worktree; `openspec validate sddm-wayland-template`
      and `openspec validate --specs` exit 0.
- [x] Fresh anonymous clone at `v0.6.0` passes `make gates` and reports the new contract.
- [x] Merge to the default branch only when green; annotated `v0.6.0` is pushed and anonymously
      fetchable; GitHub Release published with notes and no assets; tag is never moved or deleted.
- [x] Ticket closeout carries Evidence:/Verify: lines and `tickets/INDEX.md` is updated in the same
      commit as each status change.

## Evidence

- Red proof: with the assertion added and the template still at its old body, `make
  validate-templates` → **exit 2** (`make` wraps the validator's exit 1):
  `templates/display-manager/sddm.conf.j2: no [Wayland] section -- the rendered config would depend
  on SDDM's implicit 'weston --shell=kiosk' fallback, which stays invisible until a host without
  weston cannot start the greeter`.
- Green: `make validate-templates` → exit 0: `templates=9 schemas=9`, `groups: btop(1)
  display-manager(5) kitty(1) wlogout(1) zsh(1)`, `vars: required=24 optional=1`,
  `templates containing 'default(': 1; defaults on required vars: 0`, `sddm: [Wayland]
  CompositorCommand present (default='weston --shell=kiosk'; optional override asserted)`,
  `sddm deep: renders with the required variable only and with the optional override`, `PASS`.
- Dogfood (`uv run --no-project --with jinja2 python -`): required-only context (only
  `display_manager_sddm_display_server=wayland`) → `[Wayland]` +
  `CompositorCommand=weston --shell=kiosk`; explicit override
  `display_manager_sddm_compositor_command='cage -- /usr/bin/sddm-greeter'` → `CompositorCommand=cage
  -- /usr/bin/sddm-greeter`.
- Deep modes: `uv run --no-project --with jinja2 --with jsonschema python
  scripts/validate-templates.py` → exit 0, `sddm deep: renders …`, `deep: every schema validates
  against the draft 2020-12 metaschema and rejects an undeclared / required-missing instance`.
- `make validate` → exit 0: `tag=v0.6.0`, `classes (5)`, `schema_major (3): icons=1 templates=1
  desktop=1`, `AD-11 absence: 354 files scanned`, `PASS`.
- `make gates` → exit 0 (`GATES_EXIT=0`); `make gates-ci` → exit 0 (`GATES_CI_EXIT=0`);
  `make hermetic` → exit 0 (`HERMETIC_EXIT=0`) with `cwd=/tmp/tmp.cZmWig2VLv/cwd HOME=…/home
  XDG_DATA_HOME=…/xdg-data (empty, foreign)` and `hermetic: PASS`; `make ci-gates-parity` → exit 0
  (`GATES (8)`, `workflow jobs (9)`, `PASS`).
  - Host note: this host has no distro `shellcheck`; the shell half ran through
    `/tmp/opencode/shellcheck-bin/shellcheck` (`uvx --from shellcheck-py`, v0.11.0), the same tool
    the CI runner provides. The Python half and every validator ran without a venv.
- OpenSpec: `openspec validate sddm-wayland-template` → exit 0 before archive; `openspec archive
  sddm-wayland-template --yes` → exit 0 (`assets-catalog: +1 added`, archived as
  `2026-10-26-sddm-wayland-template`); `openspec validate --specs` → exit 0 (1 passed; the two
  pre-existing >500-character WARNINGs remain); `openspec validate --archived` → exit 0 (2 passed).
- Merge: fast-forward `master` `02a4534..60620ac`; annotated tag object
  `ff460db244528ec987d1f396587008382de8b320`, peeled commit
  `60620acab73a98e56b9b4d812ed52283f757062f`; `git cat-file -t v0.6.0` → `tag`;
  `git ls-remote --tags origin 'refs/tags/v0.6.0*'` → exactly the tag object line and its `^{}`
  line.
- CI: [run 40349570724](https://github.com/RandomGenericUsername/dotfiles-assets/actions/runs/40349570724)
  on `60620ac` → **success**, 9/9 jobs (validate, validate-icons, validate-content,
  validate-templates, validate-configs, validate-desktop, lint, hermetic, ci-gates-parity).
- Release: [v0.6.0 — SDDM Wayland compositor](https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.6.0)
  published, notes only, `assets: 0`, not a draft/prerelease, target `master`.
- Fresh anonymous clone: `git clone --branch v0.6.0
  https://github.com/RandomGenericUsername/dotfiles-assets.git /tmp/opencode/assets-v0.6.0-fresh`
  → checked out `60620ac`; `make gates` → exit 0 (`FRESH_GATES_EXIT=0`) with
  `templates=9 schemas=9`, `required=24 optional=1`, `sddm: [Wayland] CompositorCommand present`,
  `sddm deep: renders …`, `hermetic: PASS`; `make ci-gates-parity` → exit 0 (`GATES (8)`,
  `workflow jobs (9)`).
- Verify: `make validate-templates && make validate && make gates && make gates-ci && make hermetic`
  → all exit 0; `grep -A2 '^\[Wayland\]' templates/display-manager/sddm.conf.j2` → the
  `CompositorCommand` line; `python3 scripts/validate-templates.py` → `required=24 optional=1`;
  `git cat-file -t v0.6.0` → `tag`; `gh release view v0.6.0 --json assets` → `[]`.
