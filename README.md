# dotfiles-assets

The dotfiles corpus, as **data**: five class directories behind **one** annotated semver tag.
No package, no console script, no engine — the icon renderer, the palette generator and the
provisioner are separate pinned repos, and a renderer growing here would re-open the split that
created this repository.

**Workspace.** The corpus is developed beside its consumers under `~/Development/dotfiles/`. The
canonical ownership/pin map is
[`../dotfiles-v3/docs/WORKSPACE.md`](../dotfiles-v3/docs/WORKSPACE.md). This repo's release tag is
`v0.6.0`; the composition still consumes `v0.5.0` until its own pin bump (the `validate-configs`
gate is repo-only and `v0.6.0` adds the optional SDDM compositor contract).

```text
icons/       templates/  (one directory per icon group)      mappings/  (group -> color, + defaults)
templates/   Jinja sources + one *.vars.schema.json per template
configs/     static config corpus (compositor, editor, prompt, wlogout layout)
content/     binary/large content (wallpapers, authored themes)
desktop/     applications/*.desktop + scripts/ + desktop.yaml (requires/optional)
```

`catalog.yaml` is what is inside each class, with a `schema_major` per schema-bearing class. It
says what the corpus *is*; it deliberately names no destination and no path outside this
repository — that map belongs to whoever deploys the corpus.

**Status: all five classes are populated.** `icons/` holds 117 SVG templates in 12 template
directories plus one group map and its vocabulary; `content/` holds the unmodified wallpaper archive
and the authored btop-theme class (empty today); `configs/` holds 25 deployment-fixed config files in
six tool directories — the compositor, editor, prompt and wlogout layout (one file,
`hyprland.lua`, carries a single host path the consumer renders; the rest are literal);
`templates/` holds nine Jinja sources with nine vars schemas (24 required variables and one optional
SDDM greeter compositor command, defaulting to `weston --shell=kiosk`), each imported with its body
unchanged; `desktop/` holds six application entries and the
`toggle-touchpad` helper, with `desktop/desktop.yaml` declaring each entry's `requires`/`optional`
binaries. Each class validator arrives **with** its corpus, so every check has run against real data
before it can gate a tag. The `configs/` boundary is `make validate-configs` since `v0.5.1`: it
rejects a Jinja source, a mutable/rendered file, or a second render token, and names
`configs/hypr/hyprland.lua:7` as the one reviewed exception.

## Two version numbers, deliberately independent

| Number | Where | Answers |
| --- | --- | --- |
| tag `vMAJOR.MINOR.PATCH` | the git tag | *which corpus* is deployed |
| `schema_major` | `icons/schema.json`, `templates/**/*.vars.schema.json`, `desktop/desktop.yaml` | *can a consumer parse it* |

- **MAJOR** — a contract or path break: class directory renamed, a file the consumer addresses by
  path moved or removed, a mapping vocabulary rename, a template's required variable removed or
  retyped, or a `schema_major` bump.
- **MINOR** — additive only: a new icon group/variant, a new template (with its own first
  `schema_major`), a new `.desktop` entry, a new wallpaper.
- **PATCH** — content fix that keeps every path: an SVG recolor, a re-encoded wallpaper, a text
  fix in a mapping.

A published tag is **never moved or deleted**; a fix ships as a new tag. A consumer pins
`repo@tag`, so a moved tag would silently change a machine that was already verified.

## Contracts

- `icons/schema.json` — `schema_major: 1`; group → `color_mappings` →
  `variants[{name, template, output}]`, where `template` is relative to the group's template root
  (`icons/templates/<template_dir>`, `template_dir` defaulting to `"."`); the `{{COLOR_*}}`
  placeholder vocabulary and merge order. `make validate-icons` enforces it against the corpus:
  every mapping template resolves, every used placeholder is declared, every SVG parses, and no
  second group-map file exists beside `icons.yaml`.
- `templates/<group>/<name>.vars.schema.json` — one contract per template: JSON Schema for the
  render context plus `schema_major`, `template` and `optional`, closed with
  `additionalProperties: false`. `required` equals the names the template body reads (in `{{ }}`
  **or** `{% %}`), never a consumer's variable set. The SDDM schema also declares one optional
  compositor command, defaulted in the template body to `weston --shell=kiosk`; the rendered
  `[Wayland]` section never depends on SDDM's implicit default. `make validate-templates` enforces
  the pairing, the body equality, the no-`default(`-on-required rule and the SDDM Wayland assertion;
  `templates/README.md` carries the inventory and the rules.
