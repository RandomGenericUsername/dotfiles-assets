---
id: req-014
title: "Skins app templates: one extracted GTK template per non-bar app"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-014/
branch: ticket/req-014-skins-app-templates
---

# Skins app templates: one extracted GTK template per non-bar app

## Why

The skin plane is live for the bar only (`skins/templates/ags.gtk.css.j2`).
The contract at `contracts` `v0.6.0` freezes one template per target
`configDir`, named `<configDir>.gtk.css.j2`, rendering `<configDir>.css`; the
other six AGS apps still ship their palette-role `style.css` directly and
therefore cannot consume a skin.

Each app has a real `configDir` in its `app.manifest.json` and a canonical
`style.css` whose classes are the widget vocabulary the app already applies:

| App source | `configDir` | template target |
| --- | --- | --- |
| `ags-clipboard` | `ags-clipboard` | `ags-clipboard.gtk.css.j2` |
| `ags-notifications` | `ags-notifications` | `ags-notifications.gtk.css.j2` |
| `ags-wallpaper-selector` | `ags-wallpaper-selector` | `ags-wallpaper-selector.gtk.css.j2` |
| `ags-capture-tool` | `ags-capture` | `ags-capture.gtk.css.j2` |
| `ags-icme` | `ags-icme` | `ags-icme.gtk.css.j2` |
| `ags-btop-theme-studio` | `ags-btop-studio` | `ags-btop-studio.gtk.css.j2` |

Evidence: `ags-clipboard/app.manifest.json` (`configDir: ags-clipboard`),
`ags-notifications/app.manifest.json`, `ags-wallpaper-selector/app.manifest.json`,
`ags-capture-tool/app.manifest.json` (`configDir: ags-capture`),
`ags-icme/app.manifest.json`, `ags-btop-theme-studio/app.manifest.json`
(`configDir: ags-btop-studio`); `skins/templates/` holds only
`ags.gtk.css.j2`; `scripts/validate-skins.py` already reports template targets.

## Requirement

1. Add one template per non-bar app under `skins/templates/`, extracted from
   that app's canonical `style.css`:
   `ags-clipboard.gtk.css.j2`, `ags-notifications.gtk.css.j2`,
   `ags-wallpaper-selector.gtk.css.j2`, `ags-capture.gtk.css.j2`,
   `ags-icme.gtk.css.j2`, `ags-btop-studio.gtk.css.j2`.
2. Each template keeps the app's real top-level selectors/class vocabulary
   (window names, root classes, cards, rows, controls and their documented
   states) and uses `{{SKIN_*}}` only for genuine global knobs: panel
   background/border/border-width/radius/shadow/blur, card background/radius,
   cell radius/padding, control radius, pill radius, hairlines via
   `hairline-w`, `ink`/`ink-dim`/`accent`, and `title-size`/`text-size`.
   Component-specific paddings, small font sizes, literal spacings and
   per-element state colours stay as literals copied from that app's
   `style.css`, expressed only as `palette.v1` roles/alpha derivatives.
3. Every template has no literal hex colour, no `transition`/`animation`
   declaration (and the capture template drops its keyframes), and no layout
   token placeholder (`SKIN_PANEL_WIDTH`, `SKIN_BT_LIST_SPACING`,
   `SKIN_BAR_ROW_HEIGHT`, `SKIN_CHIP_MIN`).
4. `scripts/validate-skins.py` discovers every `<configDir>.gtk.css.j2`, prints
   all targets, and expands every template through every manifest
   (`glass`/`flat`/`paper`).
5. `skins/tests/` adds per-app checks: expansion succeeds for all three
   manifests, placeholder coverage names only schema tokens, no hex/transition/
   animation, no layout tokens, and the expected top-level selectors exist.
6. README, `skins/README.md`, CHANGELOG, `catalog.yaml`, this ticket and
   `tickets/INDEX.md` record the seven-template set; tag the next minor
   `v0.11.0`; fast-forward merge to `master`, never work on `main`.

## Acceptance

