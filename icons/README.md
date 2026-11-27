# icons — SVG templates, one group map, the role vocabulary, and the typed token grammar

This class holds the icon corpus. It is addressed by consumers as data; nothing here
is generated and nothing here names a deployment destination (spine AD-2/AD-6).

```text
templates/   106 SVGs in 13 template directories (the rendered artwork)
mappings/    icons.yaml (the ONE group map) + defaults.yaml (the COLOR_* vocabulary)
             + vocabulary.json (the declared roles) + ROLE-MIGRATION.md (the role proposal)
schema.json  the contract: schema_major 2, token families, surfaces, styles,
             group -> color_mappings -> variants, template resolution
```

## One manifest, one vocabulary

`mappings/` holds exactly two **mapping** files:

- `icons.yaml` — the group map: group name → `surface`/`serves`/`styles` →
  `color_mappings` → `variants`.
- `defaults.yaml` — the group-independent `COLOR_*` vocabulary. It is **not** a
  group map and it renders nothing.

Two companions sit beside them and are not mappings: `vocabulary.json` declares the
roles a COLOR_* value may name (the 50 Material roles + `on_backdrop`) and
`ROLE-MIGRATION.md` is the reviewed group/variant → role proposal. A consumer loads
neither.

Per-group splitting is deliberately **not supported**. A consumer loads **one**
mapping file, so several group-map files are several sources of truth that drift by
construction. `make validate-icons` fails if any other `*.yaml` appears under
`mappings/`.

The six legacy per-concern files (`battery.yaml`, `email-client.yaml`,
`network.yaml`, `power-menu.yaml`, `wallpaper-selector.yaml`, `wlogout.yaml`) were
retired in `v0.2.0`. They duplicated groups owned by `icons.yaml`, and
`network.yaml` had drifted so far that it referenced 12 templates deleted when the
network group was reworked. Nothing loaded them: the ITR loader takes a single YAML
path, and the runtime and `sync-icons-manifest` read `icons.yaml` only.

## Token families (schema_major 2)

The only two families; the name carries the family and the value space follows:

| Token | Value |
| --- | --- |
| `{{COLOR_*}}` | a role declared in `vocabulary.json`, or a `#rrggbb` literal |
| `{{OPACITY_*}}` | a numeric literal in `[0, 1]` (`1` = fully present, `0` = removed) |

Any other token name is invalid, and a value outside its family's value space (a
role as an opacity, a number as a colour) fails the gate. `OPACITY_*` is a *render
parameter*, never a state language of its own: adjacent bar states differ by shape,
and the level families dim strips that are always drawn.

Every token is satisfied by the merge, lowest priority first: `defaults.yaml` → the
group's `color_mappings` → the variant's `color_mappings`. Both families live in
that one map; the name disambiguates them. No defaults, filters or whitespace inside
a token. A rendered SVG is never committed here (spine AD-11).

## Surfaces, styles and rows

- `surface` (required per group) is the group's default layer: `wallpaper`,
  `dark-glass` or `solid`. The ink contract is `wallpaper → on_backdrop`,
  `dark-glass`/`solid → the on-surface family`.
- `serves` (optional) lists every surface the group renders on, defaulting to
  `[surface]`. This is what retires the `system-*` rows: one row serves the bar and
  the dark-glass panel, and the surface selects the ink at render time.
- `styles` (optional) declares a style axis (`[default, bold, rounded]`). A row is
  one `state x style` cell; `bar_mappings.states` stays the fixed state → variant
  table, resolving to the default-style row.
- a variant row carries `name`, `state`, `style`, `template`, `output` and its own
  token map. Several rows may name the SAME template: one canonical drawing rendered
  with different `OPACITY_*` params, or a row re-exported from another group (as
  `capture-tool/mic` re-exports the bar microphone art). A variant pin that restates
  the value it already inherits is dead data and fails the gate — pins are reserved
  for genuine tints and params.
- `output` is an explicit bare file-name stem. For a group serving more than one
  surface the runtime derives `<stem>@<surface>.svg`; that artifact-naming rule is a
  runtime concern, not a row here.

## Canonical art (REQ-149 slice 3)

Measured against `icon-architecture.md` §10: 9 collapsible groups / 26 files, and
the corpus is 123 → 106 templates.

| Family | Before | After |
| --- | --- | --- |
| `settings-panel/signal` | 4 files, one `fill-opacity="0.5"` step each | `signal/default/icon.svg` + `OPACITY_BAR_1..4` |
| `settings-panel/wifi-signal-*` | 4 files | `wifi-signal/default/icon.svg` + `OPACITY_ARC_1..4` |
| `settings-panel/bluetooth-signal-*` | 4 files | `bluetooth-signal/default/icon.svg` + `OPACITY_BAR_1..4` |
| `status-bar/network/wifi-{high,medium,low}/{default,rounded}` | 6 files | `network/wifi/{default,rounded}/icon.svg` + `OPACITY_ARC_*` |
| `volume/{medium,max}` | 2 files | `volume/default/icon.svg` + `OPACITY_ARC_1` |
| `ethernet-connected/{bold,rounded}` | byte-identical | one file, both rows point at it |
| `settings-panel/settings` vs `status-bar/settings` | byte-identical | one file, both rows point at it |
| `wallpaper-progress/picture` vs `ui/image` | byte-identical | one file, both rows point at it |

The `bold` network art and the `muted`/`low`/`lowest` volume art differ in geometry
and keep their own files. The state language is unchanged: every level state draws
all strips and dims the outer ones, outside-in. The before/after render comparison
is `tickets/req-149-icon-schema-v2/verify-collapse.py` (itr-rendered, geometry +
effective paint identical for all 142 rows).

## How a `template` path resolves

`variants[].template` is relative to the **group's template root**:

```text
templates_root / (group.template_dir or ".") / variants[].template
```

`template_dir` is optional and defaults to `"."`, so with no `template_dir` the path
is relative to `templates/` itself — e.g. `status-bar/battery/battery-0/default/icon.svg`.
A group is a logical name, not necessarily a directory: `battery`, `network` and
`wifi-*` all live under `status-bar/`.

## Gate

```bash
make validate-icons
```

fails the release, naming the file, when a mapping `template:` does not resolve,
when a token used by a template is declared for neither the group nor the vocabulary,
when a token name is outside the two families or its value breaks the family's value
space (a non-role colour, an opacity outside 0..1), when a mapping value is not a
role declared in `vocabulary.json` (legacy `colorN` carriers and aliases are rejected;
the shrink-only `phase_a_legacy_baseline` is empty since REQ-008 Phase B), when a
declared surface is invalid or a `serves` list omits the default surface, when a row's
surface ink breaks the surface-ink contract, when `styles`/`state`/`bar_mappings.states`
disagree, when a variant pin restates its inherited value, when an SVG is not
well-formed XML, when an `output` is not a bare file name, or when a second group-map
file appears beside `icons.yaml`. It also fails when a group or variant in
`icons.yaml` is missing from `ROLE-MIGRATION.md`. It reports (without failing) an
unused declared token, an unreferenced template, and a `(state, style)` cell the
corpus does not draw.

The contract itself is `schema.json`; the corpus checks it describes are the ones
above, so a change to the shape and a change to the checker land together, and the
checker asserts `schema_major 2` so the two cannot drift.
