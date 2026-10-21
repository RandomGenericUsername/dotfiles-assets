# icons — SVG templates, one color-mapping manifest, and the placeholder vocabulary

This class holds the icon corpus. It is addressed by consumers as data; nothing here
is generated and nothing here names a deployment destination (spine AD-2/AD-6).

```text
templates/   117 SVGs in 12 template directories (the rendered artwork)
mappings/    icons.yaml (the ONE group map) + defaults.yaml (the COLOR_* vocabulary)
schema.json  the contract: group -> color_mappings -> variants, template resolution
```

## One manifest, one vocabulary

`mappings/` holds exactly two files:

- `icons.yaml` — the group map: group name → `color_mappings` → `variants`.
- `defaults.yaml` — the group-independent `COLOR_*` vocabulary. It is **not** a
  group map and it renders nothing.

Per-group splitting is deliberately **not supported**. A consumer loads **one**
mapping file per render, so several group-map files are several sources of truth
that drift by construction. `make validate-icons` fails if any other `*.yaml`
appears under `mappings/`.

The six legacy per-concern files (`battery.yaml`, `email-client.yaml`,
`network.yaml`, `power-menu.yaml`, `wallpaper-selector.yaml`, `wlogout.yaml`) were
retired in `v0.2.0`. They duplicated groups owned by `icons.yaml`, and
`network.yaml` had drifted so far that it referenced 12 templates deleted when the
network group was reworked (`dotfiles-v3@37fd3958`). Nothing loaded them: the ITR
loader takes a single YAML path, and the runtime and `sync-icons-manifest` read
`icons.yaml` only. The verbatim import was therefore trimmed by exactly those six
unread duplicates; `icons.yaml` and `defaults.yaml` are byte-identical to the source.

## How a `template` path resolves

`variants[].template` is relative to the **group's template root**:

```text
templates_root / (group.template_dir or ".") / variants[].template
```

`template_dir` is optional and defaults to `"."`, so with no `template_dir` the path
is relative to `templates/` itself — e.g. `status-bar/battery/battery-0/default/icon.svg`.
A group is a logical name, not necessarily a directory: `battery`, `network` and
`wifi-*` all live under `status-bar/`. An `output` is a bare file name, never a path.

## Placeholders

SVGs carry `{{COLOR_NAME}}` tokens only. A token is satisfied by the merge, lowest
priority first: `defaults.yaml` → the group's `color_mappings` → the variant's
`color_mappings`. No defaults, filters or whitespace inside a token. A rendered SVG
is never committed here (spine AD-11).

## Gate

```bash
make validate-icons
```

fails the release, naming the file, when a mapping `template:` does not resolve,
when a token used by a template is declared for neither the group nor the vocabulary,
when an SVG is not well-formed XML, when an `output` is not a bare file name, or
when a second group-map file appears beside `icons.yaml`. It reports (without
failing) an unused declared token and an unreferenced template.

The contract itself is `schema.json`; the corpus checks it describes are the ones
above, so a change to the shape and a change to the checker land together.
