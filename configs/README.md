# configs — deployment-fixed configuration

This class holds the configuration corpus: files deployed 1:1 to fixed paths. Twenty-four of the
25 are read exactly as they ship. The twenty-fifth, `hypr/hyprland.lua`, carries **one**
consumer-resolved path token and the consumer substitutes it on deploy; everything else in that
file is literal too.

The class rule is about the **destination and the contract**, not about whether a file contains
braces. A `templates/` file has a `*.vars.schema.json` beside it and renders into a path the
consumer chooses; a `configs/` file deploys 1:1 to a fixed path and its contract is the file
itself. `hyprland.lua` names the host's XDG config home because only the host knows it, and that
token is the one exception — documented below and asserted by the release check.

```text
hypr/                 13 Lua files — the Hyprland compositor configuration
hyprpaper/hyprpaper.conf
rofi/launcher/config.rasi
nvim/                 8 files — init.lua + lua/ modules (options, 6 plugins)
starship/starship.toml
wlogout/layout
```

25 files. `catalog.yaml` records the class and its subdirectories; the consumer's manifest
owns where each path deploys, so no destination appears here (spine AD-2/AD-6).

## The per-file boundary: static here, template elsewhere

| Path | Read by | Why it is static config |
| --- | --- | --- |
| `hypr/*.lua` (13) | Hyprland | 12 module bodies are fully static; `hyprland.lua` renders the one host path below and is otherwise static |
| `hyprpaper/hyprpaper.conf` | hyprpaper | wallpaper preload/profile syntax, literal paths chosen at run time by the tool |
| `rofi/launcher/config.rasi` | rofi | theme + layout; rofi reads `.rasi` directly |
| `nvim/**` (8) | Neovim | Lua modules; Neovim resolves its own plugins at start-up |
| `starship/starship.toml` | starship | prompt format; read as-is on every prompt |
| `wlogout/layout` | wlogout | the button layout only — **one file**, not a directory: see below |

`wlogout` is the one **per-file** entry in this class, and it is deliberate. wlogout reads two
files: `layout` (static, here) and `style.css` (**rendered**, not here). `style.css` is produced
from a Jinja source whose variables are the palette file path, the runtime state root, the
current wallpaper pointer, the font family and the font size — values that only exist on a
provisioned host. The source therefore belongs to `templates/`, and the rendered `style.css`
belongs to the consumer; this class ships exactly the half that is static. A directory copy
would have to carry the template and the resolved result together, which is the boundary
failure this split removes.

## The one render-time value

`hypr/hyprland.lua` resolves the directory its modules load from:

```lua
local cfg = "{{ compositor_configs_xdg_config_home }}/hypr"
```

The consumer substitutes that token during deploy — the value is the host's XDG config home,
which only the host knows — and the `dofile(cfg .. …)` lines below it then load the other twelve
files in this directory. The file says so in its own header. It stays in `configs/` because its
destination is fixed and it declares no variable contract; a `templates/` move would change its
addressed path and therefore be a MAJOR change. Every other file in this class is literal.

## What is deliberately **not** here

- **Jinja sources with a variable contract.** The shell's `.zshrc.j2` and wlogout's
  `style.css.tpl` consume several render-time variables and declare them in a
  `*.vars.schema.json` beside the source. They ship in `templates/`, in the slice that adds the
  render contract (v0.4.0). Copying a raw template into a config tree is the exact bug this
  boundary prevents: the tool would read `{{ … }}` literally. (`hyprland.lua` is the documented
  single-token exception above, not a precedent: it declares no contract and renders exactly one
  host path.)
- **Rendered output.** No `.zshrc`, no `style.css`, no rendered `kitty.conf` or `btop.conf`.
  The consumer renders those into its own config tree. Committing one would make this
  repository a second source of truth that drifts by construction (spine AD-11) — `make
  validate` fails on those file names.
- **Mutable preference and state.** btop's `active-theme` is a host preference written by the
  theme studio, and authored btop themes are content, not configuration. Neither is something
  a consumer copies unchanged, so neither is in this class.

