# dotfiles-assets — validation verbs only (spine AD-2).
#
# This repository is DATA: five class directories behind one annotated semver tag.
# There is no package, no console script, no build, no install and no sync verb.
# The icon renderer, the palette generator and the provisioner are separate pinned
# repos; an `install`/`build` verb here would be the first step back toward one of
# them living inside the corpus.
#
# Every verb is anchored on $(CURDIR), so `make -C <repo> gates` works from any cwd.
# `make hermetic` goes further on purpose: it runs the same checks from a FOREIGN cwd
# with empty HOME/XDG_*, so a validator that only works from its own directory, or
# that reads a provisioned corpus off the host, cannot pass.
#
# Fresh clone (no virtualenv, no network beyond the clone itself):
#   make help        this list
#   make validate    catalog <-> class dirs, schema JSON, AD-11 absence check
#   make lint        shellcheck over desktop/scripts/** + compileall scripts/
#   make gates       validate + lint + hermetic  (the developer gate set)
#   make gates-ci    the same gate set, reproducible without a workflow runner
#   make hermetic    validate + lint with empty HOME/XDG_* and a foreign cwd
#
# `ci-gates-parity` compares the workflow's job keys against the `GATES` variable and
# fails naming anything unmatched in EITHER direction, so the two lists cannot drift.
# It is not a member of `GATES`: it needs the workflow file, which only CI and a
# checkout have, and it is declared as a CI-only job in the script itself.

SHELL := /bin/sh
PYTHON ?= python3

# The developer gate set. `gates` runs ALL of it: a gate that is not run here is a
# gate nobody runs.
GATES := validate lint hermetic

# The env every hermetic command runs with: nothing inherited but PATH. HOME and the
# four XDG_* dirs point into a throwaway tree this recipe creates and deletes.
EMPTY_ENV = env -i PATH="$$PATH" HOME="$$home" XDG_DATA_HOME="$$data" \
	XDG_CONFIG_HOME="$$config" XDG_CACHE_HOME="$$cache" XDG_STATE_HOME="$$state"

.PHONY: help validate lint gates gates-ci ci-gates-parity hermetic

help:
	@printf '%s\n' \
	  'validate         catalog <-> class dirs, schema JSON well-formedness, AD-11 absence check' \
	  'lint             shellcheck desktop/scripts/** (vacuous until it has scripts) + compileall scripts/' \
	  'gates            validate + lint + hermetic (the developer gate set)' \
	  'gates-ci         the same gate set, reproducible without a workflow runner' \
	  'ci-gates-parity  workflow job set == GATES + declared CI-only jobs, both directions' \
	  'hermetic         validate + lint with empty HOME/XDG_* from a foreign cwd' \
	  '' \
	  'Data repository: there is no build, install, sync or release verb (spine AD-2).'

# Catalog <-> class-dir agreement + schema JSON + the AD-11 absence check. All three
# live in one validator because they answer one question: "is this tree a shippable
# corpus envelope?" Stdlib-only, so a fresh clone passes with no venv and no network.
validate:
	@$(PYTHON) "$(CURDIR)/scripts/validate-catalog.py"

# Shell scripts must be shellcheck-clean, and the validators must at least compile.
# `desktop/scripts/` is empty in v0.1.0, so shellcheck is a VACUOUS PASS and says so
# out loud -- a silent skip and a pass would be indistinguishable in a green log.
# Bytecode goes to a throwaway PYTHONPYCACHEPREFIX, so linting never dirties the tree.
lint:
	@set -eu; \
	root="$(CURDIR)"; \
	tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp"' EXIT INT TERM; \
	PYTHONPYCACHEPREFIX="$$tmp/pycache" $(PYTHON) -m compileall -q "$$root/scripts"; \
	echo "lint: compileall $$root/scripts -> ok"; \
	find "$$root/desktop/scripts" -type f \( -name '*.sh' -o -perm -u+x \) -print \
	  > "$$tmp/scripts.list" 2>/dev/null || true; \
	if [ -s "$$tmp/scripts.list" ]; then \
	  command -v shellcheck >/dev/null 2>&1 || { \
	    echo "lint: FAIL -- shellcheck is not installed but desktop/scripts holds script(s):" >&2; \
	    sed 's/^/  /' "$$tmp/scripts.list" >&2; \
	    exit 1; \
	  }; \
	  echo "lint: shellcheck -> $$(wc -l < "$$tmp/scripts.list") script(s) under desktop/scripts"; \
	  xargs shellcheck < "$$tmp/scripts.list"; \
	  echo "lint: shellcheck -> clean"; \
	else \
	  echo "lint: shellcheck -> 0 executable scripts under desktop/scripts (vacuous pass)"; \
	fi

gates: $(GATES)

# The CI set: the same gates, reproducible by a developer without a workflow runner.
# `ci-gates-parity` is NOT a member: it compares the workflow file, so it is reachable
# here as its own target and declared as a CI-only job in `scripts/ci-gates-parity.py`.
gates-ci: $(GATES)

# Workflow <-> Makefile parity. Belongs in the CI set, not in `gates`: it compares
# the workflow file, so it only means something where the workflow exists.
ci-gates-parity:
	@$(PYTHON) "$(CURDIR)/scripts/ci-gates-parity.py"

# The reproduction command for "green because the corpus is green, not because the
# host is provisioned": empty HOME + four XDG dirs, a foreign cwd, `env -i` so no
# inherited variable leaks in. It re-runs the checks itself rather than depending on
# the `validate`/`lint` targets, because a hermetic run that reuses another target's
# state is not a hermetic run.
hermetic:
	@set -eu; \
	root="$(CURDIR)"; \
	tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp"' EXIT INT TERM; \
	home="$$tmp/home"; data="$$tmp/xdg-data"; config="$$tmp/xdg-config"; \
	cache="$$tmp/xdg-cache"; state="$$tmp/xdg-state"; cwd="$$tmp/cwd"; \
	mkdir -p "$$home" "$$data" "$$config" "$$cache" "$$state" "$$cwd"; \
	cd "$$cwd"; \
	echo "hermetic: cwd=$$cwd HOME=$$home XDG_DATA_HOME=$$data (empty, foreign)"; \
	$(EMPTY_ENV) $(PYTHON) "$$root/scripts/validate-catalog.py"; \
	$(EMPTY_ENV) PYTHONPYCACHEPREFIX="$$tmp/pycache" $(PYTHON) -m compileall -q "$$root/scripts"; \
	echo "hermetic: compileall $$root/scripts -> ok (bytecode outside the tree)"; \
	find "$$root/desktop/scripts" -type f \( -name '*.sh' -o -perm -u+x \) -print \
	  > "$$tmp/scripts.list" 2>/dev/null || true; \
	if [ -s "$$tmp/scripts.list" ]; then \
	  command -v shellcheck >/dev/null 2>&1 || { \
	    echo "hermetic: FAIL -- shellcheck is not installed but desktop/scripts holds script(s):" >&2; \
	    sed 's/^/  /' "$$tmp/scripts.list" >&2; \
	    exit 1; \
	  }; \
	  $(EMPTY_ENV) xargs shellcheck < "$$tmp/scripts.list"; \
	  echo "hermetic: shellcheck -> $$(wc -l < "$$tmp/scripts.list") script(s) clean"; \
	else \
	  echo "hermetic: shellcheck -> 0 executable scripts under desktop/scripts (vacuous pass)"; \
	fi; \
	echo "hermetic: PASS -- the corpus validates with no HOME, no XDG state and a foreign cwd"
