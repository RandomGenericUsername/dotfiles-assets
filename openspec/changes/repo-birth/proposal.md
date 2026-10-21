# Proposal

## Why

The dotfiles corpus (icons, Jinja templates, static configs, wallpapers and authored themes, desktop
entries and host scripts) lives inside the composition repo, so every corpus edit is a composition
edit, and the corpus has no version of its own: a consumer cannot ask "which icon set is this
machine running?" and get an answer a machine can be rebuilt from. The split gives the corpus its
own repository, its own annotated tag and its own validation — with **no code in it**, because the
renderer, palette generator and provisioner already exist as separate pinned repos.

Evidence: the corpus inventory measured in the spine (`117 SVGs in 12 groups`, `13 hypr Lua files`,
`8 nvim files`, `6 .desktop entries`, one in-repo script, an 82.6 MB wallpaper tarball) lives under
the composition repo's `dotfiles/` tree today; spine AD-3 records the layout this repository must
hold and AD-15 the 13-item birth checklist. Verify: `git -C dotfiles-v3 ls-files dotfiles | wc -l`
on the pre-split commit; `ls` of this repository after this change.

This change is the **birth** (slice S0): an empty but valid corpus that proves the release ritual —
gates green, annotated tag, CI green, anonymous fresh clone green — before the expensive migration
depends on it.

## What Changes

- Create the repository with the mu-strict harness copied byte-for-byte from `mu`
  (`scripts/worktree-guard.sh`, `skills-lock.json`, `_bmad/`, `.agents/skills/`, `.opencode/`,
  `tickets/LIFECYCLE.md`, `tickets/_template/`, `tickets/_fixtures/`), `AGENTS.md` retargeted only
  in its charter and repo-gates sections, `CLAUDE.md` a symlink to it.
- Add the five class directories (`icons/{templates,mappings}`, `templates/`, `configs/`,
  `content/`, `desktop/{applications,scripts}`) with `.gitkeep`, and `catalog.yaml` describing them
  with `schema_major` for the two schema-bearing classes.
- Add the two contracts: `icons/schema.json` (`schema_major: 1`, group → variants → template path,
  placeholder vocabulary) and `templates/README.md` + `templates/example.vars.schema.json`
  (`schema_major: 1`, `required[]`/`optional[]`).
- Add the validation surface: `scripts/validate-catalog.py` (catalog ⇄ dirs, schema JSON, AD-11
  absence), the `Makefile` verbs (`help validate lint gates gates-ci ci-gates-parity hermetic`,
  anchored on `$(CURDIR)`, `hermetic` with empty `HOME`/`XDG_*` and a foreign cwd), and
  `.github/workflows/gates.yml` with one job per gate plus `ci-gates-parity`.
- Release `v0.1.0` (annotated).

## Capabilities

### New Capabilities

- `assets-catalog`: the five-class layout, the repo-local catalog, the two version numbers, the
  absence of generated/mutable artifacts, the fresh-clone gate set, and the immutable-tag release
  ritual.

### Modified Capabilities

(none — this repository does not exist before this change.)

## Impact

- New repository `RandomGenericUsername/dotfiles-assets` (public), tag `v0.1.0`.
- New files: the harness above, the class layout, `catalog.yaml`, the two schemas, three validators
  (`validate-catalog.py`, `ci-gates-parity.py`, `worktree-guard.sh`), `Makefile`, workflow, README,
  CHANGELOG, LICENSE, `openspec/`, `tickets/`.
- **No change to `dotfiles-v3`**: nothing consumes this tag yet, which is why the birth can be
  rolled back by deleting the tag and the repository.
- Out of scope: the corpus itself (icons + content in `v0.2.0`, configs in `v0.3.0`, templates in
  `v0.4.0`, desktop in `v0.5.0`), the installer's pin and fetch step, and every consumer-side edit.
  The class validators (`validate-icons`, `validate-templates`, `validate-content`,
  `validate-desktop`) land with their corpora — a validator with no corpus is a rule nobody has
  seen work.
