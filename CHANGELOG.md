# Changelog

Notable changes to `dotfiles-assets`. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved). This repository ships no build artifacts: a
release is a tag with notes, and the corpus is the source.

## [0.6.0] — 2026-10-26

### Added

- **An explicit SDDM Wayland greeter compositor.** `templates/display-manager/sddm.conf.j2` now
  renders a `[Wayland]` section after `[General]`:
  `CompositorCommand={{ display_manager_sddm_compositor_command | default('weston --shell=kiosk') }}`.
  The rendered config no longer relies on SDDM's implicit `Weston` default; a host that sets
  `DisplayServer=wayland` and does not install `weston` can now be failed at deploy time instead of
  falling back to `DisplayServer=x11-user` at the greeter.
- **Optional `display_manager_sddm_compositor_command`** in
  `templates/display-manager/sddm.conf.vars.schema.json`: a non-empty string, listed in `optional`
  only, with **no schema-level default** — the fallback lives in the template body. `required` still
  names only `display_manager_sddm_display_server`; `schema_major` stays **1** because the addition
  is optional and additive.
- **`make validate-templates` asserts the SDDM contract.** The gate fails when the `[Wayland]`
  section, the `CompositorCommand` line or the `weston --shell=kiosk` fallback disappears, or when
  the variable stops being optional. When `jinja2` is importable it renders the body with the
  required variable only (fallback) and with the override (consumer value); the stdlib-only run
  still asserts the section and the exact default expression.

### Changed

- `catalog.yaml` records **24 required variables and 1 optional** for `templates/` and moves the
  corpus tag to `v0.6.0`; `README.md`, `templates/README.md` and the OpenSpec capability spec carry
  the new inventory and the SDDM scenario.

### Not here, on purpose

No `weston` package, role variable, SDDM service change or pin bump: the consumer's
`display_manager` role installs the package, passes the optional value and updates its own mirrors
to `v0.6.0`. No rendered `sddm.conf` is committed.

## [0.5.1] — 2026-10-22

### Added

- **`scripts/validate-configs.py` / `make validate-configs` (R-05/R-06).** A new `GATES` member
  with its own CI job: no `*.j2`/`*.tpl` source under `configs/`, no mutable preference
  (`active-theme`, `theme-map.yaml`) or rendered output (`.zshrc`, `kitty.conf`, `btop.conf`,
  `settings.toml`, `icons.json`, `style.css`), every file non-empty, and exactly one render token
  at `configs/hypr/hyprland.lua:7` (`{{ compositor_configs_xdg_config_home }}`). A second token
  fails naming both files and lines; a stray `.j2` fails naming the file. This turns the four
  release-time manual commands in `configs/README.md` into an executable release gate.

### Notes

- **No corpus bytes changed.** This is a validator/gate PATCH; consumers pinned at `v0.5.0` see
  the same corpus. Per the release-runbook rule (R-12), a docs/gate-only correction ships as a
  new tag and does not force a consumer pin bump when the corrected file is not a consumed
  surface.

## [0.5.0] — 2026-10-22

### Added

- **`desktop/` corpus, imported verbatim.** Six `.desktop` entries in `desktop/applications/` and
  `toggle-touchpad` in `desktop/scripts/` (mode `0755` preserved), copied from the consumer corpus.
  `cmp` returns 0 for the script; each entry differs from its source by exactly **one added line**,
  its `TryExec=`, which layer 1 requires and the pre-split corpus never carried. Every packaged
  `Exec`, comment, category, MIME type and startup hint is unchanged.
- **`TryExec=` on all six entries.** A launcher probes `TryExec` to decide whether an application is
  installed; without it a missing binary still produced a listed, dead menu entry. The value is the
  binary `Exec` launches — the IDE/TIDAL binary for the four overrides, `kitty` for the two
  kitty-hosted CLIs.
- **`desktop/desktop.yaml`, the class contract** (`schema_major: 1`): one record per entry,
  `{file, requires, optional}`. `requires` is the entry's own launcher (`basename(Exec argv[0])`,
  which is also its `TryExec`); `optional` is the payload a wrapper entry runs inside that launcher
  (`codex`, `copilot`). The consumer resolves `requires` before it deploys — a missing one fails the
  run naming entry and binary — and reports/skips an entry whose `optional` binary is absent. The
  corpus never decides whether a package is installed.
- **`scripts/validate-desktop.py` / `make validate-desktop`** (`validate-desktop` is a `GATES`
  member with its own CI job). Layer 1 of AD-10: every entry parses as a Desktop Entry
  (`[Desktop Entry]`, `Type`, `Name`, `Exec`, `Icon`), `Exec` is tokenized with the spec's quoting
  rules and its argv[0] basename must be a declared `require`, `TryExec` must be present and name
  that same binary, the contract must equal the `.desktop` set exactly in both directions, and every
  script must be executable with a `#!` shebang. The same target runs `shellcheck` over
  `desktop/scripts/*` (and `make lint` stays the class-independent sweep).
