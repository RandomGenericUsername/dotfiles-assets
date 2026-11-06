---
id: req-011
title: "Skins value types: unitless numeric tokens, vendored canonical schemas"
kind: requirement
status: in-progress
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-011/
branch: ticket/req-011-skins-value-types
---

# Skins value types: unitless numeric tokens, vendored canonical schemas

## Why

The canonical skin contract (`contracts` `schemas/skin-token.schema.json` and
`schemas/skin-manifest.schema.json`, `v0.5.0`, being patched to `v0.5.1` for the
unit convention) types these tokens as unitless JSON **numbers**:

`radius-panel`, `radius-card`, `radius-cell`, `radius-pill`, `border-w`, `gap`,
`title-size`, `text-size`, `panel-width`, `bt-list-spacing`, `bar-row-height`,
`chip-min`.

The three manifests shipped at `v0.8.0` write them as `"12px"`-style strings.
`scripts/validate-skins.py` validated only the local, non-vendored
`skins/schema.json`, which had a `px` string grammar, so the gate could not see
the violation. AGS's parser rejects the strings, so the runtime `skin.json`
would fail at startup even though this repository was green.

Evidence: `contracts` `v0.5.0` `skins.md:49-59` ("non-negative number = px",
`title-size`/`text-size` "number", layout "number") and the schema definitions
`nonNegativeNumber` / `number`; the `v0.8.0` manifests'
`radius-panel = "12px"` etc.; `make validate-skins` at `v0.8.0` passes because
the local schema alone says `dimension: string, pattern ^...px$`.

## Requirement

1. Vendor the canonical pair byte-for-byte into `skins/contracts/` and pin it:
   `skins/contracts/PIN` records the `contracts` tag and the sha256 of each
   vendored file. `v0.5.1` is not reachable in the local `contracts` checkout
   yet, so vendor the current `v0.5.0` bytes and record `v0.5.1` as the intended
   tag; re-vendoring is a hash/tag update, not a schema rewrite.
2. `skins/schema.json` delegates its token value types to the vendored canonical
   definitions (external `$ref`s), sets `canonical.vendored: true`,
   `canonical.tag: v0.5.0`, `canonical.intended_tag: v0.5.1`, and carries no
   divergent local `px` lookalike grammar.
3. All three manifests (`glass`, `flat`, `paper`) carry the numeric tokens as
   unitless TOML numbers. `cell-pad` stays the literal pair string; role
   expressions, paint, ink and `font-family` stay strings. Glass keeps its
   `v0.8.0` parity values; only the representation changes.
4. `scripts/validate-skins.py` validates against the vendored canonical schema,
   so numeric strings are rejected (`radius-panel = "12px"` is an error), and
   expands placeholders with the unit rule: a numeric token in a CSS length
   position renders `<n>px`; `cell-pad` renders verbatim.
5. The test suite proves the vendored hashes, the delegation, the canonical
   value types, and that the expanded glass still contains
   `border-radius: 12px`, `border: 1.5px solid @primary`, `padding: 8px 9px`
   and `border-radius: 20px`.
6. README, `skins/README.md`, CHANGELOG, the ticket and INDEX document the value
   convention (`number = px at render time`) and the vendoring/pin rule.

## Acceptance

- [ ] `skins/contracts/{skin-token,skin-manifest}.schema.json` are byte copies
      from `contracts` and `skins/contracts/PIN` records `contracts=<tag>` plus
      a matching sha256 for each file.
- [ ] `skins/schema.json` delegates token types to the vendored canonical pair
      (`canonical.vendored: true`, `canonical.tag` set, no local dimension
      grammar) and tests enforce byte equality and delegation.
- [ ] `glass`, `flat` and `paper` use unitless numbers for every numeric token;
      `cell-pad` and all paint/ink/font strings are unchanged in kind.
- [ ] `make validate-skins` rejects a numeric string and passes the corpus;
      `make test-skins PYTHON=$PWD/.venv/bin/python` includes the negative
      numeric-string fixture and the expanded-parity assertions.
- [ ] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python` and
      `make validate` pass; the ticket branch is fast-forward merged to `master`
      (no unmerged ticket branch) and `v0.9.0` is an annotated tag on the merged
      commit. Existing tags are not moved.

## Evidence / Verify

- Evidence: `contracts` `v0.5.0` `skins.md:49-59` and
  `schemas/skin-token.schema.json` definitions `number` /
  `nonNegativeNumber`; `v0.8.0` manifests carry `"12px"` strings; the local
  `skins/schema.json` `dimension` definition is the divergent grammar.
- Verify: `make validate-skins` → PASS; `make test-skins
  PYTHON=$PWD/.venv/bin/python` → PASS; `make validate` → PASS;
  `git cat-file -t v0.9.0` → `tag`; `git merge-base --is-ancestor
  ticket/req-011-skins-value-types master` → exit 0.

## Discrepancy / judgment log

- **`v0.5.1` is not reachable.** The local `contracts` checkout is at
  `v0.5.0` (`0625b56`) and has no `v0.5.1` tag. Vendoring waits for a tag that
  does not exist would be a false claim, so the PIN records the actual
  `contracts=v0.5.0` bytes plus `intended-contracts=v0.5.1`. The unit
  convention is already in the `v0.5.0` types, so the local manifests are
  validated against the reachable canonical truth.
- **Local manifest envelope, canonical token types.** The canonical manifest
  schema wraps the token groups in `groups` with `schemaVersion`; this
  repository's frozen v1 manifests use the flat `schema_major` + group layout
  shipped at `v0.7.0`. Token *values* delegate to the canonical definitions;
  restructuring the envelope would be a contract/tag break outside this
  correction.
- **`paper` / `flat` title-size.** Both keep `15` (they already shipped
  `"15px"`); only glass is `12.5`, preserving the `v0.8.0` parity extraction.