- [x] Six non-bar templates exist with the target names above and each is
      extracted from the matching app's `style.css`.
- [x] Each template keeps the app's real selectors and uses only the genuine
      global tokens; component detail stays literal.
- [x] No template contains a literal hex colour, a transition/animation, or a
      layout-token placeholder.
- [x] `make validate-skins` reports seven templates and all seven targets, and
      expands all seven through all three manifests.
- [x] `skins/tests/` has per-app expansion, placeholder, forbidden-text, layout
      and selector checks.
- [x] `make validate-skins`, `make test-skins PYTHON=$PWD/.venv/bin/python` and
      `make validate` pass; the ticket branch is fast-forward merged to
      `master` and `v0.11.0` is an annotated tag on the merged commit. Existing
      tags are not moved.

## Evidence / Verify

- Evidence: `skins/templates/` has one template (`ags.gtk.css.j2`);
  `scripts/validate-skins.py` already derives targets from filenames and
  expands every manifest through every template; the six app manifests name
  the target `configDir`s above; each app's `style.css` is the canonical
  selector/declaration source.
- Verify: `make validate-skins` → PASS with `templates=7` and all targets;
  `make test-skins PYTHON=$PWD/.venv/bin/python` → PASS;
  `make validate` → PASS; `git cat-file -t v0.11.0` → `tag`;
  `git merge-base --is-ancestor ticket/req-014-skins-app-templates master` →
  exit 0.

## Discrepancy / judgment log

- **Glass is a global skin, not per-app byte parity.** The templates keep each
  app's selectors and component literals, while the genuine global knobs
  (panel/card paint, radii, ink and title/text sizes) expand to the shared
  `glass` values. A few apps use a different source radius or panel alpha;
  those are the intended skin overrides, not extraction misses.
- **No new tokens.** The frozen 24-token vocabulary is enough for every app;
  per-element selection/empty/focus colours stay palette-role literals, as the
  fidelity policy requires.
- **Capture's recording accent is `@error` directly.** The source names it
  through a local custom property (`--rec-accent`); the template drops the
  custom property and uses the palette role so the same colour survives without
  a second source of truth.
