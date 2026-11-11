---
id: req-027
title: "surface.window role and the paint-free kitty conf projection"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-027/
branch: ticket/req-027-window-role-kitty-projection
---

# surface.window role and the paint-free kitty conf projection

## Why

`contracts v0.12.0` makes `surface.window` a required outer/toplevel role: eight
tokens, a unitless `[0,1]` opacity and two additional host geometry paths. The
assets class must re-vendor that contract, author the window group in every
skin (plus paper's light branch), remap the outer consumer slots, and add the
paint-free kitty `conf` artifact. `surface.panel` keeps the AGS bar/overlay
consumers and is never an alias for window.

## Requirement

1. Re-vendor the seven canonical schemas from `contracts v0.12.0` into
   `skins/contracts/`, update every `sha256` in `skins/contracts/PIN` and move
   `skins/schema.json` `canonical.tag` to `v0.12.0`.
2. Add a required `surface.window` group with exactly eight tokens (`bg`,
   `border`, `border-width`, `radius`, `padding`, `shadow`, `blur`, `opacity`)
   to all five manifests and paper's complete `mode.light.surface.window`:
   - `glass`: panel-like paint/frame/radius/padding/shadow/blur, opacity `0.94`;
   - `paper`: panel-like, opacity `1.0`; the light window group carries the
     light panel values;
   - `terminal` and `terminal-host`: panel-like opaque, opacity `1.0`;
   - `flat`: transparent/no chrome, opacity `1.0`.
   Keep `surface.panel` required for the AGS bar/overlays; no alias or
   fallback. Add `surface.window.radius` and `surface.window.border-width` to
   the `[host].inherit` policy of `glass`, `paper` and `terminal-host`
   (seven-path allowlist); `terminal`/`flat` stay `[host]`-free.
3. Remap the outer consumer templates:
   - rofi `window` → `surface.window.*`;
   - wlogout outer `window` → `surface.window.*`; action cards keep the agreed
     card fill/border/padding and panel radius/border-width;
   - GTK3/GTK4 `window` and `headerbar` slots → `surface.window.*`;
     `popover`/`.card`/`button`/`entry` keep card/control.
4. Add `skins/templates/kitty.conf.j2` (consumer `kitty`, format `conf`,
   runtime artifact `appearance/kitty.conf`):
   - `font_family` from the first usable `type.font-family` (drop CSS-wide and
     non-portable system keywords, strip quotes/escapes, fall back to
     `monospace`);
   - `font_size` from `type.size-body` and `window_padding_width` from
     `surface.window.padding` via the documented 0.75 px→pt conversion,
     two-decimal round-half-up and clamps (`font_size` 6–36,
     `window_padding_width` 0–32);
   - `background_opacity` from `surface.window.opacity` as a bare decimal;
   - no literal hex/colour and no paint placeholder; palette colours stay
     `colors.kitty`. No btop projection and no `theme` artifact.
   - Register `{consumer: kitty, format: conf}` in
     `frozen.required_artifacts`.
5. Update the validator, fixtures/tests, `skins/README.md`, `README.md`,
   `catalog.yaml`, `Makefile` help, `CHANGELOG.md` and release metadata.
   Five manifests × all templates must expand; required window/card slots are
   tested; the kitty artifact is parsed with `kitty +runpy` (unknown keys warn
   and the gate reports an explicit skip when kitty is absent); rofi still uses
   `-dump-theme`; GTK providers still parse the sheets. No fake CSS.
6. Gates in the foreground: `make validate-skins`, `make test-skins`,
   `make lint`, `make gates-ci`. Tag and push annotated `v0.19.0`.

## Acceptance

- [ ] `skins/contracts/` is a byte copy of `contracts v0.12.0`; PIN hashes,
      source commit and canonical tag agree.
- [ ] Every manifest has the eight-token `surface.window`; paper's light
      branch has a complete window group; `surface.panel` is unchanged and no
      alias exists.
- [ ] `glass`/`paper`/`terminal-host` inherit the two window geometry paths;
      `terminal`/`flat` remain `[host]`-free.
- [ ] rofi/wlogout/GTK outer slots use `surface.window`; cards/controls and
      wlogout action cards keep their agreed roles.
- [ ] `kitty.conf.j2` is a paint-free `conf` artifact with the first-usable
      family, 0.75 px→pt conversion with clamps and direct opacity; no btop.
- [ ] The kitty artifact parses cleanly with `kitty +runpy`; rofi and GTK
      probes stay green; five manifests × all templates expand.
- [ ] `make validate-skins`, `make test-skins`, `make lint` and
      `make gates-ci` pass in the foreground.
- [ ] Annotated `v0.19.0` is tagged on the fast-forwarded `master` commit and
      pushed with `master`.

## Evidence / Verify

- Evidence: `contracts v0.12.0` (`a03b563`) `schemas/appearance-manifest.schema.json`
  `surfaceGroup.required` includes `window`, `windowRole.required` is the
  eight tokens, `hostPolicy.inherit.items.enum` is the seven paths;
  `contracts@v0.12.0:tickets/REQ-020-window-role/ticket.md` names
  `dotfiles-assets v0.19.0` for the skin groups, template remaps and kitty
  template. Kitty unit and family rules:
  `dotfiles-v3/docs/113-window-role-kitty-projection.md` §7.3/§7.4 (CSS
  reference pixel, 0.75 px→pt, two-decimal round-half-up, clamps, first usable
  family).
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; `git diff v0.18.1 -- skins/contracts` shows the canonical
  `v0.12.0` bytes only.

## Non-goals

- No runtime resolver/renderer, provisioning, composition, AGS/app, live-state
  or colour-scheme change.
- No btop `theme` artifact and no kitty colour projection: `colors.kitty`
  stays the palette's artifact.
- No window padding/opacity host delegation, no panel deprecation and no
  `surface.panel` alias for window.
