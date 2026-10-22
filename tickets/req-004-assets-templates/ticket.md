---
id: REQ-004
title: "S3 assets cut: templates class, per-template vars schemas, v0.4.0"
kind: requirement
status: in-progress
size: M
lane: bmad-advisory
links:
  openspec: assets-catalog
  bmad: none
worktree: .worktrees/s3/
branch: ticket/s3-assets-templates
children: []
---

# S3 assets cut: `templates` class, per-template vars schemas, `v0.4.0`

## Requirement

Land every Jinja source in `dotfiles-assets` with its body unchanged — zsh `.zshrc.j2`, wlogout
`style.css.tpl`, kitty `kitty.conf.j2`, btop `btop.conf.j2` and the five display-manager templates —
one `*.vars.schema.json` beside each, and a `make validate-templates` gate that makes the render
contract executable (spine AD-8/AD-9). Cut `v0.4.0`; the consumer rewires five roles, adds the
required-var parity test and deletes its template sources in a separate commit there.

## Acceptance

- [x] 9 templates imported byte-for-byte into `templates/{zsh,wlogout,kitty,btop,display-manager}/`;
      `diff` exit 0 for each against the consumer's source (run before the consumer deletion), and
      the 9 sha256 values recorded below.
- [x] 9 `*.vars.schema.json`, one beside each template: `schema_major: 1`, typed `properties`,
      disjoint `required`/`optional`, `additionalProperties: false`; **24 required variables, zero
      optional**, every name derived from the template body.
- [x] `make validate-templates` is a `GATES` member with its own CI job; it asserts pairing (both
      directions), contract == body, non-empty `required` where the body reads something, no
      `default(` on a required var, real 2020-12 keywords, and (when `jsonschema` is importable)
      the 2020-12 metaschema plus closed-world/required-missing negative instances.
- [x] `templates/example.vars.schema.json` removed once real contracts existed; the class README
      carries the inventory, the rules and the `{{ }}` vs `{% %}` distinction.
- [x] `catalog.yaml` declares five group subdirectories and a glob class contract
      (`templates/**/*.vars.schema.json`); `validate-catalog.py` holds every glob match to the
      catalog's `schema_major` rather than one arbitrary representative.
- [x] The openspec spec gains the templates requirement with executable acceptance commands.
- [ ] `make gates`, `make gates-ci` and `make hermetic` exit 0 (worktree, hermetic and a fresh
      anonymous clone).
- [ ] Annotated `v0.4.0` pushed and anonymously fetchable (tag object + peeled commit recorded);
      GitHub Release published with notes and no assets; CI green on `master`.

## Deviation: the plan's "10 templates" is 9

`SLICES.md` S3's acceptance block expects `validate-templates` to report "10 templates, 10 schemas".
The corpus measures **9**: zsh 1 + wlogout 1 + kitty 1 + btop 1 + display-manager 5. The
`EVIDENCE-INDEX.md` per-file measurement is the 9-file set (`1/0/0/3/1` for the display-manager
templates plus the four role/repo sources), so the "10" is an arithmetic slip in the plan, not a
missing file. The gate reports the measured 9/9.

## Deviation: `config.toml.j2` requires two names, not one

`EVIDENCE-INDEX.md` records `1` variable for `display-manager/config.toml.j2` from a
`grep -oE '\{\{[^}]+\}\}'` count. That grep cannot see `display_manager_greeter_type`, which the
template reads in an `{% if %}`. The contract requires both names; `validate-templates` reads both
expression forms so the next branch-only variable cannot be missed the same way.

## Evidence

- Byte identity (before any consumer deletion): `diff -u` of all nine pairs → rc 0; sha256 of the
  nine imported files: `.zshrc.j2 d4850643…f75c3`, `style.css.tpl abc544b5…f0160`,
  `kitty.conf.j2 d9da04d4…c3050`, `btop.conf.j2 323aae65…12526`, `config.toml.j2 f9dfc4e5…0461db`,
  `hypr-session.j2 2658b624…b11`, `regreet.css.j2 13489fb2…b80`, `regreet.toml.j2 26424694…32fff9`,
  `sddm.conf.j2 3e7e62c7…d2fd9`.
- `make validate-templates` → rc 0: `templates=9 schemas=9`, `groups: btop(1) display-manager(5)
  kitty(1) wlogout(1) zsh(1)`, `vars: required=24 optional=0`.
- Negative proofs (each in a throwaway copy, restored after): an undeclared `{{ UNDECLARED_VAR }}`
  read → FAIL naming the schema and the name; `default(` on `STARSHIP_CONFIG` → FAIL naming the
  variable; a deleted `kitty.conf.vars.schema.json` → FAIL naming the unpaired template; an invented
  required name → FAIL ("the schema declares [...], which the template never reads"); a misspelled
  keyword (`requird`) → FAIL ("not a JSON Schema 2020-12 keyword").
- Deep mode: `uv run --with jsonschema python scripts/validate-templates.py` → rc 0, "every schema
  validates against the draft 2020-12 metaschema and rejects an undeclared / required-missing
  instance"; the stdlib run prints a NOTE when that mode is skipped.