## How the boundary is checked

`make validate` covers the envelope: the class and every declared subdirectory exist, every
subdirectory is declared, and no generated/mutable artifact name (`active-theme`, `.zshrc`,
`kitty.conf`, `btop.conf`, `settings.toml`, `icons.json`) appears anywhere in the tree.

`make validate-configs` (a `GATES` member with its own CI job since `v0.5.1`) implements the
four release-time commands below as executable checks. It fails naming the file and line, and
the second-token negative names both locations. Since `v0.6.1` it also parses `wlogout/layout`
and requires the single Logout tile's action to be exactly `uwsm stop`; a revert to the
user-wide `loginctl terminate-user` fails the gate (`BUG-001`).

```bash
make validate-configs
# PASS -- no template/mutable/rendered files; exactly one render token at configs/hypr/hyprland.lua:7; wlogout Logout action is 'uwsm stop'
```

The same rules, written as the manual commands the gate replaced:

```bash
test -z "$(find configs -type f \( -name '*.j2' -o -name '*.tpl' \))" \
  && echo "no Jinja source under configs/"
test ! -e configs/btop/active-theme && echo "no mutable preference under configs/"
test ! -e configs/zsh/.zshrc && echo "no rendered output under configs/"
grep -rn '{{' configs --exclude=README.md
# expect exactly one line: configs/hypr/hyprland.lua:7
```

A template source arriving here fails the first check; a mutable preference fails the second;
a rendered file fails `make validate` as well as the third; a second render-time token shows up
as an extra line in the fourth and must either move to `templates/` or be documented here.

## AGS startup: one launch lock, one identity per app

`hypr/autostart.lua` and `hypr/keybindings.lua` are the assets-owned AGS surfaces: the
provisioner reads them (and fails a deploy when an autostart line bypasses the lock) but never
writes them. Since `v0.6.2` every AGS cold start goes through the shared per-user wrapper
`ags-run-locked` (AD-28), installed by the consumer's `cli_tools` role into `~/.local/bin`:

```lua
bash -lc '$HOME/.local/bin/ags-run-locked --expect-instance <instance> ...'
```

The wrapper takes `$XDG_RUNTIME_DIR/ags-launch.lock` and releases it as soon as the named
instance registers on the AGS bus — not for the app's lifetime — so the existing stagger sleeps
(`sleep 2`/`3`/`4`) still order the launches without deadlocking login. `--expect-instance` is
mandatory here: an already-running instance is a no-op, and a name that never registers fails
the wrapper instead of leaving a silent half-start.

| Surface | Config dir | Instance | Launcher / log |
| --- | --- | --- | --- |
| status bar | `~/.config/ags` (default) | `ags` | autostart only |
| capture | `~/.config/ags-capture` | `capture` | `capture-ui` / `capture.log` |
| notifications | `~/.config/ags-notifications` | `notifications` | autostart / `notifications.log` |
| clipboard | `~/.config/ags-clipboard` | `clipboard` | `clipboard-ui` / `clipboard.log` |

The clipboard overlay was renamed to `clipboard` in `v0.6.2` (AD-35): config dir
`ags-clipboard`, instance `clipboard`, window `clipboard-window`, launcher `clipboard-ui` and
the keybind description “Open clipboard history”. The provisioned launcher template, the
`ags-clipboard` config link and the app itself are consumer/engine surfaces, not this corpus.
No live reference to the retired app name may remain under `configs/` or `desktop/`; the
historical mentions are confined to the changelog and the REQ-007 ticket record, which carries
the acceptance grep that proves the two class directories are clean.

## Byte identity

Every file in this class was imported byte-for-byte from the corpus it replaces; `diff -r`
against the source tree returned 0 for all six directories before the consumer deleted its
copy. The import is an inventory move, not an edit: a changed byte here is a changed machine,
and it would have to be explained in the changelog rather than absorbed into a copy.
