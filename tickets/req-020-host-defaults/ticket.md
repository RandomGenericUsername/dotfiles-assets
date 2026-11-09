---
id: req-020
title: "Skins host defaults: opt-in [host] policy and contracts v0.9.0 re-vendor"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-020/
branch: ticket/req-020-host-defaults
---

# Skins host defaults: opt-in `[host]` policy and contracts `v0.9.0` re-vendor

## Why

`contracts v0.9.0` adds the optional per-skin `[host]` policy: a skin may
delegate only `surface.panel.radius` and `surface.panel.border-width` to the
live compositor, with `mode override > host > skin fallback` precedence. The
assets class owns the authored manifests and the vendored canonical schemas,
so it must adopt that policy for `glass`/`paper` and re-vendor the `v0.9.0`
schema bytes. Runtime, composition, provisioning and apps are deliberately
out of scope.

## Requirement

1. **Re-vendor the canonical contract.** Copy the appearance and generation
   schemas from `contracts v0.9.0` (peeled commit
   `5c9fd615cae8d6596799bbafaeea93a05b3c3c11`) into `skins/contracts/`; update
   `skins/contracts/PIN` tag/source-commit/sha256 entries and
   `skins/schema.json` `canonical.tag`/paths/vendored paths. The generation
   manifest schema is vendored for byte parity; this class still validates
   skin/appearance documents, not generations.
2. **Opt in only `glass` and `paper`.** Add:
   ```toml
   [host]
   inherit = ["surface.panel.radius", "surface.panel.border-width"]
   fallback = "skin"
   ```
   `terminal` and `flat` get an explicit comment that they opt out; they carry
   no `[host]` block.
3. **Enforce the allowlist in the stdlib gate.** Extend
   `scripts/validate-skins.py` for `items`, `minItems` and `uniqueItems` so
   the host `inherit` enum/minimum/uniqueness is actually enforced. Keep the
   validator stdlib-only.
4. **Fixtures/tests.** Positive host manifest plus negative empty/duplicate/
   unknown inherit, bad fallback and extra key. Existing no-host manifests must
   remain valid. Preserve the v0.14.0 wlogout template and exact
   `required_targets` gate.
5. **Docs/changelog/catalog.** Document `[host]` as a policy object, not a
   token group; precedence, fallback and hash churn; update `skins/README.md`,
   root `README.md`, `catalog.yaml`, `CHANGELOG.md` and `skins/schema.json`
   status.
6. **Release.** `v0.15.0`, annotated tag, fast-forward merge to `master`,
   push `master` + tag, publish the GitHub Release notes.

## Acceptance

- [ ] `skins/contracts/` is byte-identical to the `contracts v0.9.0` appearance
      and generation schema set; PIN hashes and `source-commit` agree; the
      local schema names `canonical.tag = v0.9.0`.
- [ ] `glass` and `paper` carry the exact `[host]` block; `terminal` and
      `flat` carry no host block and explicitly document the opt-out.
- [ ] The stdlib validator enforces `items`, `minItems`, `uniqueItems`; host
      positive/negative fixtures pass/fail as named.
- [ ] Existing no-host manifests remain valid; wlogout remains a required
      target and its template is unchanged.
- [ ] Re-vendoring and the manifest policy leave all eight AGS + wlogout
      targets and every resolved `tokens.json` valid.
- [ ] `make validate-skins`, `make test-skins`, `make lint` and
      `make gates-ci` pass.
- [ ] `v0.15.0` is an annotated tag on the fast-forward-merged commit;
      `master` and the tag are pushed; the GitHub Release is published.

## Evidence

- Contract release: `contracts v0.9.0`, tag object
  `c3b1cc7d3fef36042b00d43ae29e2f80087cb184`, peeled commit
  `5c9fd615cae8d6596799bbafaeea93a05b3c3c11`;
  `contracts/schemas/appearance-manifest.schema.json` adds
  `definitions.hostPolicy`; `contracts/schemas/generation-manifest.schema.json`
  adds `definitions.host` and `intent.host`.
- Design/criteria: `dotfiles-v3/docs/109-hyprland-host-defaults.md` H-1.5 and
  `dotfiles-v3/docs/epics/SKIN-CONSUMERS.md` sequencing.
- Preserve wlogout: `skins/templates/wlogout.gtk.css.j2` and
  `skins/schema.json` `frozen.required_targets` are unchanged by this slice.

## Verification

Commands run from the worktree root (`.worktrees/req-020/`, branch
`ticket/req-020-host-defaults`, base `v0.14.0` + release-record docs commit
`24aa815`). Filled after implementation.

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | pending |
| Skins fixtures | `make test-skins` | pending |
| Lint | `make lint` | pending |
| CI gate set | `make gates-ci` | pending |
| PIN/schema tag parity | `grep -E 'contracts=|source-commit=' skins/contracts/PIN` | pending |

### Commits

| Commit | Subject |
| --- | --- |
| pending | `docs(req-020): plan the host-default skin policy` |
| pending | `chore(req-020): start — record worktree/branch, move to in-progress` |
| pending | `feat(req-020): adopt the host-default skin policy` |
| pending | `chore(req-020): release v0.15.0` |

### Status

**Proposed.** No runtime, composition, provisioning, app or live state change
is in this slice.

## Downstream pins (not part of this slice)

- `dotfiles-runtime v1.1.0` consumes `contracts v0.9.0` and resolves the
  policy at converge time.
- `dotfiles-v3 v0.1.56` pins assets `v0.15.0`, runtime `v1.1.0` and contracts
  `v0.9.0`.
- No provisioning or app tag is expected.

## Non-goals

- No runtime adapter/resolver/hash/doctor/GC code.
- No composition, provisioning, app or live-state change.
- No host mapping for gaps, padding, type, colours or structure.
- No Phase 2/3 host mappings or socket2 watcher.
