# Spec Delta

## Purpose

The assets repository is the dotfiles corpus as data: five class directories behind one annotated
semver tag, consumed from a pinned checkout. This delta adds the capability it introduces — the
layout, the catalog, the two version numbers, the forbidden artifacts, the fresh-clone gate set and
the immutable tag.

## ADDED Requirements

### Requirement: Five classes, one tag

The repository SHALL hold exactly five class directories — `icons/`, `templates/`, `configs/`,
`content/`, `desktop/` — versioned by one annotated `vMAJOR.MINOR.PATCH` tag. A class directory
SHALL NOT be renamed, and a file SHALL NOT move between classes, without a MAJOR tag.

Evidence: spine AD-3/AD-4; consumers address class paths literally. Verify: `ls -d icons templates
configs content desktop` and `python3 scripts/validate-catalog.py` exit 0.

#### Scenario: Class set is fixed

- **WHEN** a class directory is renamed or a sixth class appears
- **THEN** `make validate` fails, because the catalog's class names must equal the fixed set

#### Scenario: One tag covers all five

- **WHEN** a release touches two classes
- **THEN** both land under one tag and a consumer bumps one pin

### Requirement: The catalog is repo-local inventory

`catalog.yaml` SHALL declare each class's directory, subdirectories, contract file and
`schema_major` where it bears one, and SHALL NOT name a consumer destination or a deployment path.

Evidence: spine AD-6 separates "what is inside" (this file) from "where it goes" (the consumer's
manifest). Verify: `python3 scripts/validate-catalog.py` scans catalog scalars for destination
shapes and fails on one.

#### Scenario: Catalog and tree disagree

- **WHEN** a catalog entry names a missing directory, or the tree has an undeclared class or
  subdirectory
- **THEN** `make validate` fails naming the path, in both directions

### Requirement: Schema versions are separate from the tag

Each schema-bearing class SHALL carry an integer `schema_major` in its contract file equal to the
catalog's value, and removing or retyping a required name SHALL require a `schema_major` bump and a
MAJOR tag.

Evidence: spine AD-12; no schema file existed in the corpus before this change, so the files are new
work. Verify: `python3 scripts/validate-catalog.py` prints the schema-bearing classes and fails when
a file's value disagrees with the catalog's.

#### Scenario: Disagreement is a failure

- **WHEN** a schema file's `schema_major` differs from the catalog's
- **THEN** `make validate` fails naming the file and both values

#### Scenario: No contract, stated

- **WHEN** a class has no contract file
- **THEN** the catalog declares `schema_major: null` explicitly; a schema without a version, or a
  version without a schema, fails

### Requirement: Generated and mutable artifacts are absent

The tree SHALL NOT contain `icons.json`, `settings.toml`, a rendered `kitty.conf`, `btop.conf` or
`.zshrc`, palette or `current/` state, or a mutable `active-theme`.

Evidence: spine AD-11 — those are produced by the consumer's roles or the runtime. Verify:
`touch icons/mappings/icons.json && make validate` → non-zero naming the path; remove → exit 0.

#### Scenario: Accidentally committed artifact

- **WHEN** a forbidden file name exists anywhere in the tree
- **THEN** `make validate` fails naming its relative path; a template of the same base name
  (`btop.conf.j2`) stays legal because only the rendered name is forbidden

### Requirement: Gates pass with no provisioned state

`make gates` SHALL pass on a fresh clone with no virtualenv and no network beyond the clone, and
`make hermetic` SHALL re-run the checks with `env -i`, empty `HOME`/`XDG_*` directories and a
foreign working directory.

Evidence: slice S0 acceptance gate 4 (fresh clone + `make gates`). Verify: `git clone <repo>
/tmp/fresh && cd /tmp/fresh && make gates` → exit 0.

#### Scenario: Host dependency

- **WHEN** a validator reads `$HOME`, an `$XDG_*` directory, or the current working directory to
  find the repository
- **THEN** `make hermetic` fails, because the run has none of them

### Requirement: CI jobs and gates cannot drift

The workflow SHALL run one job per `make gates` target, and `scripts/ci-gates-parity.py` SHALL
compare its job keys against the Makefile's `GATES` in both directions.

Evidence: spine AD-15 item 11. Verify: `make ci-gates-parity` → exit 0 and prints both sets.

#### Scenario: Gate without a job

- **WHEN** a target joins `GATES` with no workflow job
- **THEN** `make ci-gates-parity` fails naming the gate

### Requirement: A published tag is immutable

A released tag SHALL never be moved or deleted; a fix ships as a new tag. The ritual SHALL be gates
green → CHANGELOG (and catalog when the inventory changed) → annotated tag → CI green on the tagged
commit.

Evidence: spine AD-4. Verify: `git cat-file -t v0.1.0` → `tag`; `git ls-remote --tags <repo>
'v0.1.0'` → the tag object and its peeled `^{}` commit.

#### Scenario: Post-release defect

- **WHEN** a released corpus has a defect
- **THEN** the fix ships as the next tag; the previous tag keeps the bytes a verified machine has
