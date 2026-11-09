---
id: req-019
title: "Skins wlogout consumer: paint/rhythm target, required-target gate, static import"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-019/
branch: ticket/req-019-wlogout-skin-consumer
---

# Skins wlogout consumer: paint/rhythm target, required-target gate, static import

## Why

wlogout is the first non-AGS CSS consumer of the v2 Appearance plane. Phase 1
palette parity already works: the rendered static stylesheet imports
`state/current/palette/colors.gtk.css`, so a new generation changes the palette
on the next launch.

Phase 2 makes wlogout a normal generated target without adding a runtime
adapter:

```text
skins/templates/wlogout.gtk.css.j2  ->  appearance/wlogout.css
static style.css imports appearance.css LAST
```

The static app-owned structure — wallpaper, icons, layout IDs, transitions and
grid — stays in `templates/wlogout/style.css.tpl`. The generated sheet contains
paint and rhythm only.

Acceptance criteria: `W-2.1`, `W-2.2`, `W-2.6`, `W-2.9`, `W-2.10` in
`dotfiles-v3/docs/108-non-ags-skin-consumers.md`; epic `SKIN-CONSUMERS`.
Runtime/provisioning/composition work is deliberately out of scope here.

## Requirement

1. **Required-target gate first.** `skins/schema.json` gains the frozen
   `required_targets` set (the seven existing AGS targets plus `wlogout`);
   `scripts/validate-skins.py` compares it exactly with the discovered
   `<configDir>.gtk.css.j2` set. A missing `wlogout.gtk.css.j2` must fail
   `make validate-skins`; an unregistered extra template must also fail.
2. **Add `skins/templates/wlogout.gtk.css.j2`** using only v2 token
   placeholders:
   - `window` background from `surface.panel.bg`;
   - `button` base from `surface.control.*` + `ink.ink`;
   - `button:hover` / `button:focus` / `button:active` from the matching
     `state.{hover,focus,selected}.{fill,ink,ring}` triples;
   - `button span` typography from `type.font-family`, `type.font-weight`,
     `type.letter-spacing` and `type.size-title`.
   No literal hex, `transition`, `animation`, structure/variant, layout IDs,
   icons, wallpaper, grid or margins.
3. **Static import last.** Append `@import url("appearance.css");` at the end
   of `templates/wlogout/style.css.tpl` so the generated same-specificity rules
   win the GTK3 cascade. Existing wallpaper/icon/layout/transition rules stay
   static and app-owned.
4. **Missing-target behaviour.** Keep the palette import first so a missing
   generated target leaves wlogout with palette-only styling at launch; the
   GTK3 `CssProvider` still reports a clear missing-import error, so the gap is
   never silent. Document the provisioning order that creates
   `config/wlogout/appearance.css` before launch and test the missing-target
   case.
5. **Tests/docs.** Add `wlogout` to the positive template matrix; negative
   fixtures for literal hex and structure (existing transition fixture stays);
   tests for a missing required target and a missing template. Update
   `skins/README.md`, `README.md`, `templates/README.md`, `catalog.yaml`,
   `CHANGELOG.md`, this ticket and `tickets/INDEX.md`.
6. **Release.** Tag `v0.14.0` (annotated), fast-forward merge to `master`, push
   `master` + the tag, publish the GitHub Release with only the `v0.14.0`
   artifacts. Record the one-time template-hash churn in the release notes.

## Acceptance

- [ ] The gate is red before the template lands and green after: `wlogout` is a
      required target, missing template/target fails, extra target fails.
- [ ] `wlogout.gtk.css.j2` expands for all four manifests × both modes and uses
      only v2 placeholders/roles; no hex/transition/structure/layout/icons/
      wallpaper/grid/margins.
- [ ] `templates/wlogout/style.css.tpl` imports `appearance.css` last; GTK3
      parses the combined rendered sheet and the generated rules win the
      cascade.
- [ ] Missing-target case: GTK3 reports the missing import clearly; Broadway
      wlogout remains launchable with the palette-only fallback.
- [ ] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [ ] `v0.14.0` is an annotated tag on the fast-forward-merged commit; `master`
      and the tag are pushed; the release carries only `v0.14.0` artifacts.

## Evidence / Verify

- Evidence: `W-2.1`/`W-2.2`/`W-2.6`/`W-2.9`/`W-2.10` in
  `dotfiles-v3/docs/108-non-ags-skin-consumers.md`; the static template is
  rendered by `dotfiles-provision/ansible/roles/wlogout_config`; the runtime
  derives `<configDir>.css` targets from the template set
  (`dotfiles-runtime/src/runtime/domain/models.py:173-186`).
- Verify: `make validate-skins`, `make test-skins
  PYTHON=$PWD/.venv/bin/python`, `make lint`, `make gates-ci`; GTK3
  `CssProvider` probes and the Broadway smoke recorded in the outcome.
