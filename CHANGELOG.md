# Changelog

Notable changes to `dotfiles-assets`. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved). This repository ships no build artifacts: a
release is a tag with notes, and the corpus is the source.

## [0.3.0] — 2026-10-21

### Added

- **`configs/` corpus, imported verbatim.** 25 static config files in six tool directories: 13
  Hyprland Lua files, `hyprpaper/hyprpaper.conf`, `rofi/launcher/config.rasi`, 8 Neovim files,
  `starship/starship.toml` and `wlogout/layout`. Copied byte-for-byte — `diff -r` returned 0 for all
  six directories before the consumer deleted its copy — so every consumer destination keeps the
  bytes it had. `configs/README.md` documents the per-file boundary and the exclusions.
- **wlogout is one file, not a directory.** `layout` is static config and ships here; `style.css` is
  rendered from a five-variable Jinja source whose values (palette path, runtime state root, current
  wallpaper, font family, font size) only exist on a provisioned host. The source is the `templates`
  class (v0.4.0) and the rendered file is the consumer's. A directory copy would have carried both
  halves together — the boundary failure this split removes.

### Changed

- `catalog.yaml` — `configs` declares its six subdirectories and its real contents, and `tag` moves
  to `v0.3.0`. The class enumerates no schema file (`schema_major: null`, deliberate).
- `openspec/specs/assets-catalog/spec.md` — a requirement for the static-config boundary, with the
  three acceptance commands that prove it.
- `README.md` — the status line names `configs` as populated, and the contracts section states that
  this class's contract is a boundary rather than a schema document.
- **`[0.2.0]` heading corrected.** The v0.2.0 corpus entry was still filed under `[Unreleased]` in
  the tagged tree; it now carries the version it actually shipped as. Documentation only — the
  tag's bytes are untouched.

## [0.2.0] — 2026-10-21

### Added

- **`icons/` corpus, imported verbatim.** 117 SVGs in 12 template directories, copied
  byte-for-byte from the dotfiles corpus. `icons/mappings/defaults.yaml` is the group-independent
  `COLOR_*` vocabulary, **not** a group map; `icons/mappings/icons.yaml` is the one group map.
  `icons/README.md` documents the group/template/output shape and the placeholder merge order.
- **Six stale duplicate mapping files retired (deviation from the verbatim import).**
  `battery.yaml`, `email-client.yaml`, `network.yaml`, `power-menu.yaml`,
  `wallpaper-selector.yaml` and `wlogout.yaml` were removed instead of imported. Evidence: the ITR
  loader takes a single YAML path and the runtime and `sync-icons-manifest` read `icons.yaml` only,
  so nothing loaded them; they duplicated groups owned by `icons.yaml` and had drifted
  (`network.yaml` referenced 12 templates deleted in the network rework, and `battery.yaml` /
  `power-menu.yaml` carried different variant sets or `color_mappings`). `icons.yaml` and
  `defaults.yaml` remain byte-identical to the source. `make validate-icons` now fails if any other
  `*.yaml` appears under `icons/mappings/`, so the split cannot recur.
- **`content/` corpus, imported verbatim.** `content/wallpapers/wallpapers.tar.gz` is the original
  archive, **not repacked** (its bytes are the contract; the runtime derives a hash from them) and
  holds a top-level `default.png`. `content/btop-themes/` holds authored themes only — empty today —
  and never the mutable active-theme preference (spine AD-11). `content/README.md` says why.
- **`scripts/validate-icons.py` / `make validate-icons`** — the gate the corpus never had: every
  mapping `template:` resolves under the templates root (honouring a group's `template_dir`), every
  `{{COLOR_*}}` token used by a template is declared in `defaults.yaml` or that group's / variant's
  `color_mappings`, every SVG parses as XML, variant names are unique per group, `output` is a bare
  file name, and `mappings/` holds exactly one group map plus the vocabulary. It reports unused
  tokens and unreferenced templates without failing the tag.
- **`scripts/validate-content.py` / `make validate-content`** — the tarball contains a top-level
  `default.png`, every `*.theme` is non-empty, and no archive member escapes the archive root.
- **`icons/schema.json` extended** to the concrete consumer shape: `group → color_mappings →
  variants[{name, template, output}]`, variant paths relative to the group's template root, the
  group/consumer metadata fields, and the lowest-to-highest merge order. It also corrects the
  skeleton's "a group is a directory" statement: a group is a top-level key, and only
  `template_dir` selects a directory.
- **`Makefile` / `.github/workflows/gates.yml`** — `GATES` is now `validate validate-icons
  validate-content lint hermetic`, with one CI job per gate and `ci-gates-parity` still comparing
  the two lists in both directions. `hermetic` runs both class validators with empty `HOME`/`XDG_*`
  from a foreign cwd.
- **`catalog.yaml`** — `content/` declares its `wallpapers` and `btop-themes` subdirectories, and
  every class states what it actually holds at this cut.

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
