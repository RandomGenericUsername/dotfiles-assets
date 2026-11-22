---
id: req-042
title: "Clipboard overlay paint-only skin"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-042/
branch: ticket/req-042-clipboard-overlay-skin
---

# Clipboard overlay paint-only skin

## Why

`ags-clipboard` reached app HEAD `4acd3fe` (`ticket/REQ-009-clipboard-card-modes`,
1030 lines of `style.css`). The app now owns layout, type headers, type/filter
dots, per-kind selected/focused rings and pin fills through per-widget providers
at `USER + 1`. The assets skin must be paint-only: role fill/border/radius/state/
type/ink for the app-declared surfaces, and nothing that belongs to content.

The previous req-041 branch was based on `v0.23.0`, the `surface.overlay`
experiment. That experiment is not consumed: the composition pins assets
`v0.22.3`, where AGS layer-shell overlays map to `surface.panel`. This ticket
starts a fresh branch from `v0.22.3` and does not continue req-041.

## Audit / conflict decisions

- **Base:** tag `v0.22.3` (`02f6371`), not `v0.23.0` / req-041.
- **Surface role:** the clipboard overlay is `surface.panel` — never
  `surface.window`, never `surface.overlay`.
- **Content colour:** type headers, type/filter dots, per-kind selected/focused
  rings and pin fills are app-owned content. The template contains no
  `.kind-*`, `.clipboard-type-dot`, `.clipboard-filter-dot`, per-kind
  header/selected/focused/pin rules, and no `.clipboard-card` width clamp.
- **Selected state:** the app provider replaces the base role border; the skin
  supplies only the base role border.
- **Settings:** in-page `.clipboard-settings` over transparent
  `.clipboard-settings-catcher`; no `Gtk.Popover`, popover contents or arrow
  nodes in the template.
- **`[host]`:** panel/card/control/cell radii flow from the skin/manifest, so
  terminal-host follows Hyprland rounding and border size.

## Requirement

1. Rewrite `skins/templates/ags-clipboard.gtk.css.j2` as paint-only role
   surfaces for all five skins:
   - outer surfaces (`.clipboard-full`, `.clipboard-compact`,
     `.clipboard-control-bar`, `.clipboard-pins-panel`, `.clipboard-panel`) use
     `surface.panel`;
   - cards (`card`, `stage-card`, `peek-card`, `pin-card`) and bodies use
     `surface.card`;
   - search/chips/pills/arrows/keycaps use `surface.pill`;
     gear/bar buttons/open chip/view tabs/segments use `surface.control`;
   - settings use `surface.card` + panel shadow/blur, catcher transparent.
2. Keep type/ink from skin tokens where the surface has text; no literal type
   sizes, colours or hex.
3. Remove all content/type and per-kind rules and the card width clamp.
4. Add `ags-clipboard` to `BOUNDARY_TARGETS` only after the template is clean,
   and update the gate comment and README to name it.
5. Extend the skins tests for clipboard selectors, roles, all five skins, and
   the absence of content/popover rules.

## Acceptance

- [x] Template uses `surface.panel`, never `surface.window` or
      `surface.overlay`.
- [x] Template contains no `.kind-*`, type/filter dot, per-kind
      header/selected/focused/pin rule, or `min-width: 260px`.
- [x] No `Gtk.Popover`/popover contents/arrow nodes; settings are in-page.
- [x] Panel/card/control/pill radii resolve for glass/paper/flat/terminal/
      terminal-host, including host-delegated geometry.
- [x] `ags-clipboard` is enforced in `BOUNDARY_TARGETS` with a clean gate.
- [x] `make validate-skins`, `make test-skins`, `make gates-ci`, `make lint`
      PASS.
- [x] No tag, push, full provision, or composition-pin bump.

## Evidence

App audit:
`ags-clipboard/.worktrees/REQ-009/style.css` at HEAD `4acd3fe`; ticket
`ags-clipboard/tickets/REQ-009-clipboard-card-modes/ticket.md`.

Assets policy:
`dotfiles-v3/docs/117-redesign-batch.md` (surface roles, per-item content,
no `Gtk.Popover`, v0.22.3 is the release line) and `skins/README.md`
("Skin boundary", "Overlay app implementation pattern").

Tests added:
`skins/tests/test_skins.py`:
- `test_ags_clipboard_is_paint_only_with_no_content_rules`
- `test_ags_clipboard_uses_panel_not_window_or_overlay`
- `test_ags_clipboard_roles_follow_each_skins_geometry`
- `test_ags_clipboard_settings_are_in_page_not_a_popover`

`skins/tests/test_skin_boundary.py`:
- `test_clipboard_template_has_no_boundary_violation`
- `test_clipboard_template_paints_the_panel_role`
- enforced-target registration updated to include `ags-clipboard`.

Gate runs from this worktree:

```bash
make validate-skins   # PASS; clipboard expanded for all five skins x dark/light
make test-skins       # 209 passed, 3 skipped
make gates-ci         # PASS (all validators + lint + hermetic)
make lint             # compileall ok; shellcheck clean (1 script)
```
