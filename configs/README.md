# configs — static, resolved configuration

This class holds configuration a consumer copies **unchanged**. Nothing here is rendered and
nothing here changes at runtime. That is the whole test for "does this file belong in
`configs/`": if a value must be substituted before the tool can read the file, it is not
config — it is a template.

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
| `hypr/*.lua` (13) | Hyprland | module bodies bind keys, windows and monitors; no value is render-time |
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

## What is deliberately **not** here

- **Jinja sources.** The shell's `.zshrc.j2` and wlogout's `style.css.tpl` consume render-time
  variables. They ship in `templates/`, each with a `*.vars.schema.json` beside it, in the
  slice that adds the render contract (v0.4.0). Copying a raw template into a config tree is
  the exact bug this boundary prevents: the tool would read `{{ … }}` literally.
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

The per-file boundary has no validator of its own at this tag — the class has no contract file
to parse, and a gate with no corpus rule would be a rule nobody has seen work. It is checked
at release time with three commands that must all succeed:

```bash
test -z "$(find configs -type f \( -name '*.j2' -o -name '*.tpl' \))" \
  && echo "no Jinja source under configs/"
test ! -e configs/btop/active-theme && echo "no mutable preference under configs/"
test ! -e configs/zsh/.zshrc && echo "no rendered output under configs/"
```

A template source arriving here fails the first check; a mutable preference fails the second;
a rendered file fails `make validate` as well as the third.

## Byte identity

Every file in this class was imported byte-for-byte from the corpus it replaces; `diff -r`
against the source tree returned 0 for all six directories before the consumer deleted its
copy. The import is an inventory move, not an edit: a changed byte here is a changed machine,
and it would have to be explained in the changelog rather than absorbed into a copy.
