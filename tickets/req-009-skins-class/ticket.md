---
id: req-009
title: "Skins class: frozen v1 manifests, GTK template, local validation target"
kind: requirement
status: in-progress
lane: 2 — openspec-single
links:
  openspec: skins-class
  bmad: none
worktree: .worktrees/req-009/
branch: ticket/req-009-skins-class
---

# Skins class: frozen v1 manifests, GTK template, local validation target

## Requirement

Add a sixth, data-only class `skins/` carrying the frozen skin spec v1: a
palette-role expression vocabulary (no structure/variant tokens), three shipped
manifests (`glass`, `flat`, `paper`), and one GTK stylesheet template that
expands those tokens for the Bluetooth panel and settings surfaces. The
canonical schema lives in the `contracts` repository; this repository keeps the
data-only validation target and fixture-based tests, never a runtime import of
another repository.

The frozen values are: glass is the default/fallback parity skin (today's
ags-bar look), flat is the zero-chrome skin, and paper is the light/palette
axis expressed only through `palette.v1` roles. Transitions are forbidden
because GTK 4.24 ignores them; surface, border and shadow values are
palette-role expressions, never literal hex.

## Acceptance

- [x] `skins/schema.json` states the canonical contract location in
      `contracts` (`schemas/skin-token.schema.json`,
      `schemas/skin-manifest.schema.json`) and is the local validation target;
      no cross-repo import at runtime.
- [x] `skins/manifests/glass.toml`, `flat.toml`, `paper.toml` carry every
      required token and the frozen v1 values.
- [x] `skins/templates/ags-bar.gtk.css.j2` contains only `{{SKIN_*}}`
      placeholders for skin constants, has no literal hex, no transitions and
      no structure/variant vocabulary; glass expansion is pixel-equivalent to
      the recorded ags-bar values.
- [x] `make validate-skins` proves manifest/schema validation, placeholder
      coverage and the no-hex / no-transition / no-structure rules, and the
      pytest fixtures prove each negative case fails.
- [x] `skins/README.md` documents the light-mode dependency for `paper`.
- [x] `catalog.yaml`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, `tickets/INDEX.md`
      and the gate set (Makefile + workflow) agree on the new class.
- [x] `make gates` green on the commit to be tagged; annotated next-minor tag.

## Evidence / Verify

- Evidence: current canonical settings/bluetooth look rules in
  `../ags-bar/style.css` (read-only input); frozen spec values in this ticket;
  palette role list in `icons/mappings/vocabulary.json` (51 roles).
- Verify: `make validate-skins` → PASS; `make test-skins` → PASS;
  `make gates` → exit 0; `git cat-file -t <tag>` → `tag`.

## Discrepancy / judgment log

- The `contracts` repository is reachable at `v0.4.0`, but it does **not** yet
  contain `schemas/skin-token.schema.json` or
  `schemas/skin-manifest.schema.json`. This ticket therefore records a pointer
  only; it does not claim a vendored copy or byte-equality. The local
  `skins/schema.json` is the validation target until the canonical pair lands.
- `style.css` currently paints cards at `alpha(@surface_container_high, 0.18)`
  with a solid `@primary` border, while the frozen spec freezes the glass
  manifest at `0.88` and `alpha(@primary, 0.35)`. The manifest is the frozen
  source of truth; the template expands the frozen token values and the
  discrepancy is recorded instead of silently redefining either side.
- `paper` uses `surface_container_lowest` (panel) and
  `surface_container_low` (card). In `palette.v1` these are the two light-pole
  container roles: the panel is the lightest sheet and the card is one step
  off it, so a light palette reads as paper without inverting the role family.

## Outcome (2026-11-05)

**Worktree:** `.worktrees/req-009/`
**Branch:** `ticket/req-009-skins-class`
**Commits:** `3eb79f2` (ticket + OpenSpec plan), `58e6edb` (class,
manifests, template, validator, tests, inventory/gate updates). The OpenSpec
change is archived at `openspec/changes/archive/2026-11-05-skins-class/`.
**Tag:** `v0.7.0` (annotated; the exact object is recorded in the follow-up
index commit because a tag cannot contain its own hash).

