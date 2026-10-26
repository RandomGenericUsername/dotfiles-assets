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
#   make help            this list
#   make validate        catalog <-> class dirs, schema JSON, AD-11 absence check
#   make validate-icons  every mapping template resolves, placeholders declared, SVGs parse
#   make validate-content  the wallpaper tarball holds a top-level default.png, themes non-empty
#   make validate-templates  one vars schema per template; the schema equals the body it describes
#   make validate-configs  deployment-fixed configs, one reviewed render token, wlogout Logout = uwsm stop, no mutable/rendered files
#   make validate-desktop  every .desktop parses, Exec/TryExec name declared binaries, scripts shellcheck-clean
#   make lint            shellcheck over desktop/scripts/** + compileall scripts/
#   make gates           validate + validate-icons + validate-content + validate-templates + validate-configs + validate-desktop + lint + hermetic
#   make gates-ci        the same gate set, reproducible without a workflow runner
#   make hermetic        the same checks with empty HOME/XDG_* and a foreign cwd
#
# `ci-gates-parity` compares the workflow's job keys against the `GATES` variable and
# fails naming anything unmatched in EITHER direction, so the two lists cannot drift.
# It is not a member of `GATES`: it needs the workflow file, which only CI and a
# checkout have, and it is declared as a CI-only job in the script itself.

SHELL := /bin/sh
PYTHON ?= python3

# The developer gate set. `gates` runs ALL of it: a gate that is not run here is a
# gate nobody runs.
GATES := validate validate-icons validate-content validate-templates validate-configs validate-desktop lint hermetic

# The env every hermetic command runs with: nothing inherited but PATH. HOME and the
# four XDG_* dirs point into a throwaway tree this recipe creates and deletes.
EMPTY_ENV = env -i PATH="$$PATH" HOME="$$home" XDG_DATA_HOME="$$data" \
	XDG_CONFIG_HOME="$$config" XDG_CACHE_HOME="$$cache" XDG_STATE_HOME="$$state"

.PHONY: help validate validate-icons validate-content validate-templates validate-configs validate-desktop lint gates gates-ci ci-gates-parity hermetic

help:
	@printf '%s\n' \
	  'validate          catalog <-> class dirs, schema JSON well-formedness, AD-11 absence check' \
	  'validate-icons    mapping templates resolve, {{COLOR_*}} tokens declared, every SVG parses' \
	  'validate-content  tarball has a top-level default.png, every *.theme is non-empty' \
	  'validate-templates  every *.j2/*.tpl has a vars schema that equals its body; no default() on required' \
	  'validate-configs  deployment-fixed configs; one reviewed render token; wlogout Logout = uwsm stop; no mutable/rendered files' \
	  'validate-desktop  every .desktop parses, Exec/TryExec name declared binaries, scripts shellcheck-clean' \
	  'lint              shellcheck desktop/scripts/** + compileall scripts/' \
	  'gates             validate + validate-icons + validate-content + validate-templates + validate-configs + validate-desktop + lint + hermetic' \
	  'gates-ci          the same gate set, reproducible without a workflow runner' \
	  'ci-gates-parity   workflow job set == GATES + declared CI-only jobs, both directions' \
	  'hermetic          the same checks with empty HOME/XDG_* from a foreign cwd' \
	  '' \
	  'Data repository: there is no build, install, sync or release verb (spine AD-2).'

# Catalog <-> class-dir agreement + schema JSON + the AD-11 absence check. All three
# live in one validator because they answer one question: "is this tree a shippable
# corpus envelope?" Stdlib-only, so a fresh clone passes with no venv and no network.
validate:
	@$(PYTHON) "$(CURDIR)/scripts/validate-catalog.py"

# The icons corpus. Three separate failures are caught here, and each one is a
# release-time failure only because this gate exists: a mapping entry whose
# template was deleted, a placeholder no group (and not defaults.yaml) declares,
# and an SVG that is not well-formed XML. Run it against the corpus, not against a
# consumer's deployed copy -- the tag must be shippable before it is published.
validate-icons:
	@$(PYTHON) "$(CURDIR)/scripts/validate-icons.py"