- `desktop/desktop.yaml` — `schema_major: 1`; one record per entry: `{file, requires, optional}`.
  `requires` is the entry's own launcher binary (`basename(Exec argv[0])`, which is also its
  `TryExec`); `optional` is the payload a wrapper entry runs inside that launcher. The consumer
  resolves `requires` before it deploys (a missing one fails the run) and skips the entry when an
  `optional` binary is absent. `make validate-desktop` enforces the Desktop Entry parse, the
  `Exec`/`TryExec` ↔ `requires` equality, the exact contract ↔ `.desktop` set in both directions,
  and the scripts' mode + shebang; the same target runs `shellcheck`. `desktop/README.md` carries
  the rules.
- `configs/` bears **no** schema file: its contract is a boundary, not a document. `configs/README.md`
  states it — static, resolved config only; Jinja sources are the `templates` class, and rendered
  files and mutable preferences belong to the consumer.

## Gates

Every verb is anchored on the repository root, so `make -C <clone> gates` works from anywhere.

```bash
make help             # the verbs below
make validate         # catalog <-> class dirs, schema JSON, and the generated-artifact absence check
make validate-icons   # mapping templates resolve, {{COLOR_*}} tokens declared, every SVG parses
make validate-content # the tarball holds a top-level default.png; every *.theme is non-empty
make validate-templates # one vars schema per *.j2/*.tpl; the schema equals the body it describes
make validate-configs # deployment-fixed configs; exactly one reviewed render token
make validate-desktop # Desktop Entry parse, Exec/TryExec ↔ requires, contract ↔ entries, shellcheck
make lint             # shellcheck over desktop/scripts/** + compileall scripts/
make gates            # validate + validate-icons + validate-content + validate-templates + validate-configs + validate-desktop + lint + hermetic
make hermetic         # the same, with empty HOME/XDG_* from a foreign cwd
make ci-gates-parity  # the workflow's job set == the Makefile's gate set, both directions
```

`make hermetic` is not decoration: it is the reproduction command for "green because the corpus is
green, not because this host happens to have something provisioned".

**.github/workflows/gates.yml** runs one job per gate. `scripts/ci-gates-parity.py` compares that
job set against the `Makefile`'s `GATES` and fails naming anything unmatched **in either
direction**, so a gate cannot run only on a laptop and a CI-only job cannot hide from developers.

### Generated and mutable artifacts are never assets

`icons.json`, `settings.toml`, a rendered `kitty.conf` / `btop.conf` / `.zshrc`, palette/`current/`
state and a mutable `active-theme` are produced by the consumer or by the runtime. Committing one
would make this repository a second source of truth that drifts by construction. This is
mechanical, not a convention: `make validate` fails and names the offending path. Prove it:

```bash
touch icons/mappings/icons.json && make validate   # non-zero, names icons/mappings/icons.json
rm icons/mappings/icons.json && make validate      # exit 0
```

## How `dotfiles-v3` pins this repository

`dotfiles-v3` is the composition repo. It carries a manifest entry naming this repository and an
exact tag, mirrors that pin in its role variables and in its verify assertions (locked by a parity
test), fetches the tag **once** into its own install tree, and deploys the class directories it
needs from that checkout. Two consequences worth stating:

- **This repository names no destination.** The consumer's manifest owns the destination map; a
  spine path committed here would be a second, unowned copy of it.
- **A pin bump is its own commit in the consumer**, and only after this repository's gates are
  green on that tag. The consumer's rollback is a pin bump back, which is why the tag is immutable.

## Releasing

1. `make gates` green on the commit to be tagged.
2. `CHANGELOG.md` gets the version (`catalog.yaml` too, if the class inventory changed).
3. Annotated tag: `git tag -a vX.Y.Z -m "..."`.
4. Push the commit and the tag; CI must be green on the tagged commit.
5. Announce the tag; consumers bump their pin in their own commit.

## Licence

MIT — see `LICENSE`. This repository ships no build artifacts: a release is a tag with notes, and
the corpus *is* the source.
