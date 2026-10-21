#!/usr/bin/env python3
"""ci-gates-parity — the workflow's job set must equal `make gates` plus declared CI-only jobs.

WHY THIS EXISTS. A hand-maintained job list drifts from the gate list the first time one
side is edited, and both directions of drift are invisible: a gate that runs locally and
never on a push (the failure this repo cannot otherwise detect), and a CI-only job that no
developer ever runs. The authoritative set is parsed from the `Makefile` (`GATES`), never
copied here, so the Makefile stays the one place the gate set is written.

COPIED AND RETARGETED. This is the `dotfiles-v3` `scripts/ci-gates-parity.py` mechanism
(two-direction comparison, declared differences instead of assumed correspondences) with the
retargeting the `cli-output` precedent established for a repo that has no Python project:

  * the workflow is read with the STANDARD LIBRARY, not PyYAML. `dotfiles-v3` parses YAML
    because it carries a provisioning project that ships PyYAML; this repository is
    data-only (spine AD-2) and must pass `make gates-ci` on a fresh clone with no venv and
    no network. The scanner reads the flat `jobs:` mapping of two-space keys that every
    workflow in this org uses, and REFUSES to guess — a missing `jobs:` block, a key that
    is not at two spaces, or zero jobs found is a hard failure, never an empty set.
  * the gate-exclusion tables therefore default to empty, and `CI_ONLY_EXEMPT` carries the
    one job that exists in CI without being a gate: this check itself, plus any release
    job, each with a reason and a stale-entry check in the other direction.

Usage: ``python3 scripts/ci-gates-parity.py [--root REPO_ROOT]``
Exit 0 = the two sets are equal modulo the declared tables.
Exit 1 = an unmatched/stale entry in either direction, or an unreadable input.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAKEFILE = "Makefile"
WORKFLOW = ".github/workflows/gates.yml"

# Jobs that are deliberately NOT `make` gates, with the reason they exist in CI only.
# An entry that no longer names a real job fails as stale, so this cannot become a
# place where a dead job is quietly tolerated.
CI_ONLY_EXEMPT: dict[str, str] = {
    "ci-gates-parity": (
        "this check: it compares the workflow against GATES, so it needs the workflow "
        "file to mean anything. It is reachable locally as `make ci-gates-parity` and "
        "runs in CI as its own job; it is not a member of GATES"
    ),
}

# Gates in `GATES` with deliberately NO CI job, each with the reason it cannot run on
# a stock runner. EMPTY: the whole gate set is stock-runner capable (stdlib + git +
# python3; `shellcheck` ships on `ubuntu-latest`). Removing a gate from CI without an
# entry here fails, and an entry for a gate that does have a job fails as stale.
CI_EXCLUDED_GATES: dict[str, str] = {}

# Gates that DO run in CI but on a capable self-hosted runner: (job key, why the stock
# set excludes it, why it still runs in CI). EMPTY for the same reason.
CI_SELF_HOSTED_GATES: dict[str, tuple[str, str, str]] = {}

GATES_ASSIGNMENT = re.compile(r"^\s*GATES\s*[:+?]?=\s*(.*)$")
MAKE_TARGET = re.compile(r"^([A-Za-z0-9_.-]+)\s*:")
JOB_KEY = re.compile(r"^  ([A-Za-z0-9_.-]+):\s*$")


class Drift(Exception):
    """A parse failure: this script fails rather than guessing."""


def parse_gates(text: str) -> list[str]:
    """Return the `GATES` members, in declaration order."""
    joined = re.sub(r"\\\n", " ", text)
    for raw in joined.splitlines():
        match = GATES_ASSIGNMENT.match(raw.split("#", 1)[0])
        if match:
            gates = match.group(1).split()
            if not gates:
                raise Drift(f"{MAKEFILE}: `GATES` is empty; refusing to compare nothing")
            return gates
    raise Drift(f"{MAKEFILE}: no `GATES := ...` assignment found")


def parse_targets(text: str) -> set[str]:
    """Return every target the Makefile defines, so a listed gate must exist."""
    return {
        match.group(1)
        for raw in text.splitlines()
        if (match := MAKE_TARGET.match(raw))
    }


def parse_jobs(text: str) -> list[str]:
    """Return the workflow's job keys (the two-space keys under `jobs:`), in order."""
    jobs: list[str] = []
    in_jobs = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not in_jobs:
            if re.match(r"^jobs:\s*$", raw):
                in_jobs = True
            continue
        if not raw.startswith(" "):
            break
        indent = len(raw) - len(raw.lstrip(" "))
        if indent > 2:
            # A job body (`steps:`, `runs-on:`, ...): not a job key, not this
            # scanner's business.
            continue
        if indent != 2:
            raise Drift(
                f"{WORKFLOW}:{lineno}: a job key must sit at exactly two spaces under "
                f"`jobs:`; got {raw.strip()!r}. This scanner does not guess."
            )
        match = JOB_KEY.match(raw)
        if not match:
            raise Drift(
                f"{WORKFLOW}:{lineno}: expected `  <job-key>:` under `jobs:`; got "
                f"{raw.strip()!r}. This scanner does not guess."
            )
        jobs.append(match.group(1))
    if not jobs:
        raise Drift(
            f"{WORKFLOW}: no jobs found under `jobs:` — an empty job set would make every "
            f"other check vacuously true"
        )
    return jobs


