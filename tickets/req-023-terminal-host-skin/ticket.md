---
id: req-023
title: "terminal-host skin: opt-in Hyprland-following terminal variant"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-023/
branch: ticket/req-023-terminal-host-skin
---

# terminal-host skin: opt-in Hyprland-following terminal variant

## Why

`terminal` is the dense-monospace, square/hairline skin, and its 0px radius /
1px border are an explicit identity: it declares no `[host]` policy, so its
panel geometry never follows Hyprland. A user who wants the terminal look but
wants the panel to sit on the compositor's rounding/border size has no skin to
select. This slice adds `terminal-host`, an **opt-in** variant that keeps every
terminal paint/type/rhythm token and delegates only the panel radius and border
width through the `contracts v0.9.0` `[host]` policy. The original `terminal`
does not change: it stays `[host]`-free and explicit.

Acceptance criteria: five Appearance v2 manifests and eight GTK templates
expand as 5 × 2 modes × 8 templates; `terminal-host` appears in the frozen
manifest set; a supplied host radius/border width resolves into `tokens.json`;
`terminal` remains byte-unchanged and `[host]`-free.

## Requirement

1. Add `skins/manifests/terminal-host.toml`:
   - `name = "terminal-host"`;
   - the same token groups/templates/values as `terminal` (square/hairline
     fallbacks, monospace type, radii/paddings/type scale);
   - an explicit root policy:
     ```toml
     [host]
     inherit = ["surface.panel.radius", "surface.panel.border-width"]
     fallback = "skin"
     ```
   - a header comment recording that this skin intentionally follows Hyprland
     panel geometry while `terminal` remains explicit.
2. Do **not** modify `terminal.toml`, any template, or any existing skin.
3. Update the validator/tests/schema/README/catalog/CHANGELOG/version:
   - five manifests × eight templates expand (10 manifest×mode documents);
   - `terminal-host` is in `frozen.required_files` and the manifest set;
   - host values resolve into the inherited paths only, with the skin fallback
     when the host supplies nothing;
   - the original `terminal` remains `[host]`-free;
   - negative coverage proves an unknown inherited path and a malformed policy
     still fail.
4. Validation: `make validate-skins`, `make test-skins`, `make lint`,
   `make gates-ci` in the foreground; a GTK3 probe for `terminal-host` proves
   the host radius is applied and the card fill is identical to `terminal`.
5. Release `v0.16.0` as an annotated tag on the green closing commit,
   fast-forward to `master`, push `master` and the tag. No runtime,
   provisioning, composition, app or live-state change.

## Acceptance

- [x] `skins/manifests/terminal-host.toml` exists with the terminal token
      values plus the `[host]` policy documented as opt-in.
- [x] `terminal.toml`, every template and every other skin are byte-unchanged.
- [x] Validator reports 5 manifests, 8 templates, 10 expansions and resolves
      host radius/border width into `tokens.json` for `terminal-host`; a
      no-host manifest is unchanged by the same host values.
- [x] `frozen.required_files` names all five manifests; tests cover the five ×
      eight matrix and the original `terminal` stays `[host]`-free.
- [x] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [x] GTK3 `CssProvider` probe for `terminal-host` applies the host radius and
      computes the same card fill as `terminal`.
- [x] `v0.16.0` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `skins/manifests/terminal.toml` (explicit opt-out comment);
  `skins/manifests/glass.toml` and `paper.toml` (the `[host]` policy shape);
  `skins/contracts/appearance-manifest.schema.json` (allowlist/fallback).
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; GTK3 probe recorded in the outcome.

## Outcome (2026-11-10)

**Worktree:** `.worktrees/req-023/` (base `v0.15.3`)
**Branch:** `ticket/req-023-terminal-host-skin`
**Commits:** `5149a35` (ticket + INDEX plan), `be472d5` (manifest, validator,
tests, docs, CHANGELOG + version), this closing commit (ticket outcome + INDEX
done).
**Tag:** `v0.16.0` (annotated) on this closing commit; fast-forward to
`master`.

### Delivered

