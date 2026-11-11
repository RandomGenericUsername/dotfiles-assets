---
id: req-025
title: "Host rounding guards: inner-radius rejection and outer-only render probe"
kind: requirement
status: in-progress
lane: 2 — bounded validation/docs
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-025/
branch: ticket/req-025-host-radius-guards
---

# Host rounding guards: inner-radius rejection and outer-only render probe

## Why

`dotfiles-v3/docs/111-host-radius-granularity.md` picks **Option C: outer-only**
for Hyprland `decoration:rounding`. The host scalar is a toplevel window hint;
it must not reach inner card/control/cell/pill radii. `surface.panel` is the
canonical outer-surface role and stays the only host-inheritable geometry
(`surface.panel.radius`, `surface.panel.border-width`). This slice is Phase 1
from that document: asset-side guards and documentation only (`HG-1.3`,
`HG-1.4`, `HG-1.5`).

## Requirement

1. Add `skins/tests/fixtures/invalid/host-inner-radius.toml` with an inner
   radius path in `[host].inherit` and assert `validate-skins` rejects it. The
   allowlist remains exactly `surface.panel.radius` and
   `surface.panel.border-width`.
2. Add a host-probe render test for `terminal-host`, `glass` and `paper`:
   rofi `window` radius follows the probe host value; rofi
   `mainbox`/`inputbar`/`element` retain their authored skin radii.
3. Clarify in the `scripts/validate-skins.py` docstring and `skins/README.md`
   that `surface.panel` is the canonical outer-surface role, host rounding is
   outer-only, and inner radii are skin-owned.
4. Document the wlogout button → panel exception: action-card outer geometry
   follows the panel tokens by consumer mapping, not as an inner-control
   precedent.
5. Do not change production templates, the schema allowlist or runtime
   behavior. Validation/docs only.
6. Gates: `make validate-skins`, `make test-skins`, `make lint`,
   `make gates-ci` in the foreground; tag and push `v0.17.1`.

## Acceptance

- [ ] `host-inner-radius.toml` fails `validate-skins` with the allowlist
      message; the host allowlist is unchanged.
- [ ] The rofi render probe covers `terminal-host`, `glass` and `paper`:
      `window` follows the host radius, inner selectors keep skin radii.
- [ ] Validator docstring and `skins/README.md` state outer-only host semantics
      and skin-owned inner radii.
- [ ] The wlogout panel-radius action-card exception is documented as a mapping
      decision, not an inner-control precedent.
- [ ] No production template, schema allowlist or behavior change.
- [ ] `make validate-skins`, `make test-skins`, `make lint` and `make gates-ci`
      pass in the foreground.
- [ ] `v0.17.1` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `dotfiles-v3/docs/111-host-radius-granularity.md` §Decision,
  HG-1.3–HG-1.5; `scripts/validate-skins.py` `HOST_INHERITABLE`.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; the host-probe test names the three skins and selector
  values.

## Outcome (2026-11-11)

Filled in the closing commit.
