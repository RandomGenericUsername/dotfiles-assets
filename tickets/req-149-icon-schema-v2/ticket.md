---
id: req-149
title: "Icons schema_major 2: typed token families, styles dimension, canonical-art collapse"
kind: requirement
status: in-progress
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

- [ ] `icons/schema.json` at `schema_major: 2` with the token families, styles,
      serves and surface-ink contract.
- [ ] `validate-icons` enforces the v2 contract and proves it bites (negative
      fixture run recorded in the ticket).
- [ ] 123 -> 106 templates; 142 -> 130 manifest rows.
- [ ] Collapse audit: every collapsed/deleted/re-pointed variant renders
      geometry-identically with the same effective paint.
- [ ] `make gates` PASS; `make hermetic` PASS.
- [ ] Annotated tag; consumer pin values reported.

## Evidence

Filled in by the close commit: gate commands + exit codes, the collapse audit
table, the harness output, the tag object.
