---
id: req-149
title: "Icons schema_major 2: typed token families, styles dimension, canonical-art collapse"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: add-icon-workbench (dotfiles-v3, capability icon-schema-v2)
  bmad: none
worktree: .worktrees/REQ-149/
branch: ticket/REQ-149-icon-schema-v2
---

# Icons schema_major 2

Slice 3 of the REQ-149 icon pipeline program (dotfiles-v3
`openspec/changes/add-icon-workbench`, tasks §3). The consumer-side plan and the
measured architecture live in that change (`design.md` §3,
`inputs/icon-architecture.md` §4.1/§5/§9/§10); this ticket is the assets half.

## Why

The corpus can parameterize colour only. Every non-colour parameter (opacity
ladders, surface ink) is baked into duplicate art files or name-convention
manifest rows (`system-*`), and 17 of the 123 templates are byte- or
geometry-duplicates of another template. `schema_major 2` adds a second typed
token family (`OPACITY_*`), a declared `styles` axis, a declared surface
dimension (`serves`) and retires the `system-*` workaround rows.

## Requirement

1. `icons/schema.json` is `schema_major: 2` and states, as the contract:
   - token families `^COLOR_[A-Z0-9_]+$` (declared role or `#rrggbb` literal)
     and `^OPACITY_[A-Z0-9_]+$` (numeric literal `0..1`); any other token name
     is invalid;
   - `styles` is a declared group dimension; a variant row is `state x style`
     with `template`, `output` and its own param/role pins;
   - `surface` stays declared per group; `serves` declares the surfaces a group
     serves (the `system-*` rows' job today); the surface-ink contract is
     `wallpaper -> on_backdrop`, `dark-glass/solid -> on_surface` family;
   - `bar_mappings.states` stays the fixed state -> variant resolution table;
   - `output` stays an explicit bare stem (the `@surface` artifact suffix is a
     runtime concern, not a row in this repo).
2. `scripts/validate-icons.py` implements the same contract: per-family token
   patterns, `0 <= opacity <= 1`, the surface-ink rule for every served surface,
   styles/state consistency, and `schema_major` is asserted together with the
   checker (bumped in the same commit).
3. Canonical-art collapse, measured against `icon-architecture.md` §10
   (11 geometry-identical groups / 30 files; 9 collapsible groups / 26 files
   after the two `media-controls` pairs are reclassified out):
   - 3 panel ladders (`settings-panel/signal`, `wifi-signal`, `bluetooth-signal`)
     -> one canonical template each + `OPACITY_*` params;
   - network ladders in the `default` and `rounded` styles -> one canonical
     template per style + `OPACITY_*` params (the `bold` art differs per level
     and stays);
   - `volume/{medium,max}` -> one canonical template + an `OPACITY_*` param
     (`muted`/`low`/`lowest` differ in geometry and stay);
   - 3 byte-identical duplicates deleted and single-sourced
     (`ethernet-connected/bold == rounded`,
     `settings-panel/settings == status-bar/settings`,
     `wallpaper-progress == ui/image`).
   Corpus floor: 106 templates (123 - 17).
4. Retire the 12 `system-*` rows (battery x5, volume x5, microphone x2), drop
   the redundant `ui.search` `on_surface` pin, and delete the contrast-guard
   comments whose cited file no longer exists.
5. Owner decree: the state language is today's. Signal ladders stay DIMMING
   (collapse to params preserves the dimming; no art redesign), volume/network
   stay same-strip outside-in dimming, no arc-count redesigns, no new shapes.
6. Byte-faithfulness: every collapsed/deleted/re-pointed variant renders with
   the same geometry and the same effective paint before and after. The
   verification harness is committed under this ticket and uses the pinned
   `itr` renderer.
7. `make gates` green; MAJOR tag (`schema_major` bump), consumer pins reported
   (never edited) for `dotfiles/provisioning/assets.yaml` + `program-tuple.yaml`.

## Acceptance

- [x] `icons/schema.json` at `schema_major: 2` with the token families, styles,
      serves and surface-ink contract.
- [x] `validate-icons` enforces the v2 contract and proves it bites (negative
      fixture run recorded in the ticket).
- [x] 123 -> 106 templates; 142 -> 130 manifest rows.
- [x] Collapse audit: every collapsed/deleted/re-pointed variant renders
      geometry-identically with the same effective paint.
- [x] `make gates` PASS; `make hermetic` PASS.
- [x] Annotated tag; consumer pin values reported.

## Evidence

### Collapse audit (measured, not guessed)

Basis: `icon-architecture.md` §10 (11 geometry-identical groups / 30 files, of
which the two `media-controls` pairs are reclassified out — geometry matches,
paint structure differs). Collapsible: 9 groups / 26 files -> 17 files deleted.

| Family | Before | After | Rows re-pointed |
| --- | --- | --- | --- |
| `settings-panel/signal` ladder | `low/medium/good/high/default/icon.svg` (4) | `signal/default/icon.svg` + `OPACITY_BAR_1..4` | `signal-low/medium/good/high` |
| `settings-panel/wifi-signal` ladder | `wifi-signal-{full,good,medium,low}` (4) | `wifi-signal/default/icon.svg` + `OPACITY_ARC_1..4` | 4 |
| `settings-panel/bluetooth-signal` ladder | `bluetooth-signal-{full,good,medium,low}` (4) | `bluetooth-signal/default/icon.svg` + `OPACITY_BAR_1..4` | 4 |
| network `default` style ladder | `wifi-{high,medium,low}/default` (3) | `network/wifi/default/icon.svg` + `OPACITY_ARC_1..3` | 3 |
| network `rounded` style ladder | `wifi-{high,medium,low}/rounded` (3) | `network/wifi/rounded/icon.svg` + `OPACITY_ARC_1..3` | 3 |
| `volume/{medium,max}` | 2 files | `volume/default/icon.svg` + `OPACITY_ARC_1` | 2 |
| ethernet-connected bold ≡ rounded | 2 byte-identical files | `ethernet-connected/bold/icon.svg`, both rows point at it | 2 |
| settings-panel/settings ≡ status-bar/settings | 2 byte-identical files | `status-bar/settings/default/icon.svg`, both rows point at it | 2 |
| wallpaper-progress/picture ≡ ui/image | 2 byte-identical files | `ui/image/default/icon.svg`, both rows point at it | 2 |

Kept as-is because geometry differs per level: network `bold` (3 files), the
`wifi-full` pair (coordinates differ from high/medium/low by ~0.001 units),
`volume/{muted,low,lowest}` (speaker shifts), battery, `repeat-once`, and the
`media-controls` pairs (paint structure differs).

Corpus: 123 -> 106 templates. Manifest: 142 -> 130 rows (12 `system-*` retired:
battery x5, volume x5, microphone x2; `battery`/`volume`/`microphone` gain
`serves: [wallpaper, dark-glass]`). The owner decree holds: every level state
draws all strips, the level dims the outer ones outside-in, no art redesigned.

### Before/after render comparison

```text
$ PYTHONPATH=~/Development/dotfiles/icon-templates-renderer/src \
    python3 tickets/req-149-icon-schema-v2/verify-collapse.py --base master
verify-collapse: base=master compared=142 rows (130 surviving + 12 retired)
verify-collapse: byte-identical duplicate pairs verified: 3/3 (files: 3 pairs)
verify-collapse: byte-difference limited to the identity opacity normalisation (geometry + effective paint identical):
  - network/wifi-high-default ... (18 ladder rows + volume/max)
verify-collapse: PASS -- every compared row is geometry-identical and carries the same effective paint under the same ink
exit 0
```

The harness uses the pinned itr (`icon-templates-renderer` v0.3.2) through its
own `PlaceholderSubstitutionService` + `MappingResolutionService`, with an
injective role scheme (`#sha256(role)[:6]`) so a role swap cannot hide behind
today's palette. The 12 retired rows are rendered with the retired row's ink
forced on the surviving row (surface-direct rendering). The only byte
difference is the value space's identity: a path that was fully lit now carries
`fill-opacity="1"` (and volume's outer arc sits in `<g opacity="1">`) — the
effective paint is identical. That normalisation is unavoidable while a numeric
token is always emitted and the grammar forbids conditionals.

### Negative fixtures (the gate bites)

```text
$ bash tickets/req-149-icon-schema-v2/verify-negative.sh
PASS case 1 (opacity above 1): ... must be a numeric literal in [0, 1]
PASS case 2 (a number as a colour role): ... a colour is not a number
PASS case 3 (a role as an opacity): ... an opacity is not a role
PASS case 4 (wallpaper ink is not on_backdrop): ... must be on_backdrop
PASS case 5 (unknown token family in art): ... malformed placeholder
PASS case 6 (schema and checker disagree): ... this validator implements 2
PASS case 7 (styled row without a style): ... must declare its `style`
PASS case 8 (style not declared by the group): ... not declared in the group's styles
PASS case 9 (redundant variant pin): ... what the row already inherits
PASS case 10 (state table names no variant): ... names no variant in this group
verify-negative: PASS -- 10/10 contract violations fail the gate by name
```

### Gates

```text
$ make gates            # validate + validate-icons + content + templates + configs + desktop + skins + lint + hermetic
validate-icons: root=... schema_major=2 groups=23 variants=130 svgs=106 defaults=4 roles=51 legacy_baseline=0
validate-icons: PASS -- one group map (icons/mappings/icons.yaml), every template resolves, every COLOR_*/OPACITY_* token is declared and typed, every surface a row renders on satisfies the ink contract, styles/state are consistent, the proposal names every group and variant, every SVG parses
hermetic: PASS -- the corpus validates with no HOME, no XDG state and a foreign cwd
exit 0
```

### Release

Rule followed (README, "Two version numbers"): **MAJOR — a contract or path
break: ... or a `schema_major` bump**. The icons `schema_major` goes 1 -> 2, so
the tag is `v1.0.0` (not `v0.23.x`); a published tag is never moved. Annotated
tag `v1.0.0` on the close commit, after `make gates` exit 0.

### Consumer pin values this slice needs (reported, not edited)

`dotfiles/provisioning/assets.yaml`: `assets.tag: v0.22.6` -> `v1.0.0`, and the
four checkout `source` paths `/assets/v0.22.6/...` -> `/assets/v1.0.0/...`
(wallpapers, icons/templates, icons/mappings, skins).
`dotfiles/provisioning/program-tuple.yaml`: `dotfiles-assets: v0.22.6` ->
`v1.0.0`.
