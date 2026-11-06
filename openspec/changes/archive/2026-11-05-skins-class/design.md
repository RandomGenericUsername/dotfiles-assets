# Design

## Context

This repository is data-only. The skin class must be parseable by a consumer without giving this
repository an engine, and the canonical JSON Schema documents belong to the separate `contracts`
repository. The GTK stylesheet is a render input; the app owns its selectors and widget tree.

## Goals / Non-Goals

**Goals:**

- Freeze one token vocabulary: shape, rhythm, surface, ink, type, layout — no structure/variant
  tokens.
- Keep surface/border/shadow values palette-role expressions (`transparent`, `@role`,
  `alpha(@role,n)`, `color-mix(...)`); no literal hex.
- Ship three manifests and a template whose placeholders have 1:1 coverage with the manifests.
- Prove the rules negatively, so the gate cannot pass vacuously.

**Non-Goals:**

- Shipping a renderer, a GTK build or a consumer destination.
- Adding variants (`glass-dark`, `glass-light`), layout structure, transitions or animations.
- Vendoring a schema copy while the canonical `contracts` paths are absent.

## Decisions

### D1 — TOML manifests, string CSS values

Manifests are TOML with `schema_major`, `name`, and the six token groups. Dimension tokens are
CSS-ready strings (`"16px"`, `"9px 12px"`) so the template is a substitution, not a unit-guessing
renderer. Validation patterns live in `skins/schema.json`.

**Alternative rejected:** numeric tokens plus a unit convention in the renderer. That moves policy
into the consumer and makes the template unable to check its own expansion.

### D2 — Local validation target, pointer to canonical schemas

`skins/schema.json` names `contracts/schemas/skin-token.schema.json` and
`contracts/schemas/skin-manifest.schema.json` and declares `canonical_tag: null` /
`vendored: false` because the reachable `contracts` tag (`v0.4.0`) has no such files. The local
document is the validation target; a future canonical copy must be vendored with a pinned tag and
a byte-equality test. This follows the icons precedent: a local contract file that a gate reads,
never a cross-repo runtime import.

### D3 — Role membership is checked against `palette.v1`

The validator reads the 51-role list from `skins/schema.json` and the test proves that list equals
`icons/mappings/vocabulary.json` roles (50 Material + `on_backdrop`). No invented roles, no aliases.

### D4 — The template owns selectors, not values

`skins/templates/ags-bar.gtk.css.j2` keeps the app-local settings/Bluetooth class vocabulary and
replaces every visual constant with `{{SKIN_*}}`. State selectors may reference palette roles that
have no token (for example a selected row's `@primary_container`): those are palette vocabulary,
not skin constants, and the no-hex rule still applies. Radius-clipped surfaces carry a template
comment requiring the app to set overflow HIDDEN; CSS cannot express it.

### D5 — Glass is the default/fallback parity manifest

`glass.toml` is the manifest a consumer falls back to when no skin is selected. Its values are the
frozen v1 glass values; where `ags-bar/style.css` and the frozen spec disagree (card alpha, border
alpha), the frozen spec wins and the discrepancy is recorded in the ticket.

## Risks / Trade-offs

- **Canonical drift:** `contracts` may add the schemas later. The pointer fields make the missing
  vendoring explicit, and a byte-equality test is required when a copy is added.
- **Token coverage:** a new selector state may need a role that is not a manifest token. The design
  keeps such states in the template's palette vocabulary instead of growing the frozen token set.
- **Negative fixtures:** tests mutate copies under `tmp_path`; they never touch the corpus.

## Verification plan

| Decision | Command | Expected |
| --- | --- | --- |
| D1/D2 | `make validate-skins` | PASS, 3 manifests, 1 template, all tokens |
| D3 | `make test-skins` | role list == icons vocabulary (51), PASS |
| D4 | `make validate-skins` | no `#`, no `transition`, no structure keys |
| D5 | `make test-skins` | glass expansion contains the frozen values |
| Gates | `make gates` / `make ci-gates-parity` | exit 0 |
