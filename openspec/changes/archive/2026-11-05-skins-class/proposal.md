# Proposal

## Why

The GTK surface vocabulary that the ags-bar settings and Bluetooth panels use is currently copied
into one canonical stylesheet (`ags-bar/style.css`) with literal values mixed into selectors. A
skin is not a variant: GTK 4.24 renders a palette/ink mapping, paint and rhythm/density, and it
ignores transitions. Structure (which widget sits where) and brand/variant names must stay in the
app, so the assets corpus needs a frozen token vocabulary with palette-role expressions only.

Evidence: `../ags-bar/style.css` carries the settings/Bluetooth selectors and today's constants
(`.settings-surface`, `.settings-net`, `.settings-rowact`, `.settings-chevron-*`,
`.settings-wifi-settings-*`, `.settings-nav-*`); the GTK probes recorded in the frozen spec v1
proved `backdrop-filter` blur paints and transitions do not. Verify:
`rg -n 'settings-(surface|net|rowact|chevron|wifi-settings|nav)' ../ags-bar/style.css`.

## What Changes

- Add the sixth data-only class `skins/`: `schema.json` (pointer to the canonical `contracts`
  schemas plus the local validation target), `manifests/{glass,flat,paper}.toml`, and
  `templates/ags-bar.gtk.css.j2`.
- Add `scripts/validate-skins.py` and `make validate-skins`: manifest/schema validation,
  placeholder coverage, no-literal-hex, no-transition and no-structure rules.
- Add pytest fixtures under `skins/tests/` proving the validator fails on literal hex, transitions,
  structure/variant tokens and missing/unknown placeholders.
- Update `catalog.yaml`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, the Makefile gate set and the CI
  workflow; release the next minor tag.
- The canonical schema lives in `contracts`; this repository keeps a local validation target and
  never imports another repository at runtime. No vendored copy is claimed until the canonical pair
  exists and a byte-equality test can pin it.

## Capabilities

### New Capabilities

(none — the class belongs to the corpus contract)

### Modified Capabilities

- `assets-catalog`: the fixed class set becomes six, and the skins class contract joins the corpus.

## Impact

- New class directory + validator + fixtures; catalog/docs/gate updates; `v0.7.0`.
- No existing class path, file or schema major changes. The `../ags-bar/style.css` input is
  read-only.
- Out of scope: changing the ags-bar app, adding transition/structure tokens, adding variants to a
  skin, and pinning/bumping any consumer.
