---
id: req-026
title: "Rectangle radii: delegate panel/card/control/cell and keep the pill explicit"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-026/
branch: ticket/req-026-rectangle-radii
---

# Rectangle radii: delegate panel/card/control/cell and keep the pill explicit

## Why

`contracts v0.11.0` expands the skin `[host]` allowlist from the outer panel
to the rectangle radii. The assets class must re-vendor that contract, opt its
host-following manifests into the new paths, and invert the `v0.17.1`
outer-only guards that now contradict the canonical contract. `surface.pill`
stays explicit: a capsule is a skin identity, not a host rectangle.

## Requirement

1. Re-vendor the seven canonical schemas from `contracts v0.11.0` into
   `skins/contracts/`, update every `sha256` in `skins/contracts/PIN`, and move
   `skins/schema.json` `canonical.tag` to `v0.11.0`.
2. `glass`, `paper` and `terminal-host` `[host].inherit` names all five
   rectangle paths:
   - `surface.panel.radius`
   - `surface.panel.border-width`
   - `surface.card.radius`
   - `surface.control.radius`
   - `surface.cell.radius`

   `surface.pill.radius` stays explicit and is not inheritable. `terminal`
   and `flat` remain `[host]`-free and keep their authored values.
3. Invert the old outer-only guards:
   - remove the invalid `host-inner-radius.toml` fixture; an inner radius that
     is listed is valid now;
   - add a `host-pill-radius.toml` invalid fixture proving the pill cannot be
     delegated;
   - expand `HOST_INHERITABLE`/`HOST_PROBE` and the render tests so rofi
     `window`→panel, `mainbox`→card, `inputbar`→control and `element`→cell all
     follow the probe for opt-in skins, while `terminal`/`flat` keep authored
     values;
   - add wlogout/GTK host probes where those targets carry the relevant token.
4. Update the validator docstring, `skins/README.md`, `catalog.yaml`,
   `CHANGELOG.md`, release version metadata and tests. Five manifests × all
   templates must still expand, and the required targets/artifacts stay
   unchanged.
5. Gates in the foreground: `make validate-skins`, `make test-skins`,
   `make lint`, `make gates-ci`. Tag and push annotated `v0.18.0`.

## Acceptance

- [x] `skins/contracts/` is a byte copy of `contracts v0.11.0`; PIN hashes,
      source commit and canonical tag agree.
- [x] The three opt-in manifests list all five rectangle paths and no pill;
      `terminal`/`flat` have no `[host]` block.
- [x] `host-pill-radius.toml` fails the allowlist; the removed inner-radius
      fixture is replaced by a positive all-five-paths fixture.
- [x] Rofi renders panel/card/control/cell from the host probe for opt-in
      skins and authored values for `terminal`/`flat`; wlogout/GTK probes cover
      the tokens those targets carry.
- [x] Validator docstring, skins README, catalog, CHANGELOG and version
      metadata describe `contracts v0.11.0`, rectangle delegation and the pill
      exclusion.
- [x] Five manifests × all templates still expand; required targets and
      artifacts are unchanged.
- [x] `make validate-skins`, `make test-skins`, `make lint` and
      `make gates-ci` pass in the foreground.
- [x] Annotated `v0.18.0` is tagged on the fast-forwarded `master` commit and
      pushed with `master`.

## Evidence / Verify

- Evidence: `contracts@v0.11.0` (`6a3ed99`) `schemas/appearance-manifest.schema.json`
  host `inherit.items.enum`; `contracts` ticket `REQ-019` downstream pins name
  `dotfiles-assets v0.18.0`.
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; `git diff v0.17.1 -- skins/contracts` shows only the
  canonical `v0.11.0` bytes.

## Non-goals

- No runtime resolver/identity/manifest implementation; runtime pin
  (`v1.4.0`) and engine/composition pins land in their own repos later.
- No provisioning, composition, app, template or live-state change.
- No pill, padding, gap, type, paint, colour, state, layout or non-panel
  border-width delegation.


