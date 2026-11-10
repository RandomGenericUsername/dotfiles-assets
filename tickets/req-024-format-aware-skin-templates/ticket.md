---
id: req-024
title: "Format-aware skin templates: GTK3, GTK4 and rofi artifacts"
kind: requirement
status: in-progress
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

- [ ] `gtk3.gtk.css.j2`, `gtk4.gtk.css.j2` and `rofi.rasi.j2` exist and every
      skin expands all eleven templates.
- [ ] `skins/contracts/` is byte-identical to `contracts v0.10.0` and the PIN
      names the v0.10.0 release commit.
- [ ] `required_targets` includes `gtk3` and `gtk4`; `required_artifacts`
      requires `rofi`/`rasi`; a missing or unregistered template fails.
- [ ] GTK3/GTK4 parse probes and the rofi dump+stderr probe pass.
- [ ] Generated output has no literal hex/structure/layout; rasi has no
      `alpha()` or underscore role.
- [ ] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass in the foreground.
- [ ] `v0.17.0` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `dotfiles-v3/docs/110-format-aware-skin-consumers.md` §3.1, §3.3,
  §4.1, §4.2, §7.1, §7.3, Phase 3A-2 (F-2.1–F-2.4).
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`, plus the recorded GTK3/GTK4 and rofi probes.

## Outcome

Filled at close.
