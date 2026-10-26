# `templates/` — Jinja sources and their variable contracts

This class holds **templates only**. A template's *values* belong to the consumer: this
repository ships what to render and which variables rendering needs, never a rendered file
(spine AD-8, AD-11). A rendered `kitty.conf`, `btop.conf`, `.zshrc` or `style.css` appearing
here fails `make validate` (the AD-11 absence check).

## Layout: one schema beside every template

```text
templates/
  zsh/.zshrc.j2                       zsh/.zshrc.vars.schema.json
  wlogout/style.css.tpl               wlogout/style.css.vars.schema.json
  kitty/kitty.conf.j2                 kitty/kitty.conf.vars.schema.json
  btop/btop.conf.j2                   btop/btop.conf.vars.schema.json
  display-manager/<name>.j2           display-manager/<name>.vars.schema.json   (five files)
```

- The schema is named after the template: `kitty.conf.j2` ⇄ `kitty.conf.vars.schema.json`
  (the `.j2`/`.tpl` suffix is replaced, so the pair is mechanical).
- A template with no sibling schema is a defect: the consumer has nothing to check its
  supplied values against.
- A schema with no sibling template is a defect too: it describes a contract nothing renders.

## What ships at `v0.6.0` — 9 templates, 9 schemas, 24 required variables, 1 optional

| Group | Template | Required | Optional | What it is |
| --- | --- | --- | --- | --- |
| `zsh/` | `.zshrc.j2` | 11 | 0 | the interactive shell: starship, oh-my-zsh, distro plugin paths, nvm/pyenv, the runtime palette `cat`, the `.zshrc.local` overlay |
| `wlogout/` | `style.css.tpl` | 5 | 0 | the logout stylesheet: palette import, runtime current/wallpaper + icons, font tunables |
| `kitty/` | `kitty.conf.j2` | 1 | 0 | kitty's config: one absolute include of the runtime palette |
| `btop/` | `btop.conf.j2` | 1 | 0 | btop's config: the selected theme **filename** + `save_config_on_exit = false` |
| `display-manager/` | `sddm.conf.j2` | 1 | 1 | SDDM + Pixie, Wayland greeter; optional `[Wayland] CompositorCommand` (default `weston --shell=kiosk`) |
| `display-manager/` | `config.toml.j2` | 2 | 0 | greetd: greeter type (branch) + greeter user |
| `display-manager/` | `regreet.toml.j2` | 3 | 0 | regreet appearance (retained fallback path) |
| `display-manager/` | `regreet.css.j2` | 0 | 0 | fixed GTK4 sheet (retained fallback path) |
| `display-manager/` | `hypr-session.j2` | 0 | 0 | fixed `/bin/sh` session launcher (retained fallback path) |

The SDDM template's optional variable is `display_manager_sddm_compositor_command`. The default
lives in the body (`default('weston --shell=kiosk')`), not in the schema, so a render with only the
required display-server value still produces a `[Wayland]` section with a command. A consumer that
installs another compositor passes the override; `make validate-templates` asserts both paths when
Jinja2 is importable, and always asserts the section and the exact fallback statically.

Zero variables is a real contract, not an omission: `required: []` plus
`additionalProperties: false` means a `{{ }}` added later fails the gate until a property is
declared. Three of the nine are also **unrendered at this tag** — the greetd+regreet fallback
is retained but the consumer's default login path is SDDM + Pixie (spine AD-9). Their schemas
still describe the values that path would need.

## Schema shape

Each schema is a JSON Schema (draft 2020-12) for the template's render context, extended with
four keys:

| Key | Meaning |
| --- | --- |
| `schema_major` | integer; the consumer-compatibility version (spine AD-12) — independent of the repo tag |
| `template` | the sibling template's file name, so the pair is checkable without guessing |
| `optional` | the declared complement of JSON Schema's `required` |
| `additionalProperties: false` | closed world: a variable the template does not consume is a consumer defect |

`required` names what the consumer **must** supply. It is derived from the variables the
template actually reads — not from the consuming role's whole variable set, which is always
larger and would make every template appear to need everything.

**`{{ }}` is not the whole contract.** `display-manager/config.toml.j2` reads its greeter type
in an `{% if %}` branch; a `{{ }}`-only count reports one variable and misses it. The validator
reads both expression forms, which is why the contract for that file requires two names.

**Empty is a value, absent is not.** The five zsh plugin paths are *required* and may be an
empty string: an absent plugin is a decision the consumer expresses explicitly, while an
absent variable is a render error. That is why they are not `optional`.

## Rules `make validate-templates` enforces

1. every `*.j2` / `*.tpl` has a sibling `*.vars.schema.json`, and every schema names a
   sibling template that exists;
2. every name the template reads (in `{{ }}` **or** `{% %}`) appears in `properties`, and
   every `properties` entry is read by the template — contract **equals** body;
3. `required ∪ optional` is exactly `properties`; the two lists are disjoint, and every name
   is typed;
4. **no `default(` on a required variable** — a fallback on a required value turns "the
   consumer forgot it" into "the file rendered with a wrong value" (spine AD-8.2);
5. `required` is non-empty whenever the template reads a name;
6. every keyword is a real 2020-12 keyword (or an `x-` extension) with a value of the right
   type, recursively — a misspelled keyword is a rule nothing enforces;
7. the SDDM template carries an explicit `[Wayland]` section and `CompositorCommand` that reads the
   optional variable and defaults to `weston --shell=kiosk`; the variable is optional in the schema,
   and the rendered fallback/override are asserted when `jinja2` is importable.

The validator is stdlib-only so a fresh clone passes with no virtualenv; when `jsonschema` is
importable it additionally validates each schema against the 2020-12 metaschema and proves the
closed-world and required-missing claims with negative instances. When `jinja2` is importable it
also renders the SDDM body with the required variable only and with the optional override. Both
extra modes are printed as a NOTE when skipped, never silently assumed.

## What this class is not

- Not a place for values, secrets, host names or per-machine settings.
- Not a place for the *rendered* result (AD-11).
- Not a place for a template whose schema only one consumer could satisfy: the schema is the
  public surface, and it must be sufficient for any consumer to supply a correct context.
