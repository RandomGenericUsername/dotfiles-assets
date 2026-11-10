---
id: req-024
title: "Format-aware skin templates: GTK3, GTK4 and rofi artifacts"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-024/
branch: ticket/req-024-format-aware-skin-templates
---

# Format-aware skin templates: GTK3, GTK4 and rofi artifacts

## Why

Phase 3A-1 landed the additive `appearance.artifacts` family in `contracts
v0.10.0`; Phase 3A-3 landed runtime format rendering. This slice is Phase 3A-2
from `dotfiles-v3/docs/110-format-aware-skin-consumers.md`: the assets corpus
must ship one shared template per format so every skin can project its paint,
geometry and (where honest) type into GTK3, GTK4 and rofi without pretending
CSS is the only format.

## Requirement

1. Add `skins/templates/gtk3.gtk.css.j2` (target `gtk3`, GTK3 dialect: no
   `var()`, no `color-mix()`, conservative selectors, `@define-color`/`alpha()`
   only), `gtk4.gtk.css.j2` (target `gtk4`, GTK4 dialect, conservative
   selectors) and `rofi.rasi.j2` (artifact consumer `rofi`, format `rasi`,
   solid palette roles + geometry only, no `alpha()`, no underscore role names,
   typography deferred).
2. Do not ship btop/kitty templates: btop and kitty stay palette-only; `conf`
   and `theme` remain reserved formats.
3. Re-vendor the canonical appearance/generation schemas from `contracts
   v0.10.0` into `skins/contracts/`, update `skins/contracts/PIN` and set
   `skins/schema.json` `canonical.tag = v0.10.0`.
4. `skins/schema.json` freezes `gtk3` and `gtk4` in `required_targets` and the
   `rofi`/`rasi` artifact in `required_artifacts`; missing or extra templates
   fail closed for both families.
5. Validator/tests prove: five manifests × all templates expand; GTK3/GTK4 CSS
   parse; rofi `-dump-theme` exits 0 **and** stderr has no `Failed to parse
   theme`; generated output has no literal hex, structure tokens or layout
   placeholders; rasi output has no `alpha()` and no underscore role names.
6. Gates: `make validate-skins`, `make test-skins`, `make lint`,
   `make gates-ci` in the foreground; tag `v0.17.0`, push `master` + tag.
7. No runtime, provisioning, composition, app or live-state change.

## Acceptance

- [x] `gtk3.gtk.css.j2`, `gtk4.gtk.css.j2` and `rofi.rasi.j2` exist and every
      skin expands all eleven templates.
- [x] `skins/contracts/` is byte-identical to `contracts v0.10.0` and the PIN
      names the v0.10.0 release commit.
- [x] `required_targets` includes `gtk3` and `gtk4`; `required_artifacts`
      requires `rofi`/`rasi`; a missing or unregistered template fails.
- [x] GTK3/GTK4 parse probes and the rofi dump+stderr probe pass.
- [x] Generated output has no literal hex/structure/layout; rasi has no
      `alpha()` or underscore role.
