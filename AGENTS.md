# AGENTS.md — dotfiles-assets operating contract

Canonical agent instructions for this repo — the dotfiles corpus, as data. Claude (`CLAUDE.md` symlinks here), OpenCode, and all BMAD/OpenSpec skills must follow this. The evidence rule (§1), the routing/worktree rules (§3) and every rule inside them are copied **word for word** from `mu/AGENTS.md`; the only deviations are §2 (this repo's charter, which is mu's §2 retargeted) and §4 (this repo's gates). Proof: `diff` of the §1 and §3 blocks against `mu/AGENTS.md` exits 0.

## 1. Evidence rule (hard requirement)

No suggestion "in the air". Every technical claim, recommendation, or design decision must carry testable evidence — at least one of:

- **Doc evidence:** file path + line range, or commit SHA, or URL + quoted section. Example: `ArmDevelopmentEnvironment@last-branch: setup/create_project/create_project.py:120-180`.
- **Prototype evidence:** a script/command in-repo that runs and prints the validating output. State the exact command and observed result.
- **Test evidence:** `command run → result` (exit code + key output). Failing-as-expected counts if it validates the claim.

Format: any non-trivial claim gets an `Evidence:` line and a `Verify:` line (how to reproduce in one command). If evidence doesn't exist yet, say `Evidence: MISSING — run <X> to produce it` and do not present the claim as fact.

## 2. How we work here

- This repository **is** the corpus: five class directories (`icons/`, `templates/`, `configs/`, `content/`, `desktop/`) behind **one** annotated semver tag. Classes are directories, never independent version boundaries — five tags for one corpus would be five pins to bump and five answers to "which tag is the icons at?".
- **Data only.** No importable package, no console script, no `src/`, no engine. The icon renderer, the palette generator and the provisioner are separate pinned repos; a renderer growing here would re-open the split that created this repo. Python exists only under `scripts/` as CI-executed validators.
- **Validation is the product surface.** `make validate` proves catalog ⇄ class-dir agreement, schema JSON well-formedness, and that no generated or mutable artifact is committed; `make lint` proves the shell/Python under the tree compiles; `make gates` runs both plus `hermetic`; `make hermetic` re-runs the set with empty `HOME`/`XDG_*` and a foreign cwd, so a host-provisioned corpus cannot make a release look green. Every verb is anchored on `$(CURDIR)`: run it as `make -C <repo> <verb>` from anywhere.
- **Contracts are versioned separately from the tag.** `icons/schema.json` and `templates/**/*.vars.schema.json` carry `schema_major`; the tag answers "which corpus", `schema_major` answers "can this consumer parse it". Raising `schema_major` requires a MAJOR tag even when no path moved.
- **Name no destination.** This repo says what is *inside* a class (`catalog.yaml`); the consumer's manifest says *where* a class deploys. A spine path, an absolute install dir, or another repo's directory name in this tree is a defect, not documentation.
- **One class per tag.** A migration slice lands one class, proves it (`make gates` green on a fresh clone), tags, and only then does the consumer pin it. Deletion in the consumer follows its own green proof, never precedes it.
- Prefer executed output over recalled text. Read files, run commands (`make gates`, `git ls-remote --tags`, `python3 scripts/validate-catalog.py`), paste results. `Evidence:` a claim about this repo by naming the command and its exit code; `Verify:` gives the one-liner a reviewer repeats.
- When findings contradict an earlier claim, state the discrepancy and trust the evidence.

## 3. OpenSpec + BMAD routing (via tickets)

- All work starts as a ticket in `tickets/` (`_template/`, vocab + rollup in `INDEX.md`, flow in `LIFECYCLE.md`). Triage with `/triage` (lanes in `tickets/_fixtures/router-lanes.md`).
- Broad scope (product, requirements, architecture, cross-device design) → BMAD. Only installed skills: `bmad`, `bmad-build` — say so when a step needs a missing skill instead of improvising.
- Bounded slices (one proposal + spec + design + tasks) → OpenSpec (`/opsx-propose`, `/opsx-apply`, `/opsx-archive`). Artifact rules in `openspec/config.yaml` restate this evidence rule per artifact.
- Never work on main: `scripts/worktree-guard.sh create <id> <slug>` scaffolds `ticket/<id>-<slug>` + worktree, aborts when dirty. Record worktree/branch in the ticket.
- Keep changes small, verifiable, committable. Never mix planning edits with implementation in one turn.

## 4. The tree, and what "green" means here

```text
catalog.yaml          what is inside each class + schema_major per schema-bearing class (no spine path)
icons/templates/      icon template per group (the corpus arrives in a later slice)
icons/mappings/       group → color mapping files (the corpus arrives in a later slice)
icons/schema.json     the icons contract: schema_major, group → variants → template path, placeholder rules
templates/            Jinja sources + one *.vars.schema.json per template (9 + 9 at v0.4.0)
configs/              static config corpus (compositor, editor, shell, prompt)
content/              binary/large content (wallpapers, authored themes)
desktop/              applications/ (*.desktop) + scripts/ (host scripts) + desktop.yaml (requires/optional)
scripts/              validate-catalog.py, validate-icons.py, validate-content.py, validate-templates.py, ci-gates-parity.py, worktree-guard.sh — validators only
.github/workflows/    one CI job per `make gates` target + ci-gates-parity
```

`make gates` exits 0 only when the corpus is *shippable*, not merely parseable. Because a hand-maintained gate list drifts, `scripts/ci-gates-parity.py` compares the workflow's job keys against this `Makefile`'s gate set and fails naming anything unmatched **in either direction**; `make gates-ci` is that superset and is what CI runs.

**Generated and mutable artifacts are never assets.** `icons.json`, `settings.toml`, rendered `kitty.conf`/`btop.conf`/`.zshrc`, palette/`current/` state and `btop/active-theme` are produced by the consumer or by the runtime, so committing them would make this repo a second source of truth. This is mechanical, not a convention: `make validate` fails naming the offending path (prove it with `touch icons/mappings/icons.json && make validate` → non-zero, then remove the file and it passes again).

`Evidence: MISSING` for anything the tree does not yet contain — e.g. the `.desktop` entries and
`desktop/scripts/` arrive in a later slice, and `catalog.yaml` records that class as `empty` rather
than describing content this repo does not have.
