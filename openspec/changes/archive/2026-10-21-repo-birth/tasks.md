# Tasks

## 1. Repository and harness (mu-strict, item by item)

- [x] 1.1 Create the public repository and the local clone; make the one commit that cannot be born in a worktree (`.gitignore`), then `bash scripts/worktree-guard.sh create s0 assets-repo-birth`. Verify: `git branch --show-current` in `.worktrees/s0` → `ticket/s0-assets-repo-birth`; `bash scripts/worktree-guard.sh check-clean` → exit 0.
- [x] 1.2 Copy the harness byte-for-byte from `/home/inumaki/Development/mu`: `scripts/worktree-guard.sh` (mode 0755), `skills-lock.json`, `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/LIFECYCLE.md`, `tickets/_template/`, `tickets/_fixtures/`. Verify: `diff -u` per file and `diff -r` per directory against `mu` → exit 0, no output.
- [x] 1.3 Write `AGENTS.md`: mu's §1 evidence rule and §3 routing/worktree/planning rules verbatim; §2 charter and §4 gates retargeted for a data repository; `ln -s AGENTS.md CLAUDE.md`. Verify: extracted §1 and §3 blocks `diff` against `mu/AGENTS.md` → exit 0; `test -L CLAUDE.md` → `LINK_OK`; `rg -c "Evidence:|Verify:" AGENTS.md` ≥ 2.

## 2. Class layout and catalog

- [x] 2.1 Create `icons/{templates,mappings}/`, `templates/`, `configs/`, `content/`, `desktop/{applications,scripts}/` with `.gitkeep` where empty. Verify: `ls -d icons templates configs content desktop` → five lines; `find . -name .gitkeep` → six.
- [x] 2.2 Write `catalog.yaml`: five classes, declared subdirs, `schema_major` for the schema-bearing classes only, `contents: empty in v0.1.0`, no destination path. Verify: `python3 scripts/validate-catalog.py` → exit 0, prints 5 classes and 2 `schema_major` values.

## 3. Contracts

- [x] 3.1 Write `icons/schema.json` (`schema_major: 1`): group → `variants[{name,template,output}]` with template paths relative to the templates root, the `{{COLOR_*}}` placeholder vocabulary rules, and an explicit statement that the corpus and `make validate-icons` arrive with the icons slice. Verify: the file parses (`python3 -m json.tool`), `schema_major` is 1, and `make validate` reports it as a schema-bearing class.
- [x] 3.2 Write `templates/README.md` and `templates/example.vars.schema.json` (`schema_major: 1`, `required[]`, `optional[]`, `template`, closed-world `additionalProperties: false`) as the shape S3 fills. Verify: the shape parses, `required`/`optional` are disjoint, and every name has a `properties` entry (checked by `make validate`).

## 4. Validation surface

- [x] 4.1 Write `scripts/validate-catalog.py`: catalog ⇄ class-dir agreement (both directions, including undeclared subdirectories and empty dirs without `.gitkeep`), schema JSON well-formedness + `schema_major` agreement, destination-path scan, and the AD-11 absence check. Stdlib only. Verify: `make validate` → exit 0; `touch icons/mappings/icons.json && make validate` → non-zero naming the path; remove → exit 0.
- [x] 4.2 Write the `Makefile` verbs `help validate lint gates gates-ci ci-gates-parity hermetic`, all anchored on `$(CURDIR)`; `lint` = shellcheck over `desktop/scripts/**` (stated vacuous pass) + `compileall scripts/` with bytecode outside the tree; `hermetic` = the checks re-run under `env -i` with empty `HOME`/`XDG_*` and a foreign cwd. Verify: `make gates` → exit 0 from the repo and from a foreign cwd via `make -C`; `make hermetic` → exit 0 printing the throwaway `HOME`.
- [x] 4.3 Write `.github/workflows/gates.yml` (one job per gate + `ci-gates-parity`) and `scripts/ci-gates-parity.py` (copied from `dotfiles-v3`, retargeted to stdlib parsing per the `cli-output` precedent, both directions, stale-entry checks). Verify: `make ci-gates-parity` → exit 0 printing both sets.

## 5. Product metadata and planning artifacts

- [x] 5.1 `README.md` (public surface, the two version numbers, the gates, how `dotfiles-v3` pins it, release ritual — naming no path inside another repository), `CHANGELOG.md` (`0.1.0 — skeleton`), MIT `LICENSE`, `.gitignore`. Verify: all four exist; `rg -n 'spine|\.local/share' README.md` → no destination path.
- [x] 5.2 `openspec/config.yaml` (from `mu`, context retargeted), `openspec/specs/assets-catalog/spec.md`, and this change (`proposal.md`, `design.md`, `tasks.md`, delta spec). Verify: `openspec validate --specs` → exit 0; `openspec validate repo-birth --strict` → exit 0.
- [x] 5.3 `tickets/req-001-assets-repo-birth/ticket.md` + `tickets/INDEX.md`. Verify: the ticket records worktree/branch and its acceptance boxes match the gates that were run; INDEX links resolve.

## 6. Release

- [x] 6.1 Merge the ticket branch to `master` (planning and code in separate commits), push, and confirm the first CI run is green. Verify: `gh run list --limit 1` → `completed success`.
- [x] 6.2 Annotated tag `v0.1.0`, pushed. Verify: `git cat-file -t v0.1.0` → `tag`; `git ls-remote --tags <repo> 'v0.1.0*'` → two lines (tag object `b142d02` + peeled commit `b28c564`), `--refs` → one.
- [x] 6.3 Fresh anonymous clone + `make gates`. Verify: `git clone <repo> /tmp/opencode/assets-fresh && cd /tmp/opencode/assets-fresh && make gates` → exit 0 (observed: validate PASS, 5 classes / 2 schema_major, lint vacuous shellcheck pass, hermetic PASS).
- [x] 6.4 GitHub Release for `v0.1.0` with notes and no build artifacts (a data repository has nothing to attach). Verify: `gh release view v0.1.0 --json tagName,assets` → `v0.1.0`, `assets: []`.