- [x] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass in the foreground.
- [x] `v0.17.0` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `dotfiles-v3/docs/110-format-aware-skin-consumers.md` §3.1, §3.3,
  §4.1, §4.2, §7.1, §7.3, Phase 3A-2 (F-2.1–F-2.4).
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`, plus the recorded GTK3/GTK4 and rofi probes.

## Outcome (2026-11-10)

**Worktree:** `.worktrees/req-024/` (base `v0.16.0`)
**Branch:** `ticket/req-024-format-aware-skin-templates`
**Commits:** `0aea991` (ticket + INDEX plan), `72c3154` (templates, contracts
v0.10.0 re-vendor, validator/tests/docs/version), this closing commit (ticket
outcome + INDEX done).
**Tag:** `v0.17.0` (annotated) on this closing commit; fast-forward to
`master`, push `master` + tag.

### Delivered templates and contract expectations

| File | Family / format | Output | Contract expectation |
| --- | --- | --- | --- |
| `skins/templates/gtk3.gtk.css.j2` | target / `css` | `gtk3.css` | Required target `gtk3` for every skin. GTK3 dialect: `@define-color` + alpha compositing only, no custom properties/colour-mixing, conservative selector allowlist, no layout/size/structure/transition declarations. |
| `skins/templates/gtk4.gtk.css.j2` | target / `css` | `gtk4.css` | Required target `gtk4` for every skin. GTK4/libadwaita named colours (`window_*`, `view_*`, `headerbar_*`, `popover_*`, `card_*`, `accent_*`), same conservative selector/layout ban. |
| `skins/templates/rofi.rasi.j2` | artifact / `rasi` | `rofi.rasi` | Required artifact `{consumer: rofi, format: rasi}`. Solid hyphenated palette roles + px geometry only; no alpha compositing, no underscore role names, no literal hex, no typography (Pango units deferred). |

No btop (`theme`) or kitty (`conf`) template ships; both remain palette-only and
those formats stay reserved.

### Changed surfaces

| Path | What changed |
| --- | --- |
| `skins/contracts/` + `PIN` | Byte re-vendor from `contracts v0.10.0`, source commit `8af8aca54e7107617c4d31655a6eed2665f9b751`; only `generation-manifest.schema.json` changed bytes (adds optional `appearance.artifacts`), the three appearance schemas and frozen v1 schemas are byte-identical to v0.9.0. |
| `skins/schema.json` | `canonical.tag = v0.10.0`; `status = populated (v0.17.0)`; `required_targets` adds `gtk3`/`gtk4`; new `required_artifacts = [{consumer: rofi, format: rasi}]`; notes document the two families and format laws. |
| `scripts/validate-skins.py` | Suffix discovery maps to `(family, format, output)` and fails closed on unknown `*.j2`; exact required target/artifact sets; per-format value rendering (rasi solid/hyphenated); rendered-byte scans for hex/structure/transition/layout; GTK3 dialect ban; GTK3/GTK4 selector + layout-property allowlists; rasi no-alpha/no-underscore. |
| `skins/tests/test_skins.py` + fixtures | 11-template matrix, five-skin × two-mode expansion, GTK3/GTK4 `Gtk.CssProvider` parse probes, rofi `-dump-theme` + stderr probe, and negative fixtures for GTK3 `var()`/`color-mix()`, GTK4 selector/layout, rasi alpha/underscore/hex. |
| `README.md`, `skins/README.md`, `catalog.yaml`, `templates/README.md`, `CHANGELOG.md`, `Makefile` | v0.17.0 inventory, two-family template table, v0.10.0 pin and format-specific gate documentation. |

### Gate evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 5 manifests, 11 templates, 10 targets (`ags…wlogout,gtk3,gtk4`), `artifacts=rofi:rasi`, 57 tokens, 10 expansions |
| Skins fixtures | `make test-skins` via `.venv` | **PASS** — `134 passed, 3 skipped`; the 3 skips are the pre-existing in-process GTK3 style probes that need `gi` in the pytest venv. The new GTK3/GTK4 parse probes run in a child interpreter with `gi` and pass. |
| Targeted format probes | `pytest test_gtk_format_template_parses_every_skin test_rofi_dump_theme_has_no_parse_warning test_rofi_negative_fixture_warns_while_exiting_zero` | **PASS** — `5 passed` (GTK3 + GTK4 × 10 skins/modes; 10 rasi dumps with clean stderr; 2 negatives warning at exit 0) |
| Lint | `PATH="<uv-shellcheck-bin>:$PATH" make lint` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — rc `0`; all validators, lint and `hermetic: PASS` |
| Contract PIN parity | `sha256sum skins/contracts/*.schema.json` + `PIN` | All seven hashes match; `contracts=v0.10.0`, source commit recorded. |

### Downstream pins needed (not part of this slice)

- **runtime:** already consumes `contracts v0.10.0` and format-aware templates
  (`dotfiles-runtime v1.3.0`); no new runtime change here.
- **contracts:** `v0.10.0` is the required contract pin; the assets PIN is
  updated in this tag.
- **provisioning:** add links for `config/gtk-3.0/appearance.css` →
  `current/appearance/gtk3.css`, `config/gtk-4.0/appearance.css` →
  `current/appearance/gtk4.css`, `config/rofi/appearance.rasi` →
  `current/appearance/rofi.rasi`; static `gtk.css` imports
  `appearance.css` last and rofi `config.rasi` imports `appearance.rasi` last.
- **composition:** after the assets mirror, bump the assets pin to `v0.17.0`
  and refresh stale assets source refs in its own commit.
- No live state, other repo, runtime, provisioning or composition edit is in
  this ticket.
