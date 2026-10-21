# icons — SVG templates, their color mappings, and the placeholder vocabulary

This class holds the icon corpus. It is addressed by consumers as data; nothing here
is generated and nothing here names a deployment destination (spine AD-2/AD-6).

```text
templates/   117 SVGs in 12 template directories (the rendered artwork)
mappings/    one YAML per icon concern, plus the COLOR_* vocabulary
schema.json  the contract: group -> color_mappings -> variants, template resolution
```

## `defaults.yaml` is the vocabulary, not a group

`mappings/defaults.yaml` is the one mapping file whose top-level key is `defaults`
rather than a group name. It declares the group-independent `COLOR_*` vocabulary
(`COLOR_FOREGROUND`, `COLOR_BACKGROUND`, `COLOR_SECONDARY`, `COLOR_ACCENT`). It is
not an icon group and it renders nothing. Every other mapping file is a mapping of
**group name → group entry**.

## Which mapping file a consumer reads

A consumer loads **one** mapping file per render. `mappings/icons.yaml` is the
manifest the current pipeline renders (it owns the groups and their `bar_mappings`);
the per-concern files (`battery.yaml`, `network.yaml`, `power-menu.yaml`,
`wallpaper-selector.yaml`, `wlogout.yaml`, `email-client.yaml`) ship in the same
class and are deployed alongside it for consumers that address them directly.

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
when an SVG is not well-formed XML, or when an `output` is not a bare file name. It
reports (without failing) an unused declared token, an unreferenced template, and a
group defined by more than one mapping file.

The contract itself is `schema.json`; the corpus checks it describes are the ones
above, so a change to the shape and a change to the checker land together.