- **Content literals become palette roles.** Source content colours that were
  hex (ICME black shading, btop's stage/terminal, the wallpaper LIVE green) are
  expressed with palette roles/alpha derivatives so the no-hex rule holds; they
  remain component-local, not skin tokens.

## Outcome (2026-11-05)

**Worktree:** `.worktrees/req-014/`
**Branch:** `ticket/req-014-skins-app-templates`
**Commits:** `360213e` (ticket + INDEX plan), `7bfccea` (six templates,
validator target reporting, per-app tests, docs/version updates).
**Merge:** fast-forward into `master` (`360213e..7bfccea`); the ticket branch is
not left unmerged.
**Tag:** `v0.11.0` (annotated object `d68c355`, commit `7bfccea`), created on
the merged commit before this close-out commit.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/templates/ags-clipboard.gtk.css.j2` | panel/card/field/control extraction, kind selection roles preserved |
| `skins/templates/ags-notifications.gtk.css.j2` | card/tile/chip/progress-card extraction, shadow token, cell padding |
| `skins/templates/ags-wallpaper-selector.gtk.css.j2` | panel/card/crumb/hoverbar extraction, LIVE/Apply pills, link search/back controls |
| `skins/templates/ags-capture.gtk.css.j2` | bar/overlay/panel/view, field popovers, recording cluster; keyframes omitted, `--rec-accent` replaced by `@error` |
| `skins/templates/ags-icme.gtk.css.j2` | window panel, variant cards, tree/inputs/inspector; inset wells use `surface_container_lowest` |
| `skins/templates/ags-btop-studio.gtk.css.j2` | root panel, header/rails/stage/diff/footer; content stage/terminal hexes use `surface_container_lowest` |
| `scripts/validate-skins.py` | records per-template `target=<configDir> expanded for flat,glass,paper`; summary already reports all targets |
| `skins/tests/test_skins.py` | seven-template stats, per-app expansion for all manifests, placeholder coverage, forbidden text, layout check, top-level selectors |
| `README.md`, `skins/README.md`, `CHANGELOG.md`, `catalog.yaml`, `skins/schema.json`, `tickets/INDEX.md` | seven-template inventory, targets and `v0.11.0` |

### Per-app extraction decisions

| App | Genuine skin knobs | Component literals kept from the source |
| --- | --- | --- |
| clipboard | `.clipboard-panel` panel; `.clipboard-card` card; search/incognito/clear/index control radius; ink/accent/type | per-kind head plates, selected rings/tints, 0.7–0.86rem small type, body/head geometry |
| notifications | `.notif-card` card/shadow; tile/chip/progress `radius-card`/`radius-cell`/hairline; progress bars `radius-pill`; speedtest cell `cell-pad`; ink-dim body; title/text | accent/critical/error plates, chip padding, 9–11.5px labels, bar heights |
| wallpaper selector | panel; crumb/card/hoverbar cards; search/back/quick control radius; LIVE/Apply pill; ink-dim/type | thumbnail radii and margins, selected-card ring, grid dimensions, 10–12px labels |
| capture | bar/panel/view panels; rec cluster/popup/selbadge/popover cards; field/button/segment control radius; handles/radio/switch/dot pill; ink/type | overlay geometry, recording `@error`, field padding, 8.5–14px labels, CTA shadows |
| icme | window panel; variant card; tree/input/button/inspector control radius; cell padding; pill dot; ink-dim/type | pane widths/margins, selection rings/tints, monospace 9.5–12px type, well shading |
| btop studio | root panel; `.anat` card; controls/items/cells control radius; pchip/modchip pill; cell padding; title/text | rail widths, stage/tree geometry, 9–11px monospace type, selection tints, content-stage shading |

Only genuine global knobs are substituted; every app keeps its own selector
vocabulary and its component-specific literals. The four layout tokens, `gap`
and `ink-over` remain manifest metadata and are not emitted by any template;
app-specific unused knobs (for example no panel in the notification stack) are
reported as notes by the gate rather than forced into a rule.

### Deviations

- **Glass paints the shared knobs, not byte-for-byte app parity.** Panel/card
  paint, radii, ink and title/text sizes expand to the shared `glass` values;
  each app's component literals and structure survive. A source 16px panel
  therefore becomes the glass `radius-panel = 12`, and a source `@surface`
  card becomes the glass `bg-card`.
- **Capture's recording pulse is not shipped.** The source `@keyframes` and
  `animation` declaration are omitted because GTK 4.24 ignores them; the dot is
  static `@error`. The local `--rec-accent` custom property is dropped in
  favour of the same palette role directly.
- **Hex content colours become palette roles.** ICME/btop black shading uses
  `alpha(@surface_container_lowest, …)`; btop terminal text/borders use the
  ink role; the wallpaper LIVE green becomes the accent/`@on_primary` pair.
  These are component-local role expressions, not new tokens.
- **No token or `schema_major` change.** The 24-token vocabulary and
  `schema_major: 1` are unchanged; this is an additive MINOR corpus release.

### Evidence — commands and exact results

| Command | Result |
| --- | --- |
| `make validate-skins` | **PASS** — `manifests=3 templates=7 targets=ags,ags-btop-studio,ags-capture,ags-clipboard,ags-icme,ags-notifications,ags-wallpaper-selector tokens=24 roles=51` |
| `make test-skins PYTHON=$PWD/.venv/bin/python` | **PASS** — `69 passed` |
| `make validate` | **PASS** — 6 classes, 27 directories, 403 files scanned, tag `v0.11.0` |
| `PATH=/tmp/opencode/shellcheck/shellcheck-v0.10.0:$PATH make gates` | **exit 0** — all 9 gates incl. shellcheck and hermetic PASS |
| template scan | 0 literal hex, 0 `transition:`, 0 `animation:`, 0 `@keyframes`, 0 layout placeholders across the seven templates |
| `git cat-file -t v0.11.0` | `tag` (object `d68c355`, commit `7bfccea`) |
