---
id: req-012
title: "Skins template naming: <configDir>.gtk.css.j2 and the resolved skin.json schema"
kind: requirement
status: done
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-012/
branch: ticket/req-012-skins-template-naming
---

# Skins template naming: `<configDir>.gtk.css.j2` and the resolved skin.json schema

## Why

The canonical skin contract now freezes the artifact interface at `contracts`
`v0.5.2` (`skins.md`, "Template set and consumer artifacts"):

- there is exactly one template per target config directory, named
  `<configDir>.gtk.css.j2`, and the expander renders `<configDir>.css`;
- the bar's `configDir` is `ags` (dotfiles-v3 `apps.yaml`);
- the runtime emits one shared `current/skin.json`, validated directly against
  `schemas/skin-json.schema.json`, with `version: 1` plus the six token groups
  and numeric tokens as raw JSON numbers.

This repository still ships `skins/templates/ags-bar.gtk.css.j2`. That name is
not the contract name: an expander that follows `skins.md` would look for
`ags.gtk.css.j2` and render `ags.css`, so the template is unreachable even
though `make validate-skins` is green. The gate also accepts any `*.j2` name, so
it cannot catch the next drift. The vendored pair is pinned at `v0.5.1`, and the
resolved-document schema the platform actually parses is not vendored at all.

Evidence: `contracts` `v0.5.2` (`320ad69`) `skins.md:136-191`; the current tree
`skins/templates/ags-bar.gtk.css.j2`; `scripts/validate-skins.py`
`templates_dir.glob("*.j2")` accepts the old name.

## Requirement

1. Rename `skins/templates/ags-bar.gtk.css.j2` to
   `skins/templates/ags.gtk.css.j2` with `git mv`; the body is unchanged.
2. `scripts/validate-skins.py` and `skins/tests/` enforce the naming convention:
   every file in `skins/templates/` matches
   `^[a-z0-9][a-z0-9_-]*\.gtk\.css\.j2$`; the target `configDir` is the prefix.
   The gate summary reports the template count and the target list. A bad name
   is a negative test fixture.
3. Re-vendor the canonical schemas from `contracts` `v0.5.2` (the pair is byte-
   identical to `v0.5.1`; the PIN must name the current interface tag) and add
   `skins/contracts/skin-json.schema.json` as a byte copy. `skins/contracts/PIN`
   records `contracts=v0.5.2`, the source commit and a sha256 per file.
4. `skins/schema.json` sets `canonical.tag: v0.5.2` and states that the resolved
   `skin.json` document is validated against the vendored
   `skins/contracts/skin-json.schema.json`.
5. A test validates a representative resolved `skin.json` built from the glass
   manifest (`version: 1` + the six groups, numeric tokens as raw numbers)
   against the vendored `skin-json` schema — the document the runtime emits and
   the platform parses.
6. README, `skins/README.md`, CHANGELOG, `catalog.yaml`, the ticket and INDEX
   record the naming rule, the new target (`ags`), the `v0.5.2` pin, the
   resolved-document schema and the `v0.9.1` inventory.

## Acceptance

- [x] `skins/templates/ags.gtk.css.j2` exists, the old `ags-bar` name is gone,
      and the template body is byte-identical to the `v0.9.0` file.
- [x] `make validate-skins` fails a template whose name does not match
      `^[a-z0-9][a-z0-9_-]*\.gtk\.css\.j2$`, derives the target from the prefix,
      and its summary prints `templates=<n>` and the target(s).
- [x] `skins/contracts/{skin-token,skin-manifest,skin-json}.schema.json` are
      byte copies from `contracts` `v0.5.2` (`320ad69`), and
      `skins/contracts/PIN` records `contracts=v0.5.2`, the source commit and a
      matching sha256 for each file.
- [x] `skins/schema.json` names `canonical.tag: v0.5.2`, vendors the resolved-
      document schema, and its note describes the resolved `skin.json` shape.
- [x] The test suite validates a resolved glass document (`version: 1` + six
      groups, numeric tokens raw numbers) against the vendored `skin-json`
      schema, and includes the bad-template-name negative fixture.