- **`desktop/README.md`** — the three validation layers and their owners, the `TryExec` rationale,
  the `requires`/`optional` derivation, the scope boundary (the Jinja launcher wrappers stay with
  the consumer's `cli_tools` role) and the vacuity proof.

### Changed

- **`catalog.yaml` declares `desktop` schema-bearing** (`desktop/desktop.yaml`, `schema_major: 1`)
  and records the real contents. `desktop/` is no longer "empty in a later tag": all five classes
  are populated at this tag.
- **`validate-catalog.py` reads a YAML contract as well as a JSON one.** The class contract for
  `desktop` is YAML, so the `schema_major` rule (AD-12) is applied through the same strict subset
  parser rather than a JSON-only path. The subset gained sequence-of-mappings items
  (`- file: x.desktop`) so a record list parses; anything outside the subset is still a hard error.
- **`make lint` is no longer vacuous.** `desktop/scripts/` holds `toggle-touchpad`, so
  `shellcheck` now has a real subject; the vacuous-pass message remains for a future empty class.

### Not here, on purpose

No launcher wrappers (`rofi-ui`, `capture-ui`, `hypr-pano-ui`, `wallpaper-selector-ui`,
`icon-color-mapping-editor`, `btop-theme-studio`): they are Jinja-rendered by the consumer's
`cli_tools` role because they bake in installed-binary paths (AD-10 scope boundary). No installed
binaries, no `mimeapps.list`, no launcher database: a declared binary is not an installed package,
and derived state belongs to the host.

## [0.4.0] — 2026-10-22

### Added

- **`templates/` corpus, imported verbatim.** Nine Jinja sources in five group directories, copied
  byte-for-byte from the consumer corpus with their bodies unchanged: `zsh/.zshrc.j2`,
  `wlogout/style.css.tpl`, `kitty/kitty.conf.j2`, `btop/btop.conf.j2` and the five
  `display-manager/{sddm.conf,config.toml,regreet.toml,regreet.css,hypr-session}.j2`. `diff` against
  the consumer's sources returned 0 for every file before the consumer deleted its copies.
- **Nine `*.vars.schema.json` contracts, one beside every template.** Each is a draft 2020-12
  object schema with `schema_major: 1`, the sibling `template`, typed `properties`, disjoint
  `required`/`optional` and `additionalProperties: false`. Together they declare **24 required
  variables and zero optional** — every name is one the body actually reads.
- **`scripts/validate-templates.py` / `make validate-templates`** (`validate-templates` is a
  `GATES` member, with its own CI job). It asserts: complete pairing in both directions; every read
  appears in `properties` and every property is read (**contract equals body**, so a required name
  the template never reads cannot exist); `required ∪ optional == properties`; no `default(` on a
  required variable; `required` non-empty whenever the template reads something; and every keyword
  is a real 2020-12 keyword (or an `x-` extension) with a correctly typed value. Stdlib-only; when
  `jsonschema` is importable it additionally validates each schema against the 2020-12 metaschema
  and proves the closed-world / required-missing claims with negative instances, and says so when
  that mode is skipped.
- **`catalog.yaml`** — `templates` declares its five group subdirectories, its real contents and a
  **glob** contract (`templates/**/*.vars.schema.json`); `validate-catalog.py` learned to hold every
  glob match to the catalog's `schema_major` instead of one arbitrary representative file.

### Changed

- **`{{ }}` is not the whole contract.** The validator reads `{% %}` expressions too, so
  `display-manager/config.toml.j2` requires **two** names (`display_manager_greeter_type` in its
  `{% if %}`, `display_manager_greeter_user` in the `[default_session]` line). The plan's "1 var"
  figure came from a `{{ }}`-only grep and under-counted the branch variable.
- **Three display-manager templates are contracts, not live renders.** `regreet.toml.j2`,
  `regreet.css.j2` and `hypr-session.j2` are retained for the consumer's greetd+regreet fallback
  (spine AD-9); the default login path is SDDM + Pixie. Their schemas describe the values that path
  would need, and two of them are legitimately variable-free (`required: []`).
- **`templates/example.vars.schema.json` removed.** The shape file is retired now that nine real
  contracts exist; `templates/README.md` carries the schema shape, the inventory and the rules.
- **`wlogout/style.css.tpl` keeps its source mode.** The imported file is `100755` in the consumer
  repository; the mode came along with `cp -a`. Content (not mode) is the contract.

### Not here, on purpose

No rendered `.zshrc`, `style.css`, `kitty.conf` or `btop.conf`: the templates and their contracts
ship, the values stay with the consumer (AD-8/AD-11). `make validate` fails on any of those names.

## [0.3.1] — 2026-10-21

### Fixed

- **The `configs/` boundary prose was wrong for `hypr/hyprland.lua`.** The v0.3.0 README claimed
  "nothing here is rendered"; in fact `hyprland.lua:7` carries one consumer-resolved token
  (`{{ compositor_configs_xdg_config_home }}`, the directory its twelve modules are loaded from)
  and the consumer renders it on deploy — the file says so in its own header. The class is now
  described as **deployment-fixed** rather than "static": the rule is the fixed destination and the
  absent variable contract, not the absence of braces. The documented exception, the one-token
  acceptance grep and a scenario for a second token were added to `configs/README.md` and the
  spec. Corpus bytes are identical to v0.3.0 — this is a documentation correction, and the tag is
  new rather than moved.

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
