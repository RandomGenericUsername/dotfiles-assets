# Spec Delta

## REMOVED Requirements

### Requirement: Five classes, one tag

Reason: the class set grows to six with the additive `skins/` class; every existing class path is
unchanged.

## ADDED Requirements

### Requirement: Six classes, one tag

The repository SHALL hold exactly six class directories — `icons/`, `templates/`, `configs/`,
`content/`, `desktop/`, `skins/` — versioned by one annotated tag, and SHALL NOT rename a class or
move a file between classes without a MAJOR tag.

Evidence: spine AD-3/AD-4; consumers address class paths literally. `skins/` is additive and keeps
every existing class path unchanged.

#### Scenario: Class set is fixed

- **WHEN** a class directory is renamed, a sixth class other than `skins/` appears, or a seventh
  top-level class appears
- **THEN** `make validate` fails: the catalog's class names must equal the fixed set, and a rename
  is a MAJOR change rather than an edit

#### Scenario: One tag covers all six classes

- **WHEN** a release adds content to two classes
- **THEN** both land under the same tag, and a consumer bumps one pin

### Requirement: The skins class carries frozen v1 manifests and a template

`skins/` SHALL hold a data-only contract and three manifests. A skin SHALL be a palette/ink
mapping, paint and rhythm/density only: it SHALL NOT carry structure or variant tokens. Every
manifest SHALL declare `schema_major`, a `name` equal to its file stem, and the six token groups
`shape`, `rhythm`, `surface`, `ink`, `type` and `layout` with exactly the frozen v1 token names.
Surface, border and shadow values SHALL be palette-role expressions or `transparent`; a literal hex
colour SHALL fail. `blur` SHALL be `none` or `blur(<n>px)` with an optional `saturate(<n>)`. No
manifest or template SHALL carry a CSS transition or animation.

`skins/schema.json` SHALL name the canonical schemas in the `contracts` repository and SHALL be the
local validation target; no runtime cross-repo import is allowed. A vendored copy is permitted only
with the pinned `contracts` tag and a byte-equality test.

`skins/templates/ags-bar.gtk.css.j2` SHALL keep the app-local selector vocabulary for the settings
and Bluetooth surfaces and SHALL use `{{SKIN_*}}` placeholders for every visual constant; every
placeholder used SHALL be a token in `skins/schema.json`, and every required token SHALL be present
in every manifest.

Evidence: `scripts/validate-skins.py`, `skins/tests/`, `skins/README.md`; read-only input
`../ags-bar/style.css`.

#### Scenario: A literal colour enters a manifest or template

- **WHEN** a manifest or template contains a `#rrggbb` / `#rgb` literal, a transition or an
  animation
- **THEN** `make validate-skins` fails naming the file and the offending line

#### Scenario: A structure or variant token appears

- **WHEN** a manifest adds a `structure`, `variant`, `state` or other token outside the frozen v1
  groups
- **THEN** `make validate-skins` fails naming the unknown key and the frozen token group

#### Scenario: Placeholder and manifest coverage drift

- **WHEN** a template uses a `{{SKIN_*}}` name that is not in the schema, or a manifest omits a
  required token
- **THEN** `make validate-skins` fails naming the template token or the manifest and token:
  coverage is checked in both directions

#### Scenario: A manifest names an invented role

- **WHEN** a surface/ink expression names a role outside `palette.v1` (including a producer alias)
- **THEN** `make validate-skins` fails naming the role, because the 51-role vocabulary is the
  contract and an alias hides the intent

#### Scenario: The canonical schema is claimed but not vendored

- **WHEN** `skins/schema.json` claims a canonical tag or a vendored copy without the matching
  byte-equality evidence
- **THEN** `make validate-skins` fails: a pointer is honest, a false vendoring claim is not