# The content corpus. The tarball's top-level default.png is asserted at deploy
# time by the installer, but by then the tag is published; this asserts it before
# the tag. Authored *.theme files must be non-empty (a zero-byte theme renders as
# "no theme" on a host).
validate-content:
	@$(PYTHON) "$(CURDIR)/scripts/validate-content.py"

# The templates class. This is the gate that makes the render contract executable:
# a template with no schema, a schema that declares a name its body never reads, and
# a `default(` fallback on a required value all fail here — before the tag, not on a
# user's machine at render time. It reads BOTH `{{ }}` and `{% %}` expressions, so a
# branch-only variable (config.toml.j2's greeter type) is required too.
validate-templates:
	@$(PYTHON) "$(CURDIR)/scripts/validate-templates.py"

# The configs class (AD-11, R-05/R-06). The four release-time commands become one
# executable gate: no *.j2/*.tpl source, no mutable/rendered file, exactly one
# render token at configs/hypr/hyprland.lua:7, every file non-empty. A second token
# fails naming both files and lines — that is the exception's ratchet.
validate-configs:
	@$(PYTHON) "$(CURDIR)/scripts/validate-configs.py"

# The desktop class (spine AD-10, layer 1). Static by design: it parses the six
# entries, tokenizes each `Exec` with the spec's quoting rules, requires `TryExec`
# to name the same declared binary `Exec` launches, and holds `desktop.yaml` to the
# exact `.desktop` set both ways. `shellcheck` is the shell half of the same layer
# and runs HERE as well as in `lint`: a reviewer who runs only this target must not
# get a half-validated class. A missing shellcheck with scripts present is a
# FAILURE, not a skip — a silent skip and a pass are indistinguishable in a log.
validate-desktop:
	@set -eu; \
	root="$(CURDIR)"; \
	$(PYTHON) "$$root/scripts/validate-desktop.py"; \
	tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp"' EXIT INT TERM; \
	find "$$root/desktop/scripts" -type f \( -name '*.sh' -o -perm -u+x \) -print \
	  > "$$tmp/scripts.list" 2>/dev/null || true; \
	if [ -s "$$tmp/scripts.list" ]; then \
	  command -v shellcheck >/dev/null 2>&1 || { \
	    echo "validate-desktop: FAIL -- shellcheck is not installed but desktop/scripts holds script(s):" >&2; \
	    sed 's/^/  /' "$$tmp/scripts.list" >&2; \
	    exit 1; \
	  }; \
	  xargs shellcheck < "$$tmp/scripts.list"; \
	  echo "validate-desktop: shellcheck -> $$(wc -l < "$$tmp/scripts.list") script(s) clean"; \
	else \
	  echo "validate-desktop: shellcheck -> 0 executable scripts (nothing to check)"; \
	fi

# Shell scripts must be shellcheck-clean, and the validators must at least compile.
# `desktop/scripts/` holds `toggle-touchpad` since v0.5.0, so shellcheck is a REAL
# check here (it was a vacuous pass while the class was empty). It also runs inside
# `validate-desktop`: the desktop class's layer 1 owns its own scripts' hygiene, and
# this target is the class-independent sweep. Bytecode goes to a throwaway
# PYTHONPYCACHEPREFIX, so linting never dirties the tree.
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
	$(EMPTY_ENV) $(PYTHON) "$$root/scripts/validate-icons.py"; \
	$(EMPTY_ENV) $(PYTHON) "$$root/scripts/validate-content.py"; \
	$(EMPTY_ENV) $(PYTHON) "$$root/scripts/validate-templates.py"; \
	$(EMPTY_ENV) $(PYTHON) "$$root/scripts/validate-configs.py"; \
	$(EMPTY_ENV) $(PYTHON) "$$root/scripts/validate-desktop.py"; \
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
