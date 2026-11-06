---
id: req-011
title: "Skins value types: unitless numeric tokens, vendored canonical schemas"
kind: requirement
status: done
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
   vendored file. `v0.5.1` was not reachable when this ticket was filed; it
   became reachable during the work, so vendor the `v0.5.1` bytes (the
   unit-convention patch) and pin that tag. Re-vendoring is a hash/tag update,
   not a schema rewrite.
2. `skins/schema.json` delegates its token value types to the vendored canonical
   definitions (external `$ref`s), sets `canonical.vendored: true`,
   `canonical.tag: v0.5.1`, and carries no divergent local `px` lookalike
   grammar.
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

- [x] `skins/contracts/{skin-token,skin-manifest}.schema.json` are byte copies
      from `contracts` and `skins/contracts/PIN` records `contracts=<tag>` plus
      a matching sha256 for each file.
- [x] `skins/schema.json` delegates token types to the vendored canonical pair
      (`canonical.vendored: true`, `canonical.tag` set, no local dimension
      grammar) and tests enforce byte equality and delegation.
- [x] `glass`, `flat` and `paper` use unitless numbers for every numeric token;
      `cell-pad` and all paint/ink/font strings are unchanged in kind.
- [x] `make validate-skins` rejects a numeric string and passes the corpus;
      `make test-skins PYTHON=$PWD/.venv/bin/python` includes the negative
      numeric-string fixture and the expanded-parity assertions.
- [x] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python` and
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

- **`v0.5.1` arrived during the work.** The local `contracts` checkout was at
  `v0.5.0` (`0625b56`) when this ticket was filed, so the first vendoring pass
  used `v0.5.0` and recorded `v0.5.1` as intended. While the branch was open,
  `contracts` advanced to `v0.5.1` (`d1adb19`, unit-convention patch) and then
  `v0.5.2` (`320ad69`); the final vendored bytes are re-taken from `v0.5.1`.
  The skin schemas are unchanged at `v0.5.2`, but the PIN deliberately stays on
  `v0.5.1`, the tag that defines the convention.
- **Local manifest envelope, canonical token types.** The canonical manifest
  schema wraps the token groups in `groups` with `schemaVersion`; this
  repository's frozen v1 manifests use the flat `schema_major` + group layout
  shipped at `v0.7.0`. Token *values* delegate to the canonical definitions;
  restructuring the envelope would be a contract/tag break outside this
  correction.
- **`paper` / `flat` title-size.** Both keep `15` (they already shipped
  `"15px"`); only glass is `12.5`, preserving the `v0.8.0` parity extraction.

## Outcome (2026-11-05)

**Worktree:** `.worktrees/req-011/`
**Branch:** `ticket/req-011-skins-value-types`
**Commits:** `f4a0419` (ticket + INDEX plan), `5a62c2d` (vendored schemas,
manifests, validator, tests, docs/version updates).
**Merge:** fast-forward into `master` (`6233613..5a62c2d`); the ticket branch is
not left unmerged.
**Tag:** `v0.9.0` (annotated object `4e70950`, commit `5a62c2d`), created on the
merged commit before this close-out commit; the object hash is recorded here
because a tag cannot contain its own hash.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/contracts/skin-token.schema.json`, `skin-manifest.schema.json` | byte copies from `contracts` `v0.5.1` (`d1adb19`) |
| `skins/contracts/PIN` | `contracts=v0.5.1`, source commit, sha256 of both files |
| `skins/schema.json` | `canonical.vendored: true`, `tag: v0.5.1`, PIN/delegate paths; all 23 token properties are external `$ref`s to the vendored manifest schema; local `$defs` dimension/spacing grammar removed |
| `skins/manifests/{glass,flat,paper}.toml` | numeric tokens are TOML numbers; `cell-pad` stays `"Npx Npx"`; paint/ink/font strings unchanged |
| `scripts/validate-skins.py` | PIN hash/byte check, canonical `$ref` resolver, canonical type/minimum/pattern checks, numeric-string rejection, unit-rule expansion (`number -> <n>px`, `cell-pad` verbatim) |
| `skins/tests/test_skins.py`, `test_parity.py`, `fixtures/invalid/numeric-string.toml` | hash/delegation/type tests, numeric-string negative fixture, expansion assertions including `border-radius: 12px`, `border: 1.5px solid @primary`, `padding: 8px 9px`, `border-radius: 20px` |
| `skins/README.md`, `README.md`, `CHANGELOG.md`, `catalog.yaml`, `Makefile` | value convention (number = unitless, `px` at render time), vendoring/pin rule, `contracts/` subdir, `v0.9.0` inventory |

### Evidence — commands and exact results (in `.worktrees/req-011/`)

| Command | Result |
| --- | --- |
| `make validate-skins` | **PASS** — `manifests=3 templates=1 tokens=23 roles=51`; expanded 3 manifests through 1 template with the unit rule |
| `make test-skins PYTHON=$PWD/../../.venv/bin/python` | **PASS** — `34 passed` |
| `make validate` | **PASS** — 6 classes, 27 directories, 391 files scanned, tag `v0.9.0` |
| `PATH=/tmp/opencode/shellcheck/shellcheck-v0.10.0:$PATH make gates` | **exit 0** — all 9 gates incl. shellcheck and hermetic PASS |
| `make ci-gates-parity` | **PASS** — 9 GATES, 10 workflow jobs, declared CI-only `ci-gates-parity` |
| `cmp skins/contracts/*.schema.json` against `contracts` `v0.5.1` | byte-identical; `sha256sum` matches `skins/contracts/PIN` |

### Value decisions for `flat` / `paper`

- **`flat`**: radii `0/0/0/999`, `border-w = 0`, `gap = 8`, `cell-pad =
  "7px 8px"`, `title-size/text-size = 15/13`, layout `312/4/28/48`. These are
  exactly the `v0.8.0` values, converted from strings to numbers; no value was
  reinterpreted.
- **`paper`**: radii `6/4/3/999`, `border-w = 1`, `gap = 9`, `cell-pad =
  "8px 10px"`, `title-size/text-size = 15/13`, layout `312/6/30/52`. Its
  `bg-panel`/`bg-card`/`border` role expressions, the `rgba` shadow string and
  `cell-pad` remain strings, untouched.
- **`glass`**: `12/9/7/20`, `border-w = 1.5`, `gap = 8`,
  `cell-pad = "8px 9px"`, `title-size/text-size = 12.5/13`, layout
  `312/4/0/0` — the `v0.8.0` parity values with only the representation
  converted, so the expanded CSS still contains the exact source-length
  declarations.
