---
id: REQ-001
title: "Birth the assets repository: mu harness, five empty classes, schemas, catalog, v0.1.0"
kind: requirement
status: done
size: M
lane: bmad-advisory
links:
  openspec: repo-birth
  bmad: none
worktree: .worktrees/s0/ (release record: .worktrees/s0r/)
branch: ticket/s0-assets-repo-birth
children: []
---

# Birth the assets repository: mu harness, five empty classes, schemas, catalog, v0.1.0

## Requirement

Create `RandomGenericUsername/dotfiles-assets` (public) as the corpus home for the dotfiles assets
split, with the mu-strict harness copied byte-for-byte, a **valid but empty** five-class corpus, the
two contracts consumers will parse (`icons/schema.json`,
`templates/**/*.vars.schema.json`), the mechanical absence check for generated/mutable artifacts,
and an annotated `v0.1.0` that a fresh anonymous clone can validate. Nothing in `dotfiles-v3`
changes: nothing consumes this tag yet, which is what makes the birth cheap to roll back.

Data-only (spine AD-2): no `src/`, no importable package, no console script, no engine. The
validators are standard-library Python under `scripts/`, invoked by the `Makefile` and CI.

## Acceptance

- [x] Harness is `mu`'s, byte for byte: `diff -u` on `scripts/worktree-guard.sh` and
      `skills-lock.json`, `diff -r` on `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/_template/`
      and `tickets/_fixtures/` → exit 0. `AGENTS.md` keeps the evidence/worktree/planning-vs-code
      rules verbatim (extracted-block `diff` → exit 0); `CLAUDE.md` is a symlink.
- [x] `bash scripts/worktree-guard.sh check-clean` → exit 0; `rg -c "Gate .*:" tickets/LIFECYCLE.md`
      ≥ 6; `python3 _bmad/scripts/memlog.py --help` → 0; `openspec validate --specs` → 0.
- [x] Data only: no `src/`, no `[project.scripts]` in `pyproject.toml` (dev-only tooling).
- [x] Five class dirs exist and `python3 scripts/validate-catalog.py` prints 5 classes and 2
      `schema_major` values, exit 0.
- [x] AD-11 is mechanical: `touch icons/mappings/icons.json && make validate` → non-zero naming
      `icons/mappings/icons.json`; after `rm`, `make validate` → exit 0.
- [x] `make gates` → exit 0 on a fresh clone; `make hermetic` → exit 0 with empty `HOME`/`XDG_*` and
      a foreign cwd; `make ci-gates-parity` → exit 0.
- [x] Annotated `v0.1.0` pushed and anonymously fetchable (`git ls-remote --tags … 'v0.1.0*'` → tag
      object `b142d02` + peeled `b28c564`; `--refs` → one line); the first CI run on `master` is green
      ([run 39684361040](https://github.com/RandomGenericUsername/dotfiles-assets/actions/runs/39684361040), 4/4 jobs).
- [x] GitHub Release `v0.1.0` published with notes and no assets (a data repo has nothing to build).

## Evidence

- Slice definition: `_bmad-output/planning-artifacts/architecture/architecture-assets-split-2026-10-21/SLICES.md`
  §S0 (13-item birth checklist, acceptance gate block).
- Spine invariants: AD-2 (data-only), AD-3 (five classes, one tag), AD-6 (manifest is the destination
  map, catalog is inventory), AD-8/AD-12 (template contract + schema versions), AD-11 (no generated
  artifacts), AD-15 (mu-strict birth).
- The full gate block was executed and its results recorded in the slice report; the reusable proof
  is the fresh-clone run (`git clone … && make gates`), which is CI's own entry point.
