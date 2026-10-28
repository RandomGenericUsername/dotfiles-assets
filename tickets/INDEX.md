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
- [req-007-ags-clipboard-launch-rename](./req-007-ags-clipboard-launch-rename/ticket.md) — Rename the clipboard launcher/autostart/keybind from hypr-pano to clipboard | `done` | lane 2 — assets config cutover | commits `16a43b8` + `e11b545`; `rg 'hypr-pano' configs desktop` → 0 matches; gates green; tag `v0.6.2` local (object `e94165b`, commit `4fa35c4`; not pushed/published); provision follow-up open (wrapper install, `clipboard-ui`, `ags-clipboard` link)

## Bugs

- [bug-001-wlogout-logout-uwsm-stop](./bug-001-wlogout-logout-uwsm-stop/ticket.md) — wlogout Logout runs `terminate-user` and leaves SDDM on a black VT | `done` | lane 2 — bounded config change | severity: high | fix `uwsm stop` + static guard in `v0.6.1` (f8cc828, tag object b2ad3a9; CI 40403377594 green; release published); VM matrix waived 2026-10-26; deployed via engine `v0.1.16` / v3 `PIN-0115`; host accepted 2 clean cycles (17:26:34→17:26:44, 17:36:33→17:36:54); formal 5-cycle run stopped at 3/5, user accepted — 5/5 not claimed; checker over-counted 3 successes as 5 attempts (failed password 17:36:47)