### Delivered

| Path | What it is |
| --- | --- |
| `skins/schema.json` | local validation target + pointer to `contracts`; 51 `palette.v1` roles; `canonical.tag: null`, `vendored: false` |
| `skins/manifests/{glass,flat,paper}.toml` | frozen v1 values, 23 tokens each |
| `skins/templates/ags-bar.gtk.css.j2` | settings/Bluetooth paint, `{{SKIN_*}}` only, no hex/transition/structure |
| `scripts/validate-skins.py` | stdlib gate: schema pointer, manifests, roles, template coverage, negative text rules |
| `skins/tests/test_skins.py` + `fixtures/invalid/` | 21 pytest cases (positive frozen values + every negative rule) |
| `Makefile`, `.github/workflows/gates.yml` | `validate-skins` in `GATES` + a matching CI job; `test-skins` separate |
| `catalog.yaml`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, spec | six-class inventory and v0.7.0 release notes |

### Evidence — commands and exact results

| Command (in `.worktrees/req-009/`) | Result |
| --- | --- |
| `make validate` | **PASS** — 6 classes, 26 directories, 383 files scanned |
| `make validate-icons validate-content validate-templates validate-configs` | **PASS** each (22/136/117 icons, tarball `default.png`, 9 templates/9 schemas, configs token rule) |
| `make validate-skins` | **PASS** — `manifests=3 templates=1 tokens=23 roles=51`; palette roles == `icons/mappings/vocabulary.json` |
| `make test-skins PYTHON=…/.venv/bin/python` | **PASS** — `21 passed` |
| `python3 scripts/validate-desktop.py` | **PASS** — 6 entries, 6 TryExec, 6 contract records, 1 script |
| `PATH=/tmp/opencode/shellcheck/shellcheck-v0.10.0:$PATH make gates` | **exit 0** — includes `validate-skins`, ShellCheck 0.10.0 (1 script clean), hermetic PASS |
| `make ci-gates-parity` | **PASS** — 9 GATES, 10 workflow jobs, declared CI-only `ci-gates-parity` |
| `openspec validate --specs` | **PASS** — `spec/assets-catalog` |

The only environmental note: this host has no system `shellcheck`; the green
`make gates` run above supplies ShellCheck 0.10.0 on `PATH` from
`/tmp/opencode/shellcheck/`. Without that directory the pre-existing
`validate-desktop`/`lint`/`hermetic` shellcheck step fails exactly as it does on
`master`; no corpus validator is involved in that failure.

### Judgment calls

1. **`paper` roles.** `surface_container_lowest` is the lightest container role
   and `surface_container_low` is one step off it in a light palette; that is
   the paper/panel + card pair without a mode token. In a dark palette the same
   roles are dark sheets, so the README states the appearance follows the
   palette mode.
2. **No vendored schema.** The frozen brief says the canonical schemas live in
   `contracts`, but the reachable `contracts` tag (`v0.4.0`) has no
   `schemas/skin-*.schema.json`. The local file is labelled as the validation
   target, not a copy, and the validator fails a `vendored: true` claim until a
   pinned copy plus byte-equality test exists.
3. **Frozen values win the discrepancy.** Today's `style.css` cards use
   `alpha(@surface_container_high, 0.18)` and a solid `@primary` border; the
   frozen glass manifest is `0.88` and `alpha(@primary, 0.35)`. The template
   expands the frozen tokens; the ticket and CHANGELOG record the mismatch
   instead of rewriting the read-only ags-bar source.
4. **State colours are palette roles, not new tokens.** Selected rows keep
   `@primary_container`/`@on_primary_container`; destructive actions keep
   `@tertiary`/`@secondary`. They are `palette.v1` roles, not skin tokens, so
   the frozen token set stays closed while the template remains useful.
5. **Worktree guard alias.** The docs/LIFECYCLE use
   `scripts/worktree-guard.sh --check-clean`, but the script only accepted
   `check-clean`; the implementation accepts both so the documented gate
   command works.