def check(gates: list[str], targets: set[str], jobs: list[str]) -> tuple[list[str], list[str]]:
    """Return (errors, notes). Errors are drift; notes are declared differences."""
    errors: list[str] = []
    notes: list[str] = []
    job_set, gate_set = set(jobs), set(gates)
    excluded = set(CI_EXCLUDED_GATES) | set(CI_SELF_HOSTED_GATES)
    self_hosted_jobs = {job for (job, _s, _c) in CI_SELF_HOSTED_GATES.values()}

    # 0. Every gate must be a real target: a typo here would silently compare names
    #    that no `make` invocation can run.
    for gate in gates:
        if gate not in targets:
            errors.append(f"GATES lists {gate!r} but the {MAKEFILE} defines no such target")

    # 1. A gate with no job runs on every developer machine and never on a push.
    for gate in gates:
        if gate not in job_set and gate not in excluded:
            errors.append(
                f"gate {gate!r} has no CI job and is not in CI_EXCLUDED_GATES / "
                f"CI_SELF_HOSTED_GATES -- it would run locally and never in CI"
            )

    # 2. A job that is not a gate runs something the developer gate set does not.
    for job in jobs:
        if job in gate_set or job in self_hosted_jobs:
            continue
        if job in CI_ONLY_EXEMPT:
            notes.append(f"declared CI-only job {job!r}: {CI_ONLY_EXEMPT[job]}")
            continue
        errors.append(
            f"CI job {job!r} is not a GATES member and is not declared in "
            f"CI_ONLY_EXEMPT -- either add the gate or declare why the job is CI-only"
        )

    # 3. No gate and no job may be claimed twice.
    if len(set(gates)) != len(gates):
        errors.append(f"GATES lists a duplicate member: {gates}")
    if len(job_set) != len(jobs):
        errors.append(f"{WORKFLOW} defines a duplicate job key: {jobs}")

    # 4. Declared entries must not be stale in the other direction either.
    for job in CI_ONLY_EXEMPT:
        if job not in job_set:
            errors.append(
                f"CI_ONLY_EXEMPT declares {job!r} but no such workflow job exists "
                f"(stale exemption)"
            )
        if job in gate_set:
            errors.append(
                f"CI_ONLY_EXEMPT declares {job!r} but that job IS a GATES member "
                f"(stale exemption)"
            )
    for gate in CI_EXCLUDED_GATES:
        if gate not in gate_set or gate in job_set:
            errors.append(
                f"CI_EXCLUDED_GATES declares {gate!r} but that gate is not actually "
                f"missing from the workflow (stale exclusion)"
            )
    for gate, (job, _stock_why, _self_hosted_why) in CI_SELF_HOSTED_GATES.items():
        if gate not in gate_set or gate in job_set:
            errors.append(
                f"CI_SELF_HOSTED_GATES declares {gate!r} but that gate is not a GATES "
                f"member without a stock job (stale self-hosted declaration)"
            )
        if job not in job_set:
            errors.append(
                f"CI_SELF_HOSTED_GATES declares job {job!r} for gate {gate!r} but the "
                f"workflow has no such job"
            )
    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="workflow jobs == `make gates` + declared jobs")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent

    makefile_path, workflow_path = root / MAKEFILE, root / WORKFLOW
    for path, label in ((makefile_path, MAKEFILE), (workflow_path, WORKFLOW)):
        if not path.is_file():
            print(f"ci-gates-parity: FAIL -- MISSING {label}: {path}")
            return 1

    try:
        makefile_text = makefile_path.read_text()
        gates = parse_gates(makefile_text)
        targets = parse_targets(makefile_text)
        jobs = parse_jobs(workflow_path.read_text())
    except Drift as exc:
        print(f"ci-gates-parity: FAIL -- {exc}")
        return 1

    errors, notes = check(gates, targets, jobs)

    print(f"ci-gates-parity: GATES ({len(gates)}): " + " ".join(gates))
    print(f"ci-gates-parity: workflow jobs ({len(jobs)}): " + " ".join(jobs))
    for note in notes:
        print(f"ci-gates-parity: note: {note}")
    print(
        f"ci-gates-parity: declared exclusions ({len(CI_EXCLUDED_GATES)}): "
        + (" ".join(CI_EXCLUDED_GATES) or "(none)")
    )
    print(
        f"ci-gates-parity: declared self-hosted gates ({len(CI_SELF_HOSTED_GATES)}): "
        + (
            ", ".join(f"{g}->{j}" for g, (j, _s, _c) in CI_SELF_HOSTED_GATES.items())
            or "(none)"
        )
    )

    if errors:
        print(
            f"ci-gates-parity: FAIL -- {len(errors)} unmatched/stale "
            f"entr{'y' if len(errors) == 1 else 'ies'}:"
        )
        for error in errors:
            print(f"  - {error}")
        print(
            "  Fix the workflow, the Makefile, or the declared table in this script -- "
            "in whichever is actually wrong -- rather than silencing this check."
        )
        return 1

    print(
        "ci-gates-parity: PASS -- every GATES member has a CI job and every CI job is a "
        "GATES member or a declared CI-only job"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
