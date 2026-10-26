#!/usr/bin/env python3
"""validate-templates -- the `templates` class contract, asserted against the corpus.

WHAT THIS GATE PROVES (spine AD-8):

  1. PAIRING IS COMPLETE, BOTH WAYS. Every `*.j2` / `*.tpl` has a sibling
     `<name>.vars.schema.json`, and every schema names a template that exists in
     its own directory. A template without a contract is a value the consumer
     cannot check; a schema without a template describes something nothing
     renders. Both are defects, so both fail.

  2. THE SCHEMA IS A WELL-FORMED CONTRACT. Each parses as JSON, declares
     `schema_major` (AD-12), names its sibling in `template`, is an object schema
     with typed `properties`, keeps `required` and `optional` disjoint and inside
     `properties`, and closes the world (`additionalProperties: false`).

  3. THE CONTRACT EQUALS WHAT THE TEMPLATE READS. Every name the template reads
     appears in `properties`; every `properties` entry is read by the template;
     `required ∪ optional` is exactly `properties`. That equality is what makes
     "no invented required vars" structural instead of a review habit: a name the
     body does not read cannot be required, and a read the body performs cannot be
     undeclared.

     It reads BOTH Jinja expression forms -- `{{ ... }}` and `{% ... %}`. A
     `{{ }}`-only grep reports one variable for `display-manager/config.toml.j2`
     and misses `display_manager_greeter_type`, which lives in an `{% if %}`: the
     template needs it, so the contract must require it.

  4. NO `default(` ON A REQUIRED VAR (AD-8.2). A fallback turns "the consumer
     forgot it" into "the file rendered with a wrong value". The check is
     deliberately blunt: if an expression containing `default(` also mentions a
     required name, the file fails. Grep-level rules are meant to be legible, not
     clever.

  5. `required` IS NON-EMPTY WHENEVER THE TEMPLATE READS A NAME. A template that
     interpolates nothing (regreet.css.j2, hypr-session.j2) legitimately declares
     `required: []`; a template with reads and no required names has a contract
     that constrains nothing.

  6. EVERY KEYWORD IS A REAL 2020-12 KEYWORD (or an `x-` extension). The subset
     each schema uses is type-checked and recursed into, and an unknown key is an
     error. That is what keeps "is this a valid JSON Schema?" answerable with the
     standard library: a typo like `"requird"` would otherwise be a keyword
     nothing reads and a rule nothing enforces.

  7. THE SDDM WAYLAND GREETER NAMES ITS COMPOSITOR. SDDM's implicit default is
     `weston --shell=kiosk`; a config that sets `DisplayServer=wayland` without a
     `[Wayland] CompositorCommand` line depends on that default invisibly, and a
     consumer that did not install weston gets a greeter display-server failure
     and an x11-user fallback. The sddm template must therefore render the
     section, read the optional override, and carry the exact fallback; the
     schema must keep that variable optional. The check is deliberately targeted:
     the template path is consumer-addressed, and the fallback string must match
     the package the consumer installs. When `jinja2` is importable the gate also
     renders the body with only the required variable and with an override;
     otherwise the exact default expression is still asserted statically, so the
     stdlib-only fresh-clone run cannot miss a deleted section.

WHY STDLIB ONLY. A fresh clone must pass `make gates` with no virtualenv and no
network (the S0 birth rule). The `jsonschema` package is NOT a dependency: when it
happens to be importable the gate additionally validates each schema against the
draft 2020-12 metaschema and proves the closed-world claim with a negative
instance; when it is absent the gate says so out loud rather than pretending the
deep check ran. Rule 6 is the check that always runs.

Usage: ``python3 scripts/validate-templates.py [--root REPO_ROOT]``
Exit 0 = every template has a contract that matches its body.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEMPLATES_DIR = "templates"
TEMPLATE_SUFFIXES = (".j2", ".tpl")
SCHEMA_SUFFIX = ".vars.schema.json"

#: Jinja statement/builtin vocabulary. A name found in an expression that is NOT
#: in this set, and is not preceded by `|` (a filter) or `.` (an attribute), is
#: treated as a template variable. The set is deliberately small: over-inclusion
#: produces a false "undeclared variable" error the author fixes in one edit;
#: under-inclusion would let a real read slip past the contract silently.
JINJA_WORDS = frozenset(
    {
        # statements
        "and", "or", "not", "in", "is", "if", "else", "elif", "for", "endfor",
        "endif", "block", "endblock", "macro", "endmacro", "set", "endset",
        "with", "endwith", "include", "import", "from", "as", "filter",
        "endfilter", "raw", "endraw", "call", "endcall", "do", "extends",
        "recursive", "scoped", "without", "context", "loop",
        # literals
        "true", "false", "none", "True", "False", "None", "null",
        # tests / operators / common filters used as words
        "defined", "undefined", "divisibleby", "even", "odd", "sameas",
        "default", "length", "count", "join", "lower", "upper", "title",
        "capitalize", "trim", "replace", "select", "reject", "map", "list",
        "sort", "reverse", "first", "last", "min", "max", "sum", "unique",
        "string", "int", "float", "bool", "batch", "slice", "format",
        "tojson", "urlencode", "indent", "center", "wordwrap", "groupby",
        "attr", "dictsort", "random", "safe", "e", "escape", "striptags",
    }
)

EXPRESSION = re.compile(r"\{\{(?P<expr>.*?)\}\}|\{%(?P<stmt>.*?)%\}", re.DOTALL)
STRING_LITERAL = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
DEFAULT_CALL = re.compile(r"\bdefault\s*\(")

#: Rule 7: the one deploy-critical template. The consumer addresses this path,
#: and the fallback string is the compositor package its role installs.
SDDM_TEMPLATE = "templates/display-manager/sddm.conf.j2"
SDDM_COMPOSITOR_VAR = "display_manager_sddm_compositor_command"
SDDM_COMPOSITOR_DEFAULT = "weston --shell=kiosk"
SDDM_COMPOSITOR_EXPRESSION = re.compile(
    r"\{\{\s*"
    + re.escape(SDDM_COMPOSITOR_VAR)
    + r"\s*\|\s*default\(\s*['\"]"
    + re.escape(SDDM_COMPOSITOR_DEFAULT)
    + r"['\"]\s*\)\s*\}\}"
)
INI_SECTION = re.compile(r"(?m)^\[(?P<name>[^\]]+)\]\s*$")

#: The 2020-12 keywords this class is allowed to use, with the JSON type each
#: value must have, plus this class's three extensions (rated at the top level
#: only). An unknown key is a hard error: a misspelled keyword is a rule that
#: silently does nothing, which is indistinguishable from a passing gate.
_KEYWORD_TYPES: dict[str, object] = {
    "$schema": str,
    "$id": str,
    "$comment": str,
    "title": str,
    "description": str,
    "type": (str, list),
    "enum": list,
    "const": object,
    "properties": dict,
    "patternProperties": dict,
    "additionalProperties": bool,
    "$defs": dict,
    "items": dict,
    "required": list,
    "minLength": int,
    "maxLength": int,
    "minimum": (int, float),
    "maximum": (int, float),
    "pattern": str,
    "format": str,
    "minItems": int,
    "maxItems": int,
    "uniqueItems": bool,
    "allOf": list,
    "anyOf": list,
    "oneOf": list,
    "examples": list,
    "deprecated": bool,
    "readOnly": bool,
    "writeOnly": bool,
    # This class's extensions (documented in templates/README.md).
    "schema_major": int,
    "template": str,
    "optional": list,
}

#: Keywords whose value is an object-of-schemas: each value is itself a schema.
_SCHEMA_MAPS = ("properties", "patternProperties", "$defs")

#: Keywords whose value is one schema.
_SCHEMA_SINGLE = ("items", "additionalItems", "propertyNames")

#: Keywords whose value is a list of schemas.
_SCHEMA_LISTS = ("allOf", "anyOf", "oneOf")



class TemplateError(Exception):
    """A violation, with the file and the reason a reader needs to fix it."""


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def template_reads(body: str) -> set[str]:
    """Return the names a template reads, from BOTH `{{ }}` and `{% %}` blocks.

    String literals are removed first, so `{% if type == 'regreet' %}` yields
    `type`, not `regreet`. Filters and attribute accesses are excluded by looking
    at the character before the identifier.
    """
    reads: set[str] = set()
    for match in EXPRESSION.finditer(body):
        expression = match.group("expr") or match.group("stmt") or ""
        cleaned = STRING_LITERAL.sub(" ", expression)
        for ident in IDENTIFIER.finditer(cleaned):
            name = ident.group(0)
            if name in JINJA_WORDS:
                continue
            prefix = cleaned[: ident.start()].rstrip()
            if prefix.endswith(("|", ".")):
                continue
            reads.add(name)
    return reads


def expected_schema(template: Path) -> Path:
    stem = template.name
    for suffix in TEMPLATE_SUFFIXES:
        if stem.endswith(suffix):
            return template.with_name(stem[: -len(suffix)] + SCHEMA_SUFFIX)
    raise TemplateError(f"{template}: not a template suffix {TEMPLATE_SUFFIXES}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TemplateError(message)


def _ini_section(body: str, name: str) -> str | None:
    """Return the text under `[name]`, up to the next section header (or EOF)."""
    match = re.search(rf"(?m)^\[{re.escape(name)}\]\s*$", body)
    if match is None:
        return None
    rest = body[match.end() :]
    next_section = INI_SECTION.search(rest)
    return rest[: next_section.start()] if next_section else rest


def check_sddm_wayland(
    template: Path, body: str, schema: dict, root: Path
) -> bool:
    """Rule 7: the SDDM body names its greeter compositor; return True if rendered.

    The static assertion always runs, so a fresh clone without Jinja2 still
    fails when the section or the fallback disappears. The render probe is the
    optional deep mode: required variables only must produce the template
    default, and the optional variable must override it.
    """
    rel = _rel(template, root)
    wayland = _ini_section(body, "Wayland")
    _require(
        wayland is not None,
        f"{rel}: no [Wayland] section -- the rendered config would depend on "
        f"SDDM's implicit `{SDDM_COMPOSITOR_DEFAULT}` fallback, which stays "
        f"invisible until a host without weston cannot start the greeter",
    )
    assert wayland is not None
    command_lines = [
        line.strip()
        for line in wayland.splitlines()
        if line.strip().startswith("CompositorCommand=")
    ]
    _require(
        len(command_lines) == 1,
        f"{rel}: [Wayland] must carry exactly one CompositorCommand line, found "
        f"{len(command_lines)}",
    )
    command = command_lines[0]
    _require(
        SDDM_COMPOSITOR_VAR in command,
        f"{rel}: CompositorCommand must read {SDDM_COMPOSITOR_VAR!r}, got "
        f"{command!r}",
    )
    _require(
        SDDM_COMPOSITOR_EXPRESSION.search(command) is not None,
        f"{rel}: CompositorCommand must default to {SDDM_COMPOSITOR_DEFAULT!r} "
        f"via `{SDDM_COMPOSITOR_VAR} | default(...)`, got {command!r}",
    )

    properties = schema.get("properties")
    optional = schema.get("optional")
    required = schema.get("required")
    _require(
        isinstance(properties, dict) and SDDM_COMPOSITOR_VAR in properties,
        f"{rel}: the schema must declare {SDDM_COMPOSITOR_VAR!r}",
    )
    _require(
        isinstance(optional, list) and SDDM_COMPOSITOR_VAR in optional,
        f"{rel}: {SDDM_COMPOSITOR_VAR!r} must be optional -- making it required "
        f"would break every consumer that renders the current context",
    )
    _require(
        isinstance(required, list) and SDDM_COMPOSITOR_VAR not in required,
        f"{rel}: {SDDM_COMPOSITOR_VAR!r} must not be required",
    )

    try:
        import jinja2
    except ImportError:
        return False
    try:
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        rendered = env.from_string(body).render(
            display_manager_sddm_display_server="wayland"
        )
        _require(
            f"CompositorCommand={SDDM_COMPOSITOR_DEFAULT}" in rendered,
            f"{rel}: rendering with only the required variable must produce "
            f"`CompositorCommand={SDDM_COMPOSITOR_DEFAULT}`, got:\n{rendered}",
        )
        override = "cage -- /usr/bin/sddm-greeter"
        rendered = env.from_string(body).render(
            display_manager_sddm_display_server="wayland",
            display_manager_sddm_compositor_command=override,
        )
        _require(
            f"CompositorCommand={override}" in rendered,
            f"{rel}: an explicit {SDDM_COMPOSITOR_VAR!r} must override the "
            f"default, got:\n{rendered}",
        )
    except jinja2.TemplateError as exc:
        raise TemplateError(
            f"{rel}: Jinja2 could not render the template ({exc})"
        ) from exc
    return True


def check_keywords(schema: object, rel: str, where: str = "schema") -> None:
    """Rule 6: every key is a 2020-12 keyword (or `x-*`), with a value of the right type.

    Recurse into the schema-bearing keywords so a nested property cannot carry a
    keyword the rest of the gate would never see.
    """
    _require(isinstance(schema, dict), f"{rel}: {where} must be a JSON object")
    for key, value in schema.items():  # type: ignore[union-attr]
        if key.startswith("x-"):
            _require(
                isinstance(value, dict),
                f"{rel}: {where}.{key} must be an object (an `x-` extension may not "
                f"be a bare scalar)",
            )
            continue
        expected = _KEYWORD_TYPES.get(key)
        _require(
            expected is not None,
            f"{rel}: {where}.{key} is not a JSON Schema 2020-12 keyword and not an "
            f"`x-` extension — an unknown keyword is a rule nothing enforces",
        )
        # bool is an int subclass in Python; `minimum: true` is not a number.
        if isinstance(value, bool) and expected is not bool:
            _require(False, f"{rel}: {where}.{key} must not be a boolean")
        _require(
            isinstance(value, expected),  # type: ignore[arg-type]
            f"{rel}: {where}.{key} must be {getattr(expected, '__name__', expected)}, "
            f"got {type(value).__name__}",
        )
        if key in _SCHEMA_MAPS:
            for name, sub in value.items():  # type: ignore[union-attr]
                check_keywords(sub, rel, f"{where}.{key}[{name!r}]")
        elif key in _SCHEMA_SINGLE:
            check_keywords(value, rel, f"{where}.{key}")
        elif key in _SCHEMA_LISTS:
            for index, sub in enumerate(value):  # type: ignore[union-attr]
                check_keywords(sub, rel, f"{where}.{key}[{index}]")



def check_schema(
    schema_path: Path,
    data: object,
    template: Path,
    reads: set[str],
    root: Path,
) -> tuple[int, int]:
    """Check one schema against its template body; return (required, optional) counts."""
    rel = _rel(schema_path, root)
    _require(isinstance(data, dict), f"{rel}: a schema document must be a JSON object")
    schema: dict = data  # type: ignore[assignment]
    check_keywords(schema, rel)

    _require(
        isinstance(schema.get("schema_major"), int) and schema["schema_major"] >= 1,
        f"{rel}: missing an integer `schema_major` >= 1 (spine AD-12)",
    )
    _require(
        schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        f"{rel}: `$schema` must be the JSON Schema draft 2020-12 metaschema URI",
    )
    _require(
        schema.get("template") == template.name,
        f"{rel}: `template` must name the sibling {template.name!r}, got "
        f"{schema.get('template')!r}",
    )
    _require(
        schema.get("type") == "object",
        f"{rel}: `type` must be 'object' (the render context is a mapping)",
    )
    _require(
        schema.get("additionalProperties") is False,
        f"{rel}: `additionalProperties` must be false — a variable the template "
        f"does not consume is a consumer defect, not harmless extra data",
    )

    properties = schema.get("properties")
    _require(isinstance(properties, dict), f"{rel}: `properties` must be a mapping")
    for name, spec in properties.items():
        _require(
            isinstance(spec, dict) and isinstance(spec.get("type"), (str, list)),
            f"{rel}: property {name!r} has no `type` — the contract names a value "
            f"without saying what it is",
        )

    required = schema.get("required")
    optional = schema.get("optional")
    for key, value in (("required", required), ("optional", optional)):
        _require(
            isinstance(value, list) and all(isinstance(n, str) for n in value),
            f"{rel}: `{key}` must be a list of variable names",
        )
    assert isinstance(required, list) and isinstance(optional, list)

    required_set, optional_set = set(required), set(optional)
    _require(
        len(required_set) == len(required),
        f"{rel}: `required` lists a name twice",
    )
    _require(
        len(optional_set) == len(optional),
        f"{rel}: `optional` lists a name twice",
    )
    overlap = sorted(required_set & optional_set)
    _require(not overlap, f"{rel}: {overlap} appear in both `required` and `optional`")

    undeclared = sorted((required_set | optional_set) - set(properties))
    _require(
        not undeclared,
        f"{rel}: {undeclared} are declared but have no `properties` entry (no type)",
    )
    partitioned = required_set | optional_set
    unclassified = sorted(set(properties) - partitioned)
    _require(
        not unclassified,
        f"{rel}: {unclassified} have a `properties` entry but appear in neither "
        f"`required` nor `optional` — every consumed name must state which it is",
    )

    # Rule 3: the contract equals the body.
    missing = sorted(reads - set(properties))
    _require(
        not missing,
        f"{rel}: the template reads {missing}, which the schema does not declare",
    )
    invented = sorted(set(properties) - reads)
    _require(
        not invented,
        f"{rel}: the schema declares {invented}, which the template never reads — "
        f"`required` must be derived from the template body, not the consumer's "
        f"variable set",
    )

    # Rule 5: a template that reads something requires something.
    if reads:
        _require(
            bool(required_set),
            f"{rel}: the template reads {sorted(reads)} but `required` is empty — "
            f"a contract that constrains nothing",
        )

    # Rule 4: no `default(` on a required var.
    for match in EXPRESSION.finditer(template.read_text()):
        expression = match.group("expr") or match.group("stmt") or ""
        if not DEFAULT_CALL.search(expression):
            continue
        cleaned = STRING_LITERAL.sub(" ", expression)
        mentioned = {
            ident.group(0)
            for ident in IDENTIFIER.finditer(cleaned)
            if ident.group(0) in required_set
        }
        if mentioned:
            raise TemplateError(
                f"{_rel(template, root)}: `default(` applied in an expression that "
                f"mentions required variable(s) {sorted(mentioned)} — a fallback on a "
                f"required var turns a missing value into a wrong one (spine AD-8.2)"
            )

    return len(required_set), len(optional_set)


def deep_check(schema_path: Path, data: dict, root: Path) -> bool:
    """Validate against the 2020-12 metaschema + a closed-world instance, if possible.

    Returns False when `jsonschema` is not importable. Never silently passes: the
    caller prints which mode ran.
    """
    try:
        import jsonschema
    except ImportError:
        return False
    rel = _rel(schema_path, root)
    try:
        validator_cls = jsonschema.validators.validator_for(data)
        validator_cls.check_schema(data)
        validator = validator_cls(data)
        # Closed world: an instance carrying an undeclared name must be rejected.
        assert not validator.is_valid({"__undeclared_name_probe__": "x"}), (
            f"{rel}: `additionalProperties: false` does not reject an undeclared name"
        )
        # And an instance missing a required name must be rejected.
        for name in data.get("required", []):
            probe = {n: "probe" for n in data.get("required", []) if n != name}
            assert not validator.is_valid(probe), (
                f"{rel}: `required` does not reject an instance missing {name!r}"
            )
    except AssertionError as exc:
        raise TemplateError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - jsonschema raises its own hierarchy
        raise TemplateError(f"{rel}: not a valid draft 2020-12 schema ({exc})") from exc
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the templates class contract")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    base = root / TEMPLATES_DIR
    if not base.is_dir():
        print(f"validate-templates: FAIL -- {TEMPLATES_DIR}/ is missing at {root}")
        return 1

    templates = sorted(
        p
        for p in base.rglob("*")
        if p.is_file() and p.suffix in TEMPLATE_SUFFIXES
    )
    schemas = sorted(p for p in base.rglob(f"*{SCHEMA_SUFFIX}") if p.is_file())

    errors: list[str] = []
    groups: dict[str, int] = {}
    required_total = 0
    optional_total = 0
    default_probe_count = 0
    sddm_seen = False
    sddm_render_probe = False

    template_set = set(templates)
    schema_set = set(schemas)

    # Rule 1a: every template has its sibling schema.
    for template in templates:
        want = expected_schema(template)
        if want not in schema_set:
            errors.append(
                f"{_rel(template, root)}: no sibling {want.name} — a template without "
                f"a vars schema is a value the consumer cannot check"
            )

    # Rule 1b + 2-5: every schema names a real sibling template and matches its body.
    for schema_path in schemas:
        rel = _rel(schema_path, root)
        try:
            data = json.loads(schema_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: a schema document must be a JSON object")
            continue
        declared = data.get("template")
        if not isinstance(declared, str) or not declared:
            errors.append(f"{rel}: missing the sibling `template` file name")
            continue
        template = schema_path.parent / declared
        if template not in template_set:
            errors.append(
                f"{rel}: `template` names {declared!r}, which is not a template in "
                f"{_rel(schema_path.parent, root)}/"
            )
            continue
        if expected_schema(template) != schema_path:
            errors.append(
                f"{rel}: is not the schema sibling of {declared!r} (expected "
                f"{expected_schema(template).name})"
            )
            continue
        reads = template_reads(template.read_text())
        try:
            required_n, optional_n = check_schema(schema_path, data, template, reads, root)
            deep_check(schema_path, data, root)
            if _rel(template, root) == SDDM_TEMPLATE:
                sddm_seen = True
                sddm_render_probe = check_sddm_wayland(
                    template, template.read_text(), data, root
                )
        except TemplateError as exc:
            errors.append(str(exc))
            continue
        required_total += required_n
        optional_total += optional_n
        if DEFAULT_CALL.search(template.read_text()):
            default_probe_count += 1
        group = template.parent.name
        groups[group] = groups.get(group, 0) + 1

    print(
        f"validate-templates: root={root} templates={len(templates)} "
        f"schemas={len(schemas)}"
    )
    print(
        "validate-templates: groups: "
        + (" ".join(f"{g}({n})" for g, n in sorted(groups.items())) or "(none)")
    )
    print(
        f"validate-templates: vars: required={required_total} optional={optional_total} "
        f"(properties == reads on every template)"
    )
    print(
        f"validate-templates: templates containing `default(`: {default_probe_count}; "
        f"defaults on required vars: 0 (rule enforced)"
    )
    if not sddm_seen:
        errors.append(
            f"{SDDM_TEMPLATE}: missing -- the SDDM Wayland greeter contract "
            f"cannot be asserted without the template"
        )
    else:
        print(
            f"validate-templates: sddm: [Wayland] CompositorCommand present "
            f"(default={SDDM_COMPOSITOR_DEFAULT!r}; optional override asserted)"
        )
        if sddm_render_probe:
            print(
                "validate-templates: sddm deep: renders with the required variable "
                "only and with the optional override"
            )
        else:
            print(
                "validate-templates: NOTE -- the sddm render probe did not run "
                "(jinja2 is not installed or the probe failed); the static "
                "section/default assertion still ran"
            )
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print(
            "validate-templates: NOTE -- jsonschema is not installed; the draft "
            "2020-12 metaschema and closed-world instance checks were skipped "
            "(the envelope, pairing and body-equality rules above still ran)"
        )
    else:
        print(
            "validate-templates: deep: every schema validates against the draft "
            "2020-12 metaschema and rejects an undeclared / required-missing instance"
        )

    if errors:
        print(f"validate-templates: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("validate-templates: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
