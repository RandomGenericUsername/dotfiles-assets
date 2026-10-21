# assets-catalog Specification

## Purpose

The assets repository is the dotfiles corpus as data: five class directories behind one annotated
semver tag, consumed from a pinned checkout. This specification states what the corpus must be for a
consumer to pin it safely — the class layout, the two version numbers, the repo-local catalog, and
the absence of everything the consumer generates itself.

## Requirements

### Requirement: Five classes, one tag

The repository SHALL hold exactly five class directories — `icons/`, `templates/`, `configs/`,
`content/`, `desktop/` — versioned by one annotated tag, and SHALL NOT rename a class or move a file
between classes without a MAJOR tag.

Evidence: spine AD-3/AD-4; consumers address class paths literally.

#### Scenario: Class set is fixed

- **WHEN** a class directory is renamed, or a sixth top-level class appears
- **THEN** `make validate` fails: the catalog's class names must equal the fixed set, and a rename
  is a MAJOR change rather than an edit

#### Scenario: One tag covers all five classes

- **WHEN** a release adds content to two classes
- **THEN** both land under the same tag, and a consumer bumps one pin

### Requirement: The catalog is repo-local inventory

`catalog.yaml` SHALL describe what is inside each class — directory, declared subdirectories,
contract file, and `schema_major` where the class bears one — and SHALL NOT name a consumer
destination, a deployment path, or an absolute path.

Evidence: spine AD-6 separates "what is inside" (this file) from "where it goes" (the consumer's
manifest).

#### Scenario: Catalog and tree agree

- **WHEN** the catalog names a class directory that does not exist, or a class directory exists that
  the catalog does not declare
- **THEN** `make validate` fails naming the path, in both directions

#### Scenario: Undeclared subdirectory

- **WHEN** a class directory gains a subdirectory the catalog does not declare
- **THEN** `make validate` fails: an undeclared path is corpus nothing tracks

#### Scenario: A destination path appears

- **WHEN** a catalog value is an absolute path, starts with `~`, or names a deployment location
- **THEN** `make validate` fails naming the dotted key, because the destination map belongs to the
  consumer and a second copy here would drift unowned

### Requirement: Schema versions are separate from the tag

Each schema-bearing class SHALL carry an integer `schema_major` in its contract file, equal to the
catalog's value; removing or retyping a required name SHALL require a `schema_major` bump and a
MAJOR tag.

Evidence: spine AD-12; no schema file existed in the corpus before this repository, so these are new
work.

#### Scenario: Schema and catalog disagree

- **WHEN** `icons/schema.json` declares `schema_major: 2` while the catalog still says `1`
- **THEN** `make validate` fails naming the file and both values

#### Scenario: Class with no contract

- **WHEN** a class has no contract file
- **THEN** the catalog declares `schema_major: null` explicitly, and a declared schema with no
  `schema_major` (or the reverse) fails validation

### Requirement: Generated and mutable artifacts are absent

The tree SHALL NOT contain `icons.json`, `settings.toml`, a rendered `kitty.conf`, `btop.conf` or
`.zshrc`, palette or `current/` state, or a mutable `active-theme`.

Evidence: spine AD-11 — those are produced by the consumer's roles or by the runtime.

#### Scenario: Artifact committed by accident

- **WHEN** any forbidden file name exists anywhere in the tree
- **THEN** `make validate` fails naming every offending relative path

#### Scenario: A template of the same name stays legal

- **WHEN** a source template is named `btop.conf.j2`
- **THEN** it is allowed, because only the *rendered* file name is forbidden — conflating the two
  would either ban the class or wave the artifact through

### Requirement: Gates pass with no provisioned state

`make gates` SHALL pass on a fresh clone with no virtualenv and no network beyond the clone, and
`make hermetic` SHALL re-run the checks with `env -i`, empty `HOME`/`XDG_*` directories and a
foreign working directory.

Evidence: slice S0 acceptance gate 4 (`git clone … && make gates`).

#### Scenario: Validator depends on the host

- **WHEN** a validator reads a path under `$HOME` or an `$XDG_*` directory, or resolves the
  repository from the current working directory instead of its own location
- **THEN** `make hermetic` fails, because the run has neither

### Requirement: CI jobs and gates cannot drift

The workflow SHALL run one job per `make gates` target, and `scripts/ci-gates-parity.py` SHALL
compare its job keys against the Makefile's `GATES` in both directions.

Evidence: spine AD-15 item 11.

#### Scenario: Gate without a job

- **WHEN** a target joins `GATES` and no workflow job is added
- **THEN** `make ci-gates-parity` fails naming the gate

#### Scenario: CI-only job without a declaration

- **WHEN** a job exists that is not a `GATES` member and is not a declared `CI_ONLY_EXEMPT` entry
- **THEN** `make ci-gates-parity` fails naming the job, because it runs something no developer gate
  runs

### Requirement: A published tag is immutable

A released tag SHALL never be moved or deleted; a fix SHALL ship as a new tag, after gates green,
the changelog update, and an annotated tag.

Evidence: spine AD-4.

#### Scenario: Post-release defect

- **WHEN** a defect is found in a released corpus
- **THEN** the fix is committed, validated and released as the next tag; the previous tag keeps the
  bytes a verified machine already has

#### Scenario: The tag is annotated

- **WHEN** a release is cut
- **THEN** `git cat-file -t <tag>` reports `tag`, and `git ls-remote --tags <repo> <tag>` reports the
  tag object plus its peeled `^{}` commit