| Path | What changed |
| --- | --- |
| `skins/manifests/terminal-host.toml` | **new** fifth manifest: terminal's groups byte-for-byte plus the opt-in `[host]` policy and the documenting header |
| `scripts/validate-skins.py` | `_resolve_manifest(manifest, mode, host=None)` applies `mode override > host > skin fallback`; gate resolves deterministic probe values for every `[host]` manifest, proves only inherited paths move, and proves no-host manifests are unchanged; summary now prints `host=...` |
| `skins/schema.json` | `frozen.required_files` adds `terminal-host`; `status` `populated (v0.16.0)`; notes name terminal-host as the opt-in counterpart |
| `skins/tests/test_skins.py` | 5-manifest matrix, terminal-host fixture/equality, host-resolution/precedence/fallback tests, wlogout terminal-host parameterization, GTK3 host-geometry + card-fill probe |
| `skins/tests/fixtures/positive/terminal-host.toml` | **new** positive fixture, byte-equal to the shipped manifest |
| `skins/README.md`, `README.md`, `templates/README.md`, `catalog.yaml`, `CHANGELOG.md` | five-manifest inventory, host-resolution gate, v0.16.0 release notes |
| `skins/manifests/terminal.toml`, `skins/templates/*`, `templates/wlogout/style.css.tpl`, `configs/**` | **unchanged** from `v0.15.3` |

### Exact manifest diff

```diff
diff --git a/skins/manifests/terminal-host.toml b/skins/manifests/terminal-host.toml
new file mode 100644
--- /dev/null
+++ b/skins/manifests/terminal-host.toml
@@ -0,0 +1,116 @@
+# terminal-host — the opt-in Hyprland-following variant of terminal. ...
+schemaVersion = 2
+name = "terminal-host"
+
+[host]
+inherit = ["surface.panel.radius", "surface.panel.border-width"]
+fallback = "skin"
+
+[groups.surface.panel]
+bg = "@surface"
+border = "alpha(@on_surface, 0.22)"
+border-width = 1
+radius = 0
+padding = 9
+shadow = "none"
+blur = "none"
+# … every other group is byte-identical to terminal.toml
```

`git diff --stat v0.15.3 -- skins/manifests` → only
`terminal-host.toml | 116 +++++++++++++++++` (1 file changed, 116 insertions).
`git diff --exit-code v0.15.3 -- skins/manifests/terminal.toml skins/templates
templates/wlogout configs` → rc `0` (no existing skin, template or config
changed).

### Host precedence and resolution

| Case | Probe (`radius=13`, `border-width=2`) result |
| --- | --- |
| `terminal-host` dark | panel radius `13`, border width `2`; every card/cell/control/pill/state/type/ink/layout token unchanged |
| `terminal-host` light | same (no mode override) |
| `glass` dark/light | radius `13`, border width `2` |
| `paper` dark | radius `13`, border width `2` |
| `paper` light | radius `6`, border width `1` — the authored `mode.light.surface` group wins over host |
| `terminal`, `flat` | unchanged by the same probe values (`terminal` stays `0`/`1`, `flat` `0`/`0`) |
| Host silent, `fallback = "skin"` | skin values (`0`/`1` for terminal-host) |
| Host silent, `fallback = "error"` | `ValueError` (fails closed) |

### Gate and probe evidence

| Claim | Command | Result |
| --- | --- | --- |
| Skins gate | `make validate-skins` | **PASS** — 5 manifests, 8 templates, 8 targets, 10 expansions, 57 tokens, `host=glass,paper,terminal-host` |
| Skins fixtures | `make test-skins PYTEST="<assets>/.venv/bin/python -m pytest"` | **PASS** — `109 passed, 3 skipped`; skips are `gi` absent from the venv (the host GTK3 probe runs with system Python) |
| Lint | `make lint` with the uv-cache shellcheck on `PATH` | **PASS** — compileall + shellcheck clean |
| CI gate set (foreground) | `PATH="<uv-shellcheck-bin>:$PATH" make gates-ci` | **PASS** — rc `0`; every validator, lint, `hermetic: PASS` |
| Existing bytes unchanged | `git diff --exit-code v0.15.3 -- skins/manifests/terminal.toml skins/templates templates/wlogout configs` | rc `0` (empty) |
| GTK3 terminal-host probe | system Python + `Gtk.CssProvider`/style context on the wlogout sheet with host `radius=13`, `border-width=2` | **PASS** — parsed with zero `parsing-error`; `border-radius: 13px` / `border: 2px solid …` present; card fill `rgb(32,40,48)` identical to `terminal` |

### Downstream pins (not part of this slice)

- **Engine assets mirror:** mirror `v0.16.0` in its own commit. The new
  manifest adds one identity; existing skin/template bytes did not change.
- **Composition:** after the assets mirror, bump the assets pin to `v0.16.0`
  and refresh stale assets source refs; its own gate proves the mirror.
- No runtime, provisioning, composition, app or live-state change is in this
  ticket.
