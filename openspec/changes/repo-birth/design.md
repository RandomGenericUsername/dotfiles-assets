# Design

## Decisions

### D1 — Data only: validators under `scripts/`, no package

**Decision.** No `src/`, no importable package, no `[project.scripts]`, no console script. Python
exists only as `scripts/validate-catalog.py` and `scripts/ci-gates-parity.py`, executed by the
`Makefile` and CI. `pyproject.toml` is dev-only tooling (`package = false`, no `[build-system]`).

**Why.** The renderer is `itr`, the palette generator is `csg`, the provisioner is the installer —
each already released and pinned. A renderer inside the corpus would immediately couple a corpus
tag to code changes and re-open the split that this repository exists to make possible (spine AD-2).

**Cost accepted.** Two `python3` processes per gate run instead of one import; no shared helper
module. At this size that is cheaper than a package, its build metadata and its install story.

### D2 — Stdlib-only validators, and a deliberately small YAML subset

**Decision.** `validate-catalog.py` imports nothing outside the standard library. It parses
`catalog.yaml` with a narrow reader (nested mappings, scalar lists, `null`, `[]`, quoted/bare
scalars, full-line comments) and **errors** on anything else — tabs, block scalars, flow
collections, anchors, multi-line values.

**Why.** A gate that requires `uv sync` first is not a fresh-clone gate, and the fresh-clone run is
the one that proves the ritual. Refusing unsupported YAML is what keeps the parser honest: a
silently mis-parsed catalog would make every other check vacuously true.

**Cost accepted.** ~120 lines of parser, and a `catalog.yaml` that must stay in the supported
subset. The file is authored here and changes rarely; the alternative (PyYAML) costs a venv on
every fresh clone and in CI.

### D3 — Three checks in one `validate` target

**Decision.** Catalog ⇄ dirs, schema JSON well-formedness, and the generated-artifact absence check
live in one script under one `make validate`.

**Why.** They answer one question — "is this tree a shippable corpus envelope?" — and all three are
cheap, file-local and stdlib-only. Splitting them would give three jobs in CI for the same tree
read. The class validators (which need real corpora and, in the templates case, Jinja/JSON-Schema
libraries) stay separate and arrive with the corpus.

### D4 — `hermetic` re-runs the checks, it does not depend on them

**Decision.** The `hermetic` target runs its own `validate-catalog.py` and `compileall` inside
`env -i` with empty `HOME`/`XDG_*` and a foreign cwd. It does not list `validate lint` as
prerequisites.

**Why.** A hermetic run that reuses another target's execution is not a hermetic run: make would
evaluate prerequisites in the ambient environment first, and the property being tested (no host
state is read) would be untested for anything that already ran. The duplication is two command
lines.

**Verification.** `make hermetic` prints the `HOME`, the `XDG_DATA_HOME` and the foreign cwd it
used, so a reader can see the property rather than trust it.

### D5 — CI parity reads `GATES`, stdlib-only, in both directions

**Decision.** `scripts/ci-gates-parity.py` parses `GATES` from the `Makefile` (never a copy) and the
workflow's two-space `jobs:` keys (stdlib only), then fails on anything unmatched in either
direction, plus stale declared entries. `ci-gates-parity` is a CI-only job, declared with a reason.

**Why.** The drift is invisible by nature: a gate running only on a laptop looks exactly like a gate
running everywhere. `dotfiles-v3`'s copy parses YAML with PyYAML; this repository has no Python
project to carry that dependency (D2), so the copy is retargeted the way the `cli-output` repo
already retargets it — and the scanner fails rather than guessing when the workflow shape is not the
flat form it understands.

## Trade-offs and rejected alternatives

- **Five tags, one per class.** Rejected: five pins to bump per release and five answers to "which
  tag are the icons at?" (spine AD-3).
- **One `schema.json` for everything.** Rejected: the icons contract and a template's vars schema
  answer different questions and move on different schedules; a template added in a MINOR must not
  need the icons contract re-read.
- **Shipping example content so the gates are non-vacuous.** Rejected: example content is corpus
  nobody wants and a second thing to keep true. The gates state their vacuity out loud instead
  ("0 executable scripts under desktop/scripts (vacuous pass)"), and each class validator lands with
  the corpus that makes it real.

## Verification plan

| Decision | Command | Expected |
| --- | --- | --- |
| D1 data-only | `test ! -d src && rg -n '\[project.scripts\]' pyproject.toml` | `NO_PACKAGE_ROOT`, rg exit 1 |
| D2 stdlib-only | `make validate` from a fresh clone with no venv | exit 0 |
| D2 parser honesty | add a tab-indented line to `catalog.yaml` and `make validate` | non-zero, names the line |
| D3 envelope checks | `touch icons/mappings/icons.json && make validate` | non-zero, names the path; exit 0 after removal |
| D4 hermetic | `make hermetic` | exit 0, prints the throwaway `HOME` and foreign cwd |
| D5 parity | `make ci-gates-parity`; then add a job with no gate | exit 0 first; non-zero naming the job second |
| Harness fidelity | `diff -u` against `mu` for each copied harness file | exit 0, no output |
| Fresh clone | `git clone <repo> /tmp/fresh && cd /tmp/fresh && make gates` | exit 0 |
| Tag ritual | `git ls-remote --tags <repo> 'v0.1.0'` | tag object line + peeled `^{}` line |
