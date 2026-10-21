# Changelog

Notable changes to `dotfiles-assets`. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved). This repository ships no build artifacts: a
release is a tag with notes, and the corpus is the source.

## [Unreleased]

## [0.1.0] — skeleton — 2026-10-21

First release, deliberately empty. The point of tagging an empty corpus is to prove the release
ritual (gates green → changelog → annotated tag → CI green → anonymous clone passes) before the
expensive migration depends on it.

### Added

- **Five class directories** with the layout consumers will address literally: `icons/templates/`,
  `icons/mappings/`, `templates/`, `configs/`, `content/`, `desktop/applications/`,
  `desktop/scripts/`. Each is `.gitkeep`-backed so it survives a clone. `catalog.yaml` records all
  five with `contents: empty in v0.1.0` and a `schema_major` for the two schema-bearing classes.
- **`icons/schema.json`** (`schema_major: 1`) — the icons contract: a group's `variants[]` carry
  `{name, template, output}` with `template` relative to the templates root, plus the
  `{{COLOR_*}}` placeholder vocabulary rules. New work: no schema file existed in the corpus
  before this repository.
- **`templates/README.md` + `templates/example.vars.schema.json`** (`schema_major: 1`,
  `required[]` / `optional[]`) — the shape every `*.vars.schema.json` takes once the templates
  land. The `example.` prefix marks it as the shape, not a live contract.
- **`scripts/validate-catalog.py`** — one stdlib-only validator for the corpus envelope: catalog
  ⇄ class-dir agreement (including undeclared subdirectories), schema JSON well-formedness and
  `schema_major` agreement, and the mechanical **absence check** for generated/mutable artifacts
  (`icons.json`, `settings.toml`, rendered `kitty.conf` / `btop.conf` / `.zshrc`, `active-theme`).
  Stdlib-only on purpose: `make gates` must pass on a fresh clone with no virtualenv and no network.
- **`Makefile`** — `help validate lint gates gates-ci ci-gates-parity hermetic`, all anchored on
  `$(CURDIR)`. `lint` runs shellcheck over `desktop/scripts/**` (a vacuous pass that says so out
  loud while the directory is empty) and `compileall` over `scripts/` with bytecode written outside
  the tree. `hermetic` re-runs the checks with `env -i`, empty `HOME`/`XDG_*` and a foreign cwd.
- **`.github/workflows/gates.yml`** — one job per `make gates` target plus `ci-gates-parity`, which
  compares the workflow's job keys against the Makefile's `GATES` in both directions so the two
  lists cannot drift.
- **mu-strict harness, byte-identical to `mu`**: `scripts/worktree-guard.sh`, `skills-lock.json`,
  `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/LIFECYCLE.md`, `tickets/_template/`,
  `tickets/_fixtures/`. `AGENTS.md` carries mu's evidence rule, routing, worktree and
  planning-vs-code rules verbatim, with only the charter (§2) and the repo-specific gates (§4)
  retargeted; `CLAUDE.md` is a symlink to it.
- **`openspec/`** — the `assets-catalog` capability spec plus the `repo-birth` change that produced
  this release, and `tickets/REQ-001` recording the birth.

### Not here, on purpose

No `src/`, no importable package, no `[project.scripts]`, no engine, no build, install or sync
verb. `pyproject.toml` is dev-only tooling (`package = false`, no build system) for the class
validators that arrive with their corpora.
