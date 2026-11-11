---
id: req-027
title: "surface.window role and the paint-free kitty conf projection"
kind: requirement
status: done
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

- [x] `skins/contracts/` is a byte copy of `contracts v0.12.0`; PIN hashes,
      source commit and canonical tag agree.
- [x] Every manifest has the eight-token `surface.window`; paper's light
      branch has a complete window group; `surface.panel` is unchanged and no
      alias exists.
- [x] `glass`/`paper`/`terminal-host` inherit the two window geometry paths;
      `terminal`/`flat` remain `[host]`-free.
- [x] rofi/wlogout/GTK outer slots use `surface.window`; cards/controls and
      wlogout action cards keep their agreed roles.
- [x] `kitty.conf.j2` is a paint-free `conf` artifact with the first-usable
      family, 0.75 px→pt conversion with clamps and direct opacity; no btop.
- [x] The kitty artifact parses cleanly with `kitty +runpy`; rofi and GTK
      probes stay green; five manifests × all templates expand.
- [x] `make validate-skins`, `make test-skins`, `make lint` and
      `make gates-ci` pass in the foreground.
- [x] Annotated `v0.19.0` is tagged on the fast-forwarded `master` commit and
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
- Vendored bytes: `git -C ../../../contracts show v0.12.0:schemas/<file> | cmp - skins/contracts/<file>` → all seven identical.
- Window/policy: `skins/manifests/*.toml` carry `[groups.surface.window]`;
  `glass` `12/1.5/11/0.94`, `flat` `0/0/11/1.0`, `paper` `6/1/11/1.0` in both
  modes, `terminal`/`terminal-host` `0/1/9/1.0`; `[host].inherit` of
  `glass`/`paper`/`terminal-host` is the seven-path allowlist.
- Artifact: `skins/templates/kitty.conf.j2` → consumer `kitty`, format `conf`,
  runtime `appearance/kitty.conf`; `font_family`, `font_size`,
  `window_padding_width`, `background_opacity` only.

## Non-goals

- No runtime resolver/renderer, provisioning, composition, AGS/app, live-state
  or colour-scheme change.
- No btop `theme` artifact and no kitty colour projection: `colors.kitty`
  stays the palette's artifact.
- No window padding/opacity host delegation, no panel deprecation and no
  `surface.panel` alias for window.

## Outcome (2026-11-11)

**Worktree:** `.worktrees/req-027/` (base `v0.18.1`)
**Branch:** `ticket/req-027-window-role-kitty-projection`
**Commits:** `6183012` (ticket + INDEX plan), `15288a6` (contracts v0.12.0
re-vendor, required window groups, outer remaps, kitty conf artifact,
validator/tests), `5a14cc2` (release docs/version), this closing commit
(ticket outcome + INDEX done).
**Tag:** `v0.19.0` (annotated) on this closing commit; fast-forward to
`master`, push `master` + tag.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/contracts/` + `PIN` | Byte re-vendor from `contracts v0.12.0`, source commit `a03b5632828df8012c02a6117c3be438eca4264b`; PIN hashes and comment updated. `appearance-manifest`, `appearance-json` and `generation-manifest` changed bytes; `appearance-artifact` and the frozen v1 schemas are byte-identical. |
| `skins/manifests/*.toml` | Required eight-token `surface.window` in all five skins; paper has a complete `mode.light.surface.window`. Seven-path `[host].inherit` on glass/paper/terminal-host; terminal/flat stay `[host]`-free. |
| `skins/templates/{rofi.rasi,wlogout.gtk.css,gtk3.gtk.css,gtk4.gtk.css}.j2` | rofi/wlogout outer `window` → `surface.window.*`; GTK `window`/`headerbar` → `surface.window.*`; wlogout action cards keep card fill/border/padding + panel radius/border-width; GTK cards/controls unchanged. |
| `skins/templates/kitty.conf.j2` | Paint-free `conf` artifact: first usable `font_family`, `font_size`/`window_padding_width` in bare points via 0.75 px→pt with two-decimal round-half-up and clamps, direct `background_opacity`. |
| `scripts/validate-skins.py` | v0.12.0 pin, required window role, seven-path host probe (`window 17/3`, `panel 13/2`, `card 14`, `control 15`, `cell 16`), conf bare-point/opacity/family rules, paint fail-closed, required kitty artifact. |
| `skins/schema.json` | `canonical.tag = v0.12.0`, `required_artifacts` adds `{consumer: kitty, format: conf}`, six surface roles / 65 token paths, `status = populated (v0.19.0)`. |
| `skins/tests/` | Required-window and opacity tests, outer-remap tests, kitty family/point/clamp tests, `kitty +runpy` parse and unknown-key warning, positive/invalid fixture migration, missing-kitty artifact gate. |
| `skins/README.md`, `README.md`, `catalog.yaml`, `Makefile`, `CHANGELOG.md` | v0.12.0/v0.19.0 metadata, window semantics, seven-path allowlist, kitty projection and required artifact. |

### Exact window values

| Token | glass | flat | paper (dark) | paper light | terminal | terminal-host |
| --- | --- | --- | --- | --- | --- | --- |
| `bg` | `alpha(@surface, 0.94)` | `transparent` | `@surface_container_lowest` | `@surface_container_lowest` | `@surface` | `@surface` |
| `border` | `@primary` | `transparent` | `alpha(@on_surface, 0.22)` | `alpha(@on_surface, 0.16)` | `alpha(@on_surface, 0.22)` | `alpha(@on_surface, 0.22)` |
| `border-width` | 1.5 | 0 | 1 | 1 | 1 | 1 |
| `radius` | 12 | 0 | 6 | 6 | 0 | 0 |
| `padding` | 11 | 11 | 11 | 11 | 9 | 9 |
| `shadow` | `none` | `none` | `0 10px 28px rgba(0,0,0,0.22)` | `0 8px 22px alpha(@shadow, 0.16)` | `none` | `none` |
| `blur` | `none` | `none` | `none` | `none` | `none` | `none` |
| `opacity` | 0.94 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### Gate evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 5 manifests, 12 templates, 10 targets, `artifacts=kitty:conf,rofi:rasi`, 65 tokens, 10 expansions, host probe on `glass,paper,terminal-host` |
| Skins fixtures | `make test-skins PYTEST="../../.venv/bin/python -m pytest"` | **PASS** — `180 passed, 3 skipped` (the 3 skips are the pre-existing GTK probes that need `gi`; the kitty `+runpy` probe ran) |
| Lint | `PATH="<uv-shellcheck-bin>:$PATH" make lint` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — rc `0`; every validator, lint and `hermetic: PASS` |
| Vendored bytes | `git -C ../../../contracts show v0.12.0:schemas/<file> \| cmp - skins/contracts/<file>` | all seven files identical |

### Downstream pins

- **contracts `v0.12.0`** — required canonical contract pin.
- **assets `v0.19.0`** — this release.
- **dotfiles-runtime `v1.5.0`** — accept/emit the required window group and
  opacity, resolve the window host paths, render `conf` lengths as bare points.
- **ags-platform `v1.1.0`** — parse the unchanged `schemaVersion: 2` document
  with the required window role and opacity kind.
- **dotfiles-provision `v0.1.63` / composition `v0.1.68`** — later slices after
  assets and runtime.

No runtime, provisioning, composition, app or live-state change is in this
ticket.
