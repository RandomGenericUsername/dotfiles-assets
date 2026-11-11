---
id: req-025
title: "Host rounding guards: inner-radius rejection and outer-only render probe"
kind: requirement
status: done
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

- [x] `host-inner-radius.toml` fails `validate-skins` with the allowlist
      message; the host allowlist is unchanged.
- [x] The rofi render probe covers `terminal-host`, `glass` and `paper`:
      `window` follows the host radius, inner selectors keep skin radii.
- [x] Validator docstring and `skins/README.md` state outer-only host semantics
      and skin-owned inner radii.
- [x] The wlogout panel-radius action-card exception is documented as a mapping
      decision, not an inner-control precedent.
- [x] No production template, schema allowlist or behavior change.
- [x] `make validate-skins`, `make test-skins`, `make lint` and `make gates-ci`
      pass in the foreground.
- [x] `v0.17.1` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `dotfiles-v3/docs/111-host-radius-granularity.md` §Decision,
  HG-1.3–HG-1.5; `scripts/validate-skins.py` `HOST_INHERITABLE`.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; the host-probe test names the three skins and selector
  values.

## Outcome (2026-11-11)

**Worktree:** `.worktrees/req-025/` (base `v0.17.0`)
**Branch:** `ticket/req-025-host-radius-guards`
**Commits:** `c32989f` (ticket + INDEX plan), `158ab1b` (inner-radius fixture +
rofi host-probe test), `678bab1` (validator docstring, skins README, release
docs/version), this closing commit (ticket outcome + INDEX done).
**Tag:** `v0.17.1` (annotated) on this closing commit; fast-forward to
`master`, push `master` + tag.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/tests/fixtures/invalid/host-inner-radius.toml` | **new** negative fixture: glass with `[host].inherit = ["surface.card.radius"]` |
| `skins/tests/test_skins.py` | fixture parameter asserts the exact allowlist message; new rofi host-probe render test for `terminal-host`/`glass`/`paper`; explicit `HOST_INHERITABLE` lock |
| `scripts/validate-skins.py` | docstring and `HOST_INHERITABLE` comment state outer-only semantics and skin-owned inner radii; no logic change |
| `skins/README.md` | outer-surface role, outer-only host rounding, inner-radii ownership, wlogout action-card exception |
| `README.md`, `skins/schema.json`, `catalog.yaml`, `CHANGELOG.md` | v0.17.1 release metadata and summary |

No production template, manifest, schema allowlist or validator behavior
changed. `git diff v0.17.0 -- skins/templates skins/manifests skins/contracts`
is empty.

### Fixture evidence

`host-inner-radius.toml` with `surface.card.radius` produces:

```text
skins/manifests/glass.toml: must be one of ['surface.panel.radius', 'surface.panel.border-width'], got 'surface.card.radius'
```

The allowlist remains exactly `surface.panel.radius` and
`surface.panel.border-width`; the new test also asserts
`validate_skins.HOST_INHERITABLE` equals that tuple.

### Rofi host-probe evidence

Probe host `radius=13`, `border-width=2`, rofi `window` → `13px`/`2px` for
all three skins. Authored inner radii retained:

| Skin | `mainbox` card | `inputbar` control | `element` cell |
| --- | ---: | ---: | ---: |
| `terminal-host` | 0px | 2px | 0px |
| `glass` | 9px | 7px | 7px |
| `paper` | 4px | 3px | 3px |

### Gate evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 5 manifests, 11 templates, 10 targets, `artifacts=rofi:rasi`, 57 tokens, 10 expansions, host probe on `glass,paper,terminal-host` |
| Skins fixtures | `make test-skins PYTEST="<assets>/.venv/bin/python -m pytest"` | **PASS** — `138 passed, 3 skipped` (the 3 skips are the pre-existing GTK probes that need `gi`) |
| Lint | `PATH="<uv-shellcheck-bin>:$PATH" make lint` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — rc `0`; every validator, lint and `hermetic: PASS` |

### Downstream pins

- **Composition should remain on assets `v0.17.0`.** No deployed artifact
  changed: this release only adds fixtures/tests and documentation, and the
  rendered templates, manifests and contracts are byte-identical to `v0.17.0`.
  Bumping the composition pin would churn a pin without changing what is
  deployed. Bump only if a consumer wants the guard tests/docs in its mirror.
- No runtime, provisioning, composition, app or live-state change is in this
  ticket.
