---
id: req-015
title: "Skins v2: convert the skin data class to the Appearance token model"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-015/
branch: ticket/req-015-appearance-v2
---

# Skins v2: convert the skin data class to the Appearance token model

## Why

`contracts` `v0.7.0` freezes the v2 appearance plane (docs/105, `appearance.md`):
one nested token model (`surface`, `state`, `type`, `ink`, `layout.<app>`,
`mode.dark`/`mode.light`) replaces the v1 flat skin vocabulary. The assets
class still ships `schema_major = 1` manifests and v1 `{{SKIN_*}}`
placeholders, so it cannot produce a v2 `tokens.json` or expand the v2
templates a v2 consumer reads.

Evidence: `contracts@appearance.md` §"Token model v2"; the vendored pair in
`skins/contracts/` is `contracts=v0.6.0`; every manifest in
`skins/manifests/` is `schema_major = 1`.

## Requirement

1. Convert `skins/manifests/{glass,flat,paper}.toml` to the v2 manifest
   envelope (`schemaVersion = 2`; the local schema's `schema_major` is 2) with
   the nested v2 groups:
   `surface.{panel,card,cell,control,pill}`, `state.{hover,selected,focus,disabled}`,
   `type`, `ink`, `layout.<app>`, and `mode.light`/`mode.dark` overrides where
   needed. `glass` is a faithful conversion of the real bar stylesheet;
   `paper` declares explicit `mode.light` overrides instead of guessing from
   the palette. No literal hex, no transitions, no structure.
2. Rewrite all seven `<configDir>.gtk.css.j2` templates to flattened v2
   placeholder paths (`surface.panel.bg` → `{{SKIN_SURFACE_PANEL_BG}}`,
   `state.hover.fill` → `{{SKIN_STATE_HOVER_FILL}}`, …), replacing v1
   literals where the v2 model covers them (per-role borders/paddings,
   card/control/pill type and padding, hover/selected/focus/disabled, small
   type sizes). Keep component geometry that has no token. No layout token in
   CSS; no hex/transitions.
3. Vendor the `contracts` `v0.7.0` appearance schemas and PIN
   (`appearance-manifest`, `appearance-json`, `appearance-artifact`), keep the
   frozen v1 skin schemas for provenance, and make `scripts/validate-skins.py`
   validate every manifest against `appearance-manifest`, resolve every
   manifest under both modes, validate the resolved `tokens.json` against
   `appearance-json`, and expand every template for every manifest × mode.
   The gate also checks placeholder coverage, palette role vocabulary,
   forbidden hex/transition/structure, and rejects layout tokens in CSS.
4. Update `skins/tests/` parity/mode/state/negative fixtures, plus
   `README.md`, `skins/README.md`, `CHANGELOG.md`, `catalog.yaml`, this ticket
   and `tickets/INDEX.md`.
5. Tag `v0.12.0`; fast-forward merge to `master`; do not push.

## Acceptance

- [x] The three manifests are `schemaVersion = 2`, use only the frozen v2
      vocabulary, and validate against the vendored `appearance-manifest`
      schema; `paper` has explicit light-mode overrides.
- [x] All seven templates use flattened v2 placeholders, contain no literal
      hex/transition/structure, and emit no layout token into CSS.
- [x] `make validate-skins` expands all 7 templates × 3 manifests × 2 modes,
      validates each resolved token document against `appearance-json`, and
      reports the vendored `v0.7.0` hashes.
- [x] `make test-skins` covers glass parity for the tokenized set, paper
      light/dark mode expansion, state/role coverage and the negative fixtures.
- [x] `make validate-skins`, `make test-skins` and `make validate` pass.
- [ ] `v0.12.0` is an annotated tag on the fast-forward-merged commit; the
      branch is not left unmerged; nothing is pushed.

## Evidence / Verify

- Evidence: `contracts` tag `v0.7.0` exists at commit
  `3ea6d8354f23d0b9239e06392897e53496f25144`; the three appearance schemas at
  that tag are byte-identical to the worktree copies. The current assets
  manifests are `schema_major = 1` and the vendored PIN is `v0.6.0`.
- Verify: `make validate-skins`, `make test-skins`, `make validate`;
  `git cat-file -t v0.12.0`; `git merge-base --is-ancestor
  ticket/req-015-appearance-v2 master`.

## Discrepancy / judgment log

- **Manifest envelope spelling.** The task says `schema_major = 2`; the frozen
  `appearance-manifest` schema requires `schemaVersion = 2` and closes the
  object with `additionalProperties: false`. The manifests therefore use
  `schemaVersion = 2`, while `skins/schema.json` carries `schema_major: 2`.
  The canonical contract wins; adding `schema_major` would be rejected.
- **Asymmetric component paddings (`10px 11px`, `8px 9px`, `4px 8px`,
  `2px 6px`) cannot be represented by the contract's single numeric `padding`
  token. The token carries the first/vertical value and the template keeps the
  expressive second value as a literal, so the glass expansion is unchanged.
- `state.disabled` has no opacity token; component opacity literals remain.
- Per-app layout metrics are namespaced in `layout.<app>` and stay TSX-owned;
  no template emits them.