- [x] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python` and
      `make validate` pass; the ticket branch is fast-forward merged to `master`
      (no unmerged ticket branch) and `v0.9.1` is an annotated tag on the merged
      commit. Existing tags are not moved.

## Evidence / Verify

- Evidence: `contracts` `v0.5.2` (`320ad69`) `skins.md:136-191` freezes
  `<configDir>.gtk.css.j2` → `<configDir>.css`, `configDir = ags` for the bar,
  and the resolved `skin.json` shape (`version: 1` + six groups, raw numbers).
  The `v0.9.0` tree ships `skins/templates/ags-bar.gtk.css.j2`, accepts any
  `*.j2`, pins `v0.5.1`, and does not vendor `skin-json.schema.json`.
- Verify: `make validate-skins` → PASS; `make test-skins
  PYTHON=$PWD/.venv/bin/python` → PASS; `make validate` → PASS;
  `git cat-file -t v0.9.1` → `tag`; `git merge-base --is-ancestor
  ticket/req-012-skins-template-naming master` → exit 0.

## Discrepancy / judgment log

- **Why a requirement, not an ops-task.** The slice changes the validator, the
  vendored schema set and the test suite, so it is a bounded implementation
  slice rather than doc/data-only work.
- **No token or `schema_major` change.** Renaming the template keeps every token
  value; the runtime only learns the contract name `<configDir>.gtk.css.j2`.
  This is a PATCH: no class path moves, no token is retyped, and
  `schema_major` stays `1`.
- **Both canonical tags are recorded honestly.** The skin pair is byte-identical
  at `v0.5.1` and `v0.5.2`; the PIN moves to `v0.5.2` because that is the tag
  that freezes the artifact interface this slice implements. The hashes still
  match the unchanged bytes.
- **The naming regex cannot identify the bar's target by itself.** `ags-bar` is
  a syntactically valid `configDir` prefix, so `ags-bar.gtk.css.j2` still matches
  the generic regex. The rename to `ags.gtk.css.j2` is driven by the contract's
  bar `configDir = ags`; the regex + reported target catch malformed names, not
  a syntactically valid wrong target for a specific consumer. The negative
  fixture is therefore `ags-bar.css.j2`, which genuinely violates the suffix.
- **The resolved-document schema is vendored but not a `$ref` delegate.** The
  local manifest envelope still delegates token types only to
  `skin-manifest.schema.json`; `skin-json.schema.json` describes the runtime
  output, so it is a third pinned file and `canonical.resolved_document`, not a
  fourth token delegate.

## Outcome (2026-11-05)

**Worktree:** `.worktrees/req-012/`
**Branch:** `ticket/req-012-skins-template-naming`
**Commits:** `50528fb` (ticket + INDEX plan), `db33e7e` (template rename,
validator, vendored schemas, tests, docs/version updates).
**Merge:** fast-forward into `master` (`49f9235..db33e7e`); the ticket branch is
not left unmerged.
**Tag:** `v0.9.1` (annotated object `34fa2e2`, commit `db33e7e`), created on the
merged commit before this close-out commit; the object hash is recorded here
because a tag cannot contain its own hash.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/templates/ags.gtk.css.j2` | `git mv` from `ags-bar.gtk.css.j2`; body byte-identical (`sha256 02619b…`) |
| `scripts/validate-skins.py` | enforces `^[a-z0-9][a-z0-9_-]*\.gtk\.css\.j2$` on every file in `skins/templates/`, derives the target from the prefix, prints `templates=<n> targets=<configDir>`, pins three vendored files, checks `source-commit`, and requires `canonical.resolved_document` |
| `skins/contracts/skin-json.schema.json` | byte copy from `contracts` `v0.5.2` (`12eeb2cd…`) |
| `skins/contracts/PIN` | `contracts=v0.5.2`, source commit `320ad69…`, sha256 for token/manifest/skin-json |
| `skins/schema.json` | `canonical.tag: v0.5.2`, three `paths`/`vendored_paths`, `resolved_document` note |
| `skins/tests/test_skins.py`, `test_parity.py`, fixtures | template target test, bad-name fixture (`ags-bar.css.j2`), resolved-glass `skin.json` validation, resolved numeric-string rejection, new template path |
| `README.md`, `skins/README.md`, `CHANGELOG.md`, `Makefile`, `catalog.yaml` | naming rule/target, `v0.9.1` inventory, `v0.5.2` pin, resolved-document schema |

### Evidence — commands and exact results

| Command | Result |
| --- | --- |
| `make validate-skins` | **PASS** — `manifests=3 templates=1 targets=ags tokens=23 roles=51` |
| `make test-skins PYTHON=$PWD/.venv/bin/python` | **PASS** — `38 passed` |
| `make validate` | **PASS** — 6 classes, 27 directories, 395 files scanned, tag `v0.9.1` |
| `PATH=/tmp/opencode/shellcheck/shellcheck-v0.10.0:$PATH make gates` | **exit 0** — all 9 gates incl. shellcheck and hermetic PASS |
| `git show v0.9.0:skins/templates/ags-bar.gtk.css.j2 \| cmp - skins/templates/ags.gtk.css.j2` | byte-identical |
| `git -C ../contracts show v0.5.2:schemas/<name>.schema.json \| cmp - skins/contracts/<name>.schema.json` | byte-identical for token, manifest and skin-json |

### New PIN (verbatim)

```text
contracts=v0.5.2
source-commit=320ad69105456500693eb938e3d1d51ef287a455
sha256  22e81ec4e73a659ed94334f323e6c578886842ed873abac50eacc6608ba906fd  skin-token.schema.json
sha256  aac5d8caf3997eb45bb8c03068f708b07b79cdd68a098de29e4e96c9319bb48a  skin-manifest.schema.json
sha256  12eeb2cdcbb3883212a7fde50dbc4f9028adaa6d5ca05bbbd35dcdcf715b3728  skin-json.schema.json
```