## Outcome (2026-11-11)

**Worktree:** `.worktrees/req-026/` (base `v0.17.1`)
**Branch:** `ticket/req-026-rectangle-radii`
**Commits:** `b962194` (ticket + INDEX plan), `3467c2f` (contracts v0.11.0
re-vendor, five-path manifests, validator probe), `3512018` (inverted fixtures
and rectangle render probes), `6b993bc` (release docs/version), this closing
commit (ticket outcome + INDEX done).
**Tag:** `v0.18.0` (annotated) on this closing commit; fast-forward to
`master`, push `master` + tag.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/contracts/` + `PIN` | Byte re-vendor from `contracts v0.11.0`, source commit `6a3ed99dab6cf3e49a4643bc82e9d7428d0880ca`; PIN hashes and comment updated. Only `appearance-manifest` and `generation-manifest` changed bytes. |
| `skins/manifests/{glass,paper,terminal-host}.toml` | `[host].inherit` names the five rectangle paths; `surface.pill.radius` stays authored. `terminal`/`flat` remain `[host]`-free. |
| `scripts/validate-skins.py` | `HOST_INHERITABLE` and `HOST_PROBE` cover panel/card/control/cell (probe 13/2/14/15/16); docstring and notes state the rectangle rule and pill exclusion. |
| `skins/tests/fixtures/invalid/host-pill-radius.toml` | Replaces the old inner-radius rejection: only the pill remains invalid. |
| `skins/tests/fixtures/positive/host-rectangles.toml` | Positive all-five-path fixture; inner radii are valid when listed. |
| `skins/tests/fixtures/invalid/host-unknown-inherit.toml` | Unknown path moved to `surface.card.border-width`. |
| `skins/tests/test_skins.py` | Rofi `window`/`mainbox`/`inputbar`/`element` probe covers panel/card/control/cell for opt-in skins, `terminal`/`flat` stay authored; GTK3/GTK4 card/control probe; wlogout panel-mapping probe; policy/fallback/fixture assertions updated. |
| `skins/schema.json`, `README.md`, `skins/README.md`, `catalog.yaml`, `CHANGELOG.md`, `Makefile` | `contracts v0.11.0` / `v0.18.0` release metadata, five-path inventory and pill-exclusion docs. |

No production template changed: `git diff v0.17.1 -- skins/templates` is empty,
the target/artifact sets are unchanged, and every template still expands for
five manifests × both modes.

### Guard evidence

| Claim | Command | Result |
| --- | --- | --- |
| Vendored bytes | `git -C ../contracts show v0.11.0:schemas/<file>` piped to `cmp` | all seven files identical |
| Pill rejected | `make test-skins` (`host-pill-radius.toml`) | `surface.pill.radius` fails the allowlist |
| Inner radii accepted | `make test-skins` (`host-rectangles.toml`) | all five paths validate |
| Rectangle probes | `make test-skins` | rofi window/mainbox/inputbar/element and GTK/wlogout probes pass |

### Gate evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 5 manifests, 11 templates, 10 targets, `artifacts=rofi:rasi`, 57 tokens, 10 expansions, host probe on `glass,paper,terminal-host` |
| Skins fixtures | `make test-skins PYTEST="../../.venv/bin/python -m pytest"` | **PASS** — `156 passed, 3 skipped` (the 3 skips are the pre-existing GTK probes that need `gi`) |
| Lint | `PATH="<uv-shellcheck-bin>:$PATH" make lint` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — rc `0`; every validator, lint and `hermetic: PASS` |

### Downstream pins

- **contracts `v0.11.0`** — required canonical contract pin.
- **assets `v0.18.0`** — this release.
- **runtime `v1.4.0`** — resolve and record the additional delegated rectangle
  radii, then re-pin `contracts v0.11.0`.
- **engine/composition** — later slice, after assets and runtime.

No runtime, provisioning, composition, app or live-state change is in this
ticket.
