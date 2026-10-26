# Tasks

## 1. Red proof

- [ ] 1.1 Extend `scripts/validate-templates.py` with the SDDM `[Wayland]` / `CompositorCommand`
      assertion, leaving the template unchanged. Verify: `make validate-templates` → non-zero
      naming the missing `[Wayland]` section.

## 2. Template and contract

- [ ] 2.1 Add the `[Wayland]` section and default command to
      `templates/display-manager/sddm.conf.j2`. Verify: `grep -n '^\[Wayland\]$\|^CompositorCommand='
      templates/display-manager/sddm.conf.j2` → both lines.
- [ ] 2.2 Add `display_manager_sddm_compositor_command` as an optional string in
      `templates/display-manager/sddm.conf.vars.schema.json`; keep `schema_major: 1` and
      `additionalProperties: false`. Verify: `python3 -m json.tool` parses; `make validate` → 0.
- [ ] 2.3 Render the template with only the required variable and with the override. Verify:
      `uv run --with jinja2 python …` → fallback and override present.

## 3. Inventory and docs

- [ ] 3.1 Update `catalog.yaml` (24 required / 1 optional, tag `v0.6.0`), `README.md`,
      `templates/README.md` and `CHANGELOG.md`. Verify: `rg -n '24 required|1 optional|v0.6.0'`
      names the updated files and `make validate` → 0.

## 4. Gates and release

- [ ] 4.1 Run `make validate`, `make validate-templates`, `make gates`, `make gates-ci`,
      `make hermetic`, `make ci-gates-parity`, `openspec validate sddm-wayland-template` and
      `openspec validate --specs`. Verify: all exit 0.
- [ ] 4.2 Merge to `master` only when green; tag annotated `v0.6.0`; push and publish the GitHub
      Release. Verify: `git cat-file -t v0.6.0` → `tag`; `gh release view v0.6.0` → notes, no assets.
- [ ] 4.3 Fresh anonymous clone at `v0.6.0`. Verify: `git clone --branch v0.6.0 … && make gates` →
      exit 0.
