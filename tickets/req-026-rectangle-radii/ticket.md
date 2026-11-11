---
id: req-026
title: "Rectangle radii: delegate panel/card/control/cell and keep the pill explicit"
kind: requirement
status: in-progress
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

- [ ] `skins/contracts/` is a byte copy of `contracts v0.11.0`; PIN hashes,
      source commit and canonical tag agree.
- [ ] The three opt-in manifests list all five rectangle paths and no pill;
      `terminal`/`flat` have no `[host]` block.
- [ ] `host-pill-radius.toml` fails the allowlist; the removed inner-radius
      fixture is replaced by a positive all-five-paths fixture.
- [ ] Rofi renders panel/card/control/cell from the host probe for opt-in
      skins and authored values for `terminal`/`flat`; wlogout/GTK probes cover
      the tokens those targets carry.
- [ ] Validator docstring, skins README, catalog, CHANGELOG and version
      metadata describe `contracts v0.11.0`, rectangle delegation and the pill
      exclusion.
- [ ] Five manifests × all templates still expand; required targets and
      artifacts are unchanged.
- [ ] `make validate-skins`, `make test-skins`, `make lint` and
      `make gates-ci` pass in the foreground.
- [ ] Annotated `v0.18.0` is tagged on the fast-forwarded `master` commit and
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
