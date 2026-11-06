# Ticket index

> Counting rule: completeness checks cover item files (`tickets/<id>-<slug>/ticket.md`) only.
> `tickets/_template/` (and any `tickets/_fixtures/`) are excluded from INDEX completeness counting.
> Entry format: link — title | `status` | execution links. Epics add `done/total children done`,
> done-when, and one nested line per child. Bugs add severity. Spikes add timebox state.

## Epics

(none yet — the assets split is executed as one requirement per slice, not as an epic with children)

## Requirements

- [req-001-assets-repo-birth](./req-001-assets-repo-birth/ticket.md) — Birth the assets repository: mu harness, five empty classes, schemas, catalog, `v0.1.0` | `done` | openspec: repo-birth (archived 2026-10-21) | tag `v0.1.0`, CI run 39684361040 green
- [req-002-assets-icons-content](./req-002-assets-icons-content/ticket.md) — S1 assets cut: icons + content, one group map, `v0.2.0` | `done` | tag `v0.2.0` (4b47290), CI run 39686428951 green, release published
- [req-003-assets-configs](./req-003-assets-configs/ticket.md) — S2 assets cut: static config corpus, `v0.3.0`/`v0.3.1` | `done` | tag `v0.3.1` (4359b4f), CI run 39693485641 green, releases published
- [req-004-assets-templates](./req-004-assets-templates/ticket.md) — S3 assets cut: 9 Jinja templates + 9 vars schemas + `validate-templates`, `v0.4.0` | `done` | tag `v0.4.0` (9902c91), CI run 39783964966 green, release published
- [req-005-assets-desktop](./req-005-assets-desktop/ticket.md) — S4 assets cut: 6 desktop entries + `toggle-touchpad` + `TryExec` + `requires`/`optional` contract + `validate-desktop`, `v0.5.0` | `done` | tag `v0.5.0` (fc0ce5d, tag object 1fdbc85), CI run 39813199995 green, release published
- [req-006-sddm-wayland-template](./req-006-sddm-wayland-template/ticket.md) — SDDM template carries the explicit Wayland greeter compositor, `v0.6.0` | `done` | lane 2 — openspec-single | openspec: sddm-wayland-template (archived 2026-10-26) | tag `v0.6.0` (60620ac, tag object ff460db), CI run 40349570724 green, release published
- [req-008-icons-role-mappings](./req-008-icons-role-mappings/ticket.md) — Icons manifest: semantic role re-pin, real defaults, surface classes, vocabulary lint | `done` | tag: v0.6.3 | live: no colorN, 58 on_backdrop variants
- [req-007-ags-clipboard-launch-rename](./req-007-ags-clipboard-launch-rename/ticket.md) — Rename the clipboard launcher/autostart/keybind from hypr-pano to clipboard | `done` | lane 2 — assets config cutover | commits `16a43b8` + `e11b545`; `rg 'hypr-pano' configs desktop` → 0 matches; gates green; tag `v0.6.2` local (object `e94165b`, commit `4fa35c4`; not pushed/published); provision follow-up open (wrapper install, `clipboard-ui`, `ags-clipboard` link)
- [req-009-skins-class](./req-009-skins-class/ticket.md) — Skins class: frozen v1 manifests, GTK template, local validation target | `done` | lane 2 — openspec-single | openspec: skins-class (archived 2026-11-05) | worktree `.worktrees/req-009/`, branch `ticket/req-009-skins-class` | tag `v0.7.0` (object `8428b75`, commit `e989c03`)
- [req-010-skins-parity](./req-010-skins-parity/ticket.md) — Skins fidelity: glass expands to today's ags-bar settings/Bluetooth declarations | `done` | lane 2 — bounded correction | worktree `.worktrees/req-010/`, branch `ticket/req-010-skins-parity` | commits `62f5d5f` + `c63108d`, gates green, fast-forward merged to `master`, tag `v0.8.0` (object `20e77e7`, commit `fd0deef`)
- [req-011-skins-value-types](./req-011-skins-value-types/ticket.md) — Skins value types: unitless numeric tokens, vendored canonical schemas, `v0.9.0` | `done` | lane 2 — bounded correction | worktree `.worktrees/req-011/`, branch `ticket/req-011-skins-value-types` | commits `f4a0419` + `5a62c2d`, gates green (`34 passed`), fast-forward merged to `master`, tag `v0.9.0` (object `4e70950`, commit `5a62c2d`)
- [req-012-skins-template-naming](./req-012-skins-template-naming/ticket.md) — Skins template naming: `<configDir>.gtk.css.j2`, `v0.5.2` pin + resolved `skin.json` schema, `v0.9.1` | `done` | lane 2 — bounded correction | worktree `.worktrees/req-012/`, branch `ticket/req-012-skins-template-naming` | commits `50528fb` + `db33e7e`, gates green (`38 passed`), fast-forward merged to `master`, tag `v0.9.1` (object `34fa2e2`, commit `db33e7e`)
- [req-013-skins-hairline-layout](./req-013-skins-hairline-layout/ticket.md) — Skins hairlines + layout ownership: `hairline-w` token, layout tokens TSX-owned (no layout placeholders in CSS), `v0.6.0` contract pin, `v0.10.0` | `done` | lane 2 — bounded correction | worktree `.worktrees/req-013/`, branch `ticket/req-013-skins-hairline-layout` | commits `ca50b40` + `1247ee5`, gates green (`41 passed`), fast-forward merged to `master`, tag `v0.10.0` (object `50fe7c4`, commit `1247ee5`)
- [req-014-skins-app-templates](./req-014-skins-app-templates/ticket.md) — Skins app templates: one extracted GTK template per non-bar app, `v0.11.0` | `done` | lane 2 — bounded implementation | worktree `.worktrees/req-014/`, branch `ticket/req-014-skins-app-templates` | commits `360213e` + `7bfccea`, gates green (`69 passed`), fast-forward merged to `master`, tag `v0.11.0` (object `d68c355`, commit `7bfccea`)
- [req-015-appearance-v2](./req-015-appearance-v2/ticket.md) — Skins v2: Appearance token model, `v0.7.0` contract pin, `v0.12.0` | `in-progress` | lane 2 — bounded implementation | worktree `.worktrees/req-015/`, branch `ticket/req-015-appearance-v2`

## Bugs

- [bug-001-wlogout-logout-uwsm-stop](./bug-001-wlogout-logout-uwsm-stop/ticket.md) — wlogout Logout runs `terminate-user` and leaves SDDM on a black VT | `done` | lane 2 — bounded config change | severity: high | fix `uwsm stop` + static guard in `v0.6.1` (f8cc828, tag object b2ad3a9; CI 40403377594 green; release published); VM matrix waived 2026-10-26; deployed via engine `v0.1.16` / v3 `PIN-0115`; host accepted 2 clean cycles (17:26:34→17:26:44, 17:36:33→17:36:54); formal 5-cycle run stopped at 3/5, user accepted — 5/5 not claimed; checker over-counted 3 successes as 5 attempts (failed password 17:36:47)

