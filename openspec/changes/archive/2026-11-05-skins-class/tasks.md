# Tasks

## 1. Contract and inventory

- [x] 1.1 Add `skins/schema.json` (pointer + local validation target) and the three manifests.
      Verify: `make validate-skins` → PASS.
- [x] 1.2 Add `skins/README.md`, update `catalog.yaml`, `README.md`, `AGENTS.md` and the class
      count in `scripts/validate-catalog.py`. Verify: `make validate` → PASS, 6 classes.

## 2. Template

- [x] 2.1 Extract the Bluetooth/settings look rules into
      `skins/templates/ags-bar.gtk.css.j2`, replacing every visual constant with `{{SKIN_*}}`.
      Verify: `make validate-skins` → placeholder coverage PASS.
- [x] 2.2 Record the overflow-HIDDEN requirement as a template comment and prove the glass
      expansion carries the frozen values. Verify: `make test-skins` → PASS.

## 3. Gate and negative fixtures

- [x] 3.1 Add `scripts/validate-skins.py`, `make validate-skins` and the pytest fixtures.
      Verify: `make validate-skins` → PASS; `make test-skins` → PASS.
- [x] 3.2 Add the CI job and keep `make ci-gates-parity` green. Verify:
      `make ci-gates-parity` → PASS.

## 4. Release

- [x] 4.1 `CHANGELOG.md` records `v0.7.0`; annotated tag after the corpus gates pass.
      `make gates` → exit 0 with ShellCheck 0.10.0 supplied on `PATH` from
      `/tmp/opencode/shellcheck/` (this host has no system shellcheck);
      `make test-skins` → 21 passed; `git cat-file -t v0.7.0` → `tag`.
