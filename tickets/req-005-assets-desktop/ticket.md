---
id: REQ-005
title: "S4 assets cut: desktop class, TryExec + requires/optional contract, v0.5.0"
kind: requirement
status: done
size: M
lane: bmad-advisory
links:
  openspec: assets-catalog
  bmad: none
worktree: .worktrees/s4/
branch: ticket/s4-assets-desktop
children: []
---

# S4 assets cut: `desktop` class, `TryExec` + `requires`/`optional`, `v0.5.0`

## Requirement

Land the last corpus class in `dotfiles-assets`: six `.desktop` entries and `toggle-touchpad`,
byte-identical from the consumer, plus the one edit layer 1 needs (`TryExec=`) and the class
contract `desktop/desktop.yaml` (`requires`/`optional` per entry). Add `make validate-desktop` as
spine AD-10 **layer 1** and wire it into `gates` + CI parity. Cut `v0.5.0`; the consumer rewires
`compositor_configs`, adds deploy-time resolution (layer 2) and verify assertions (layer 3), then
deletes `dotfiles/applications/` and `dotfiles/scripts/` in its own commits.

## Acceptance

- [x] Six entries copied to `desktop/applications/`; `toggle-touchpad` to `desktop/scripts/` with
      mode `0755` preserved (`stat -c %a` → `755`, `cmp` → rc 0 against the source).
- [x] Every entry carries `TryExec=` naming the binary its `Exec` launches (`antigravity-ide`,
      `code`, `devin-desktop`, `kitty` ×2, `tidal-hifi`). Each entry differs from its source by
      exactly one added line; everything else is the consumer's byte.
- [x] `desktop/desktop.yaml`: `schema_major: 1`, one record per entry, exactly
      `{file, requires, optional}`; requires tracks `Exec` argv[0] (6 names), optional the two
      kitty-hosted CLI payloads (`codex`, `copilot`).
- [x] `make validate-desktop` (layer 1) is a `GATES` member with its own CI job and a real
      `shellcheck` run; `make ci-gates-parity` reports `GATES (7)` and `workflow jobs (8)` with the
      CI-only job declared.
- [x] The gate is not vacuous: a bogus `Exec` fails non-zero naming `code.desktop` and
      `definitely-not-installed`; so do a missing `TryExec`, a dropped contract record, a
      non-executable script, an invented `optional` name and unsupported YAML (evidence below).
- [x] `catalog.yaml` declares `desktop` schema-bearing (`desktop/desktop.yaml`, `schema_major: 1`)
      and `validate-catalog.py` reads a YAML contract through the same strict subset as JSON, with
      sequence-of-mappings items added for the record list.
- [x] `desktop/README.md` documents the three layers, the `TryExec` rationale, the
      `requires`/`optional` semantics, the scope boundary (launcher wrappers stay in `cli_tools`)
      and the vacuity proof.
- [x] The openspec spec gains the desktop requirement with executable acceptance commands.
- [x] `make gates`, `make gates-ci` and `make hermetic` exit 0 (worktree and a fresh anonymous
      clone); `openspec validate --specs` exit 0.
- [ ] Annotated `v0.5.0` pushed and anonymously fetchable (tag object + peeled commit recorded);
      GitHub Release published with notes and no assets; CI green on `master`.

## Evidence

- Byte identity: `cmp desktop/scripts/toggle-touchpad <consumer>/dotfiles/scripts/toggle-touchpad`
  → rc 0, sha256 `d1a945367387015ed1d89d46ac213e40f45a0296c40d0bb6f31b02b40a69e6c7` on both sides;
  `stat -c '%a'` → `755`. Per entry, `diff <(grep -v '^TryExec=' <imported>) <source>` → rc 0 and
  `git diff --numstat` → `+1 -0` (the added `TryExec=` line only).
- `make validate-desktop` → rc 0: `entries=6 with_TryExec=6 contract_records=6 requires=6
  optional=2 scripts=1`, `shellcheck -> 1 script(s) clean`, `PASS`.
- Vacuity / negative proofs (each mutated then restored; the clean run returns rc 0):
  - `Exec=definitely-not-installed --flag %F` → rc 1, names `code.desktop`, the binary and its
    declared `requires ['code']`; also flags the `TryExec`/`Exec` disagreement.
  - `TryExec=` line removed → rc 1, "missing or empty TryExec".
  - `devin-desktop.desktop` record removed from the contract → rc 1, "no record in
    desktop/desktop.yaml".
  - `chmod 0644 desktop/scripts/toggle-touchpad` → rc 1, "not executable (mode 0644)".
  - `optional: [codex-cli]` (invented) → rc 1, "does not occur in this entry's Exec line
    (['kitty', '--title', 'OpenAI Codex CLI', 'codex'])".
  - `optional: [code]` (flow collection) → rc 1, "flow collections other than `[]`/`{}` are not
    supported".
- `make gates` / `make gates-ci` → rc 0 in the worktree; `make hermetic` → rc 0 from a foreign cwd
  with empty HOME/XDG dirs. `make ci-gates-parity` → rc 0 (`GATES (7)` = workflow jobs minus the
  declared CI-only `ci-gates-parity`).
- `openspec validate --specs` → rc 0, 1 passed; two >500-character requirement WARNINGs (one
  carried from the templates requirement, one on the new desktop requirement) — warnings, not
  failures.
