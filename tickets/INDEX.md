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

