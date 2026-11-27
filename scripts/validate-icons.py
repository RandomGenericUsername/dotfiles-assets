#!/usr/bin/env python3
"""validate-icons -- the icons corpus: mappings resolve, tokens are typed, SVGs parse.

WHAT THIS GATE PROVES, and why each part is separate (schema_major 2, REQ-149):

  1. EVERY MAPPING TEMPLATE RESOLVES. Each `variants[].template` in the ONE
     group-map file (`icons/mappings/icons.yaml`) names a real file under
     `icons/templates/`, joined EXACTLY as the consumer joins it: relative to the
     group's template root (`templates/<template_dir>`, default `.`), not to the
     mapping file's directory. A stale entry here is otherwise discovered at render
     time on a user's machine, never at release time. Several variants MAY share
     one template -- that is the canonical-art collapse (one drawing, params per
     row), not a missing file.

  2. EVERY PLACEHOLDER IS DECLARED, AND TYPED. Each token used by a template the
     mapping renders must be declared for that group: in `mappings/defaults.yaml`
     (the group-independent COLOR_* vocabulary) or in that group's
     `color_mappings` / variant `color_mappings`. This mirrors the consumer's merge
     order (defaults < group < variant). Only two families exist:

       - `{{COLOR_*}}` -> a role declared in `mappings/vocabulary.json`, or a
         `#rrggbb` literal;
       - `{{OPACITY_*}}` -> a numeric literal in [0, 1].

     Any other token name is invalid, and a value outside its family's value space
     (a role as an opacity, a number as a colour) is an error, not a typo.

  3. EVERY SVG IS WELL-FORMED XML. A malformed template fails the tag here, not
     in a renderer.

  4. THE SHAPE RULES THE CONTRACT STATES. `variants[].name` is unique inside its
     group; `output` is a bare file name (no path separators, no `..`, no
     placeholder); a `template` may not escape the templates root. A group
     declares its default `surface`, the surfaces it `serves`, and the `styles`
     axis; a styled group's rows each declare a `style`, `(state, style)` is
     unique, and `bar_mappings.states` values name live variants.

  5. THE SURFACE-INK CONTRACT. For every surface a row renders on: wallpaper ink
     must be `on_backdrop`; dark-glass/solid ink must be in the on-surface family
     when the row does not pin it (a pin is a genuine tint). This is the rule that
     retires the `system-*` duplicate rows: one row renders per surface.

  6. ONE MANIFEST, ONE VOCABULARY. `icons/mappings/` holds exactly `icons.yaml`
     (the group map) and `defaults.yaml` (the COLOR_* vocabulary). A second
     `*.yaml` there is a contract violation: the consumer loads ONE mapping file,
     so a per-group split is a second source of truth that drifts by construction.

  7. EVERY COLOR VALUE IS A DECLARED ROLE (or a `#rrggbb` literal). Legacy `colorN`
     carrier indices and producer aliases (`foreground`, `accent`, `accent-muted`,
     `warning`) are rejected. The single exception is `phase_a_legacy_baseline` in
     `vocabulary.json`: an exact, shrink-only list of pins a role migration has not
     converted yet. An entry that no longer matches a live pin fails.

  8. SCHEMA AND CHECKER MOVE TOGETHER. This validator implements `schema_major 2`
     and asserts the contract file says 2 (and repeats the same token patterns).
     Raising the version without teaching the checker is the failure this rule
     exists to prevent.

WHAT IT REPORTS WITHOUT FAILING: a token declared for one group and unused there
(forward compatibility), a template no variant references, and a `(state, style)`
grid cell a styled group does not draw (the consumer blanks loudly instead of
inventing art).

WHY NO PyYAML. A fresh clone must pass `make gates` with no virtualenv and no
network. The mapping files use a deliberately small YAML subset: nested mappings,
sequences of mappings, `{}`, scalars and comments. Anything outside that subset
(flow collections other than `{}`, anchors, block scalars, tabs, inline nested
mappings) is a hard ERROR rather than a guess, so a future edit cannot silently
change what this gate checked.

Usage: ``python3 scripts/validate-icons.py [--root REPO_ROOT]``
Exit 0 = the icons corpus is shippable. Exit 1 = at least one violation, listed by path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCHEMA = "icons/schema.json"
MAPPINGS = "icons/mappings"
TEMPLATES = "icons/templates"
MANIFEST = "icons/mappings/icons.yaml"
DEFAULTS = "icons/mappings/defaults.yaml"
VOCABULARY = "icons/mappings/vocabulary.json"
PROPOSAL = "icons/mappings/ROLE-MIGRATION.md"
VOCABULARY_FILES = ("icons.yaml", "defaults.yaml")
SURFACES = ("wallpaper", "dark-glass", "solid")
EXPECTED_SCHEMA_MAJOR = 2
INK_TOKENS = ("COLOR_FOREGROUND", "COLOR_JOIN")
ROLE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")

TOKEN = re.compile(r"\{\{\s*([^{}]*?)\s*\}\}")
STRICT_TOKEN = re.compile(r"\{\{((?:COLOR|OPACITY)_[A-Z0-9_]+)\}\}")
COLOR_NAME = re.compile(r"^COLOR_[A-Z0-9_]+$")
OPACITY_NAME = re.compile(r"^OPACITY_[A-Z0-9_]+$")
HEX_LITERAL = re.compile(r"^#[0-9a-fA-F]{6}$")
# Exactly the numeric grammar the ITR substitution accepts, so a value this gate
# passes cannot be rejected by the renderer later.
NUMERIC_LITERAL = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
OUTPUT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
STYLE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
STATE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class CorpusError(Exception):
    """A violation, with the path/reason a reader needs to fix it."""


class YamlSubsetError(Exception):
    """A mapping file used YAML this parser deliberately refuses to guess at."""


def token_family(token: str) -> str | None:
    """Return "COLOR", "OPACITY", or None for a token name outside the grammar."""
    if COLOR_NAME.match(token):
        return "COLOR"
    if OPACITY_NAME.match(token):
        return "OPACITY"
    return None


def opacity_value(value: object) -> float | None:
    """Parse a YAML scalar as an OPACITY value in [0, 1]; None when invalid."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        text = str(value)
    elif isinstance(value, float):
        text = repr(value)
    elif isinstance(value, str):
        text = value
    else:
        return None
    if NUMERIC_LITERAL.match(text) is None:
        return None
    number = float(text)
    if 0.0 <= number <= 1.0:
        return number
    return None


def on_surface_family(role: object) -> bool:
    """The dark-glass/solid ink family: on_surface/on_*_container/on_primary/..."""
    return (
        isinstance(role, str)
        and role.startswith("on_")
        and role != "on_backdrop"
    )


def ink_satisfies(surface: str, value: object) -> bool:
    if surface == "wallpaper":
        return value == "on_backdrop"
    return on_surface_family(value)


# --------------------------------------------------------------------------- #
# The YAML subset (nested mappings + sequences of mappings, as the mappings use)
# --------------------------------------------------------------------------- #


def _scalar(text: str, source: str, lineno: int):
    if text == "":
        raise YamlSubsetError(f"{source}:{lineno}: empty value")
    if text[0] in "\"'":
        if len(text) < 2 or text[-1] != text[0]:
            raise YamlSubsetError(f"{source}:{lineno}: unterminated quoted scalar {text!r}")
        return text[1:-1]
    if text[0] in "[{":
        if text in ("[]", "{}"):
            return [] if text == "[]" else {}
        raise YamlSubsetError(
            f"{source}:{lineno}: flow collections other than `[]`/`{{}}` are not "
            f"supported ({text!r})"
        )
    if text[0] in "|>&*!%@`":
        raise YamlSubsetError(
            f"{source}:{lineno}: block scalars / anchors / tags are not supported ({text!r})"
        )
    if text in ("null", "~"):
        return None
    if text in ("true", "false"):
        return text == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if ": " in text:
        raise YamlSubsetError(
            f"{source}:{lineno}: a nested mapping must be a block, not inline ({text!r})"
        )
    return text


def _mapping(lines, i, indent, source):
    out: dict[str, object] = {}
    while i < len(lines) and lines[i][0] == indent:
        text, lineno = lines[i][1], lines[i][2]
        if text.startswith("- "):
            raise YamlSubsetError(f"{source}:{lineno}: list item where a key was expected")
        key, sep, rest = text.partition(":")
        if not sep or not key.strip():
            raise YamlSubsetError(f"{source}:{lineno}: expected `key: value`, got {text!r}")
        key, rest = key.strip(), rest.strip()
        if key in out:
            raise YamlSubsetError(f"{source}:{lineno}: duplicate key {key!r}")
        i += 1
        if rest:
            out[key] = _scalar(rest, source, lineno)
            continue
        if i < len(lines) and lines[i][0] > indent:
            if lines[i][0] != indent + 2:
                raise YamlSubsetError(
                    f"{source}:{lines[i][2]}: expected exactly two spaces of indent "
                    f"under {key!r}, got {lines[i][0] - indent}"
                )
            out[key], i = _block(lines, i, indent + 2, source)
        else:
            raise YamlSubsetError(f"{source}:{lineno}: key {key!r} has no value")
    if i < len(lines) and lines[i][0] > indent:
        raise YamlSubsetError(f"{source}:{lines[i][2]}: unexpected indentation")
    return out, i


def _sequence(lines, i, indent, source):
    out: list[object] = []
    while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
        text, lineno = lines[i][1], lines[i][2]
        body = text[2:].strip()
        if not body:
            raise YamlSubsetError(f"{source}:{lineno}: empty list item")
        if body[0] in "\"'":
            # A quoted scalar item (a `styles`/`serves` entry).
            out.append(_scalar(body, source, lineno))
            i += 1
            continue
        key, sep, rest = body.partition(": ")
        if not sep:
            # A plain scalar item (a `styles`/`serves` entry), e.g. `- wallpaper`.
            out.append(_scalar(body, source, lineno))
            i += 1
            continue
        item: dict[str, object] = {}
        key, rest = key.strip(), rest.strip()
        if not key:
            raise YamlSubsetError(
                f"{source}:{lineno}: a sequence item must be `key: value` or a scalar; "
                f"got {text!r}"
            )
        i += 1
        if rest:
            item[key] = _scalar(rest, source, lineno)
        else:
            if i < len(lines) and lines[i][0] > indent:
                if lines[i][0] != indent + 2:
                    raise YamlSubsetError(
                        f"{source}:{lines[i][2]}: expected exactly two spaces of indent "
                        f"under {key!r}, got {lines[i][0] - indent}"
                    )
                item[key], i = _block(lines, i, indent + 2, source)
            else:
                raise YamlSubsetError(f"{source}:{lineno}: key {key!r} has no value")
        while i < len(lines) and lines[i][0] > indent:
            if lines[i][0] != indent + 2:
                raise YamlSubsetError(
                    f"{source}:{lines[i][2]}: a sequence item's keys must sit at "
                    f"{indent + 2} spaces"
                )
            continuation, i = _mapping(lines, i, indent + 2, source)
            for ckey, cvalue in continuation.items():
                if ckey in item:
                    raise YamlSubsetError(
                        f"{source}:{lines[i - 1][2]}: duplicate key {ckey!r} in a list item"
                    )
                item[ckey] = cvalue
        out.append(item)
    return out, i


def _block(lines, i, indent, source):
    if lines[i][1].startswith("- "):
        return _sequence(lines, i, indent, source)
    return _mapping(lines, i, indent, source)


def parse_yaml_subset(text: str, source: str) -> dict:
    lines: list[tuple[int, str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw:
            raise YamlSubsetError(f"{source}:{lineno}: tabs are not valid YAML indentation")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise YamlSubsetError(
                f"{source}:{lineno}: indentation must be a multiple of two spaces"
            )
        lines.append((indent, stripped, lineno))
    if not lines:
        raise YamlSubsetError(f"{source}: file is empty")
    if lines[0][0] != 0:
        raise YamlSubsetError(f"{source}:{lines[0][2]}: top level must not be indented")
    value, i = _block(lines, 0, 0, source)
    if i != len(lines):
        raise YamlSubsetError(f"{source}:{lines[i][2]}: trailing content")
    if not isinstance(value, dict):
        raise YamlSubsetError(f"{source}: top level must be a mapping")
    return value


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load_schema(root: Path, errors: list[str]) -> None:
    path = root / SCHEMA
    if not path.is_file():
        errors.append(f"{SCHEMA}: missing -- the icons contract is not optional")
        return
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"{SCHEMA}: invalid JSON ({exc})")
        return
    if not isinstance(data, dict):
        errors.append(f"{SCHEMA}: a schema document must be a JSON object")
        return
    major = data.get("schema_major")
    if not isinstance(major, int):
        errors.append(f"{SCHEMA}: missing an integer `schema_major` (spine AD-12)")
    elif major != EXPECTED_SCHEMA_MAJOR:
        errors.append(
            f"{SCHEMA}: `schema_major` is {major}; this validator implements "
            f"{EXPECTED_SCHEMA_MAJOR}. The schema and its checker are bumped in the "
            f"same commit -- teach the checker, then raise the contract (or fix one)"
        )
    paths = data.get("paths")
    if not isinstance(paths, dict):
        errors.append(f"{SCHEMA}: `paths` must be a mapping")
        return
    for key, expected in (
        ("templates_root", TEMPLATES),
        ("mappings_root", MAPPINGS),
        ("defaults", DEFAULTS),
        ("vocabulary", VOCABULARY),
        ("role_proposal", PROPOSAL),
    ):
        if paths.get(key) != expected:
            errors.append(
                f"{SCHEMA}: paths.{key} is {paths.get(key)!r}; this validator reads "
                f"{expected!r} -- keep the contract and the checker in step"
            )
    surfaces = data.get("surface_classes")
    if not isinstance(surfaces, dict):
        errors.append(f"{SCHEMA}: `surface_classes` must be a mapping (the surface enum)")
        return
    if tuple(surfaces.get("enum") or ()) != SURFACES:
        errors.append(
            f"{SCHEMA}: surface_classes.enum is {surfaces.get('enum')!r}; this validator "
            f"enforces {list(SURFACES)!r} -- keep the contract and the checker in step"
        )
    families = (data.get("token_families") or {}).get("families") or {}
    for name, pattern in (("COLOR", COLOR_NAME), ("OPACITY", OPACITY_NAME)):
        declared = (families.get(name) or {}).get("name_pattern")
        if declared != pattern.pattern:
            errors.append(
                f"{SCHEMA}: token_families.families.{name}.name_pattern is "
                f"{declared!r}; this validator enforces {pattern.pattern!r} -- keep the "
                f"contract and the checker in step"
            )


def load_vocabulary(
    root: Path, errors: list[str]
) -> tuple[set[str], list[dict[str, str]]]:
    """Load the declared role vocabulary and the Phase A legacy baseline."""
    path = root / VOCABULARY
    if not path.is_file():
        errors.append(f"{VOCABULARY}: missing -- mapping values have no role authority")
        return set(), []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"{VOCABULARY}: invalid JSON ({exc})")
        return set(), []
    if not isinstance(data, dict):
        errors.append(f"{VOCABULARY}: a vocabulary document must be a JSON object")
        return set(), []
    if not isinstance(data.get("vocabulary"), int):
        errors.append(f"{VOCABULARY}: missing an integer `vocabulary` version")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append(f"{VOCABULARY}: `source` must be a mapping naming the producer/requirement")
        source = {}
    for key in ("producer", "requirement", "target_release"):
        if not isinstance(source.get(key), str) or not source.get(key):
            errors.append(f"{VOCABULARY}: source.{key} must be a non-empty string")

    roles = data.get("roles")
    if not isinstance(roles, list) or not roles:
        errors.append(f"{VOCABULARY}: `roles` must be a non-empty list of role names")
        roles = []
    role_set: set[str] = set()
    for role in roles:
        if not isinstance(role, str) or not ROLE_NAME.match(role):
            errors.append(f"{VOCABULARY}: {role!r} is not a snake_case role name")
            continue
        if role in role_set:
            errors.append(f"{VOCABULARY}: role {role!r} is declared twice")
        role_set.add(role)
    if len(role_set) != 51:
        errors.append(
            f"{VOCABULARY}: {len(role_set)} role(s) declared; expected 51 (50 Material "
            f"roles + `on_backdrop`, theme-producer REQ-022)"
        )
    if "on_backdrop" not in role_set:
        errors.append(f"{VOCABULARY}: `on_backdrop` (the produced wallpaper-ink role) is missing")

    aliases = source.get("aliases_are_not_roles")
    if isinstance(aliases, dict):
        for alias in aliases.get("not_roles") or []:
            if alias in role_set:
                errors.append(
                    f"{VOCABULARY}: {alias!r} is listed as an alias but declared as a role; "
                    f"an alias hides which pole it resolves to"
                )

    surfaces = data.get("surface_classes")
    if not isinstance(surfaces, dict) or tuple(surfaces.get("enum") or ()) != SURFACES:
        errors.append(
            f"{VOCABULARY}: surface_classes.enum must be exactly {list(SURFACES)!r}"
        )

    baseline_raw = data.get("phase_a_legacy_baseline")
    if not isinstance(baseline_raw, dict):
        errors.append(
            f"{VOCABULARY}: `phase_a_legacy_baseline` must be a mapping (use an empty "
            f"`entries` list when the migration is complete)"
        )
        return role_set, []
    entries = baseline_raw.get("entries")
    if not isinstance(entries, list):
        errors.append(f"{VOCABULARY}: phase_a_legacy_baseline.entries must be a list")
        return role_set, []
    baseline: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, entry in enumerate(entries):
        where = f"{VOCABULARY}: phase_a_legacy_baseline.entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: an entry must be a mapping")
            continue
        scope, token, value = entry.get("scope"), entry.get("token"), entry.get("value")
        if not isinstance(scope, str) or not scope:
            errors.append(f"{where}: missing `scope` (\"defaults\", a group, or group/variant)")
            continue
        if not isinstance(token, str) or not COLOR_NAME.match(token):
            errors.append(f"{where}: `token` must be a COLOR_* name")
            continue
        if not isinstance(value, str) or not value:
            errors.append(f"{where}: `value` must be the non-role value the pin carries")
            continue
        if value in role_set:
            errors.append(
                f"{where}: {value!r} is a declared role, so it needs no baseline exemption"
            )
        key = (scope, token, value)
        if key in seen:
            errors.append(f"{where}: duplicate baseline entry {key}")
        seen.add(key)
        baseline.append({"scope": scope, "token": token, "value": value})
    return role_set, baseline


def load_defaults(root: Path, errors: list[str]) -> dict[str, object]:
    path = root / DEFAULTS
    if not path.is_file():
        errors.append(f"{DEFAULTS}: missing -- the group-independent vocabulary is required")
        return {}
    try:
        data = parse_yaml_subset(path.read_text(), DEFAULTS)
    except YamlSubsetError as exc:
        errors.append(str(exc))
        return {}
    defaults = data.get("defaults")
    if not isinstance(defaults, dict) or not defaults:
        errors.append(f"{DEFAULTS}: `defaults` must be a non-empty mapping")
        return {}
    for name, value in defaults.items():
        if not COLOR_NAME.match(str(name)):
            errors.append(
                f"{DEFAULTS}: {name!r} is not a COLOR_* token name -- the vocabulary "
                f"defaults are colour roles; an OPACITY_* param belongs to a group or "
                f"a variant row"
            )
        if not isinstance(value, str) or not value:
            errors.append(f"{DEFAULTS}: {name!r} must map to a non-empty palette role")
    return defaults


def _check_token_value(
    scope: str,
    where: str,
    token: str,
    value: object,
    roles: set[str],
    baseline_keys: set[tuple[str, str, str]],
    used_baseline: set[tuple[str, str, str]],
    errors: list[str],
) -> None:
    """One mapping value must satisfy the value space of its token's family."""
    family = token_family(token)
    if family == "OPACITY":
        if opacity_value(value) is None:
            errors.append(
                f"{where}: {token!r} must be a numeric literal in [0, 1], got {value!r} "
                f"-- an opacity is not a role"
            )
        return
    if not isinstance(value, str) or not value:
        errors.append(
            f"{where}: {token!r} must map to a non-empty palette role or a #rrggbb "
            f"literal, got {value!r} -- a colour is not a number"
        )
        return
    if HEX_LITERAL.match(value):
        return
    if NUMERIC_LITERAL.match(value):
        errors.append(
            f"{where}: {token!r} maps to the number {value!r} -- a colour is not a "
            f"number; use a role or a #rrggbb literal"
        )
        return
    if value in roles:
        return
    key = (scope, token, value)
    if key in baseline_keys:
        used_baseline.add(key)
        return
    hint = ""
    if re.fullmatch(r"color\d+", value):
        hint = (
            " -- `colorN` is the legacy positional carrier list; its meaning changed "
            "under the current producer, so it is not a role"
        )
    errors.append(
        f"{where}: {token!r} maps to {value!r}, which is not a declared role in "
        f"{VOCABULARY}, not a #rrggbb literal, and not an exact "
        f"`phase_a_legacy_baseline` entry{hint}. Use a semantic role "
        f"(on_backdrop / on_surface / primary / tertiary / error, ...)"
    )


def _check_token_map(
    scope: str,
    where: str,
    value: object,
    roles: set[str],
    baseline_keys: set[tuple[str, str, str]],
    used_baseline: set[tuple[str, str, str]],
    errors: list[str],
) -> dict[str, object]:
    """Validate a token map; return the declared names mapped to their values."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(f"{where}: `color_mappings` must be a mapping")
        return {}
    declared: dict[str, object] = {}
    for name, raw in value.items():
        name = str(name)
        if token_family(name) is None:
            errors.append(
                f"{where}: {name!r} is not a token name -- the grammar is "
                f"`COLOR_[A-Z0-9_]+` or `OPACITY_[A-Z0-9_]+`"
            )
            continue
        _check_token_value(
            scope, where, name, raw, roles, baseline_keys, used_baseline, errors
        )
        declared[name] = raw
    return declared


def check_mappings(
    root: Path,
    defaults: dict[str, object],
    roles: set[str],
    baseline: list[dict[str, str]],
    errors: list[str],
    notes: list[str],
) -> dict[str, int]:
    """Check the one group map; return the counts this gate reports."""
    troot = root / TEMPLATES
    if not troot.is_dir():
        errors.append(f"{TEMPLATES}/: missing -- mappings cannot resolve against nothing")
        return {"files": 0, "groups": 0, "variants": 0}

    baseline_keys = {(e["scope"], e["token"], e["value"]) for e in baseline}
    used_baseline: set[tuple[str, str, str]] = set()

    # The vocabulary defaults are mapping values too: `accent` / `accent-muted`
    # were aliases whose names contradicted the pole they resolved to.
    for token, value in defaults.items():
        _check_token_value(
            "defaults",
            DEFAULTS,
            str(token),
            value,
            roles,
            baseline_keys,
            used_baseline,
            errors,
        )

    # ONE manifest + ONE vocabulary. A second group-map file is not a style
    # preference: the consumer loads one file, so a split is a second source of
    # truth that drifts (the six retired per-concern files proved it).
    mapping_dir = root / MAPPINGS
    present = sorted(p.name for p in mapping_dir.glob("*.y*ml") if p.is_file())
    unexpected = [name for name in present if name not in VOCABULARY_FILES]
    missing = [name for name in VOCABULARY_FILES if name not in present]
    if unexpected:
        errors.append(
            f"{MAPPINGS}/: unexpected mapping file(s) {unexpected} -- this class ships "
            f"exactly one group map ({MANIFEST}) plus the vocabulary ({DEFAULTS}). The "
            f"consumer loads ONE mapping file; a per-group split is a second source of "
            f"truth that drifts by construction"
        )
    if missing:
        errors.append(f"{MAPPINGS}/: missing required file(s) {missing}")
    manifest = root / MANIFEST
    if not manifest.is_file():
        return {"files": 0, "groups": 0, "variants": 0}

    rel = MANIFEST
    try:
        data = parse_yaml_subset(manifest.read_text(), rel)
    except YamlSubsetError as exc:
        errors.append(str(exc))
        return {"files": 1, "groups": 0, "variants": 0}

    # Every token declared anywhere, for the global SVG rule (a token used by a
    # template must be satisfiable by SOME group; the per-group rule below is the
    # stricter, consumer-accurate one).
    globally_declared: set[str] = set(defaults)
    referenced_paths: set[Path] = set()
    groups_count = variants_count = 0
    wallpaper_checked = 0
    surface_checked = 0
    style_cells_missing = 0

    for group_name, entry in data.items():
        group_name = str(group_name)
        if not isinstance(entry, dict):
            errors.append(f"{rel}: group {group_name!r} must be a mapping")
            continue
        groups_count += 1
        group_surface = entry.get("surface")
        if group_surface not in SURFACES:
            errors.append(
                f"{rel}:{group_name}: `surface` is {group_surface!r}; every group "
                f"declares one of {list(SURFACES)!r} (schema_major 2)"
            )
            group_surface = None
        serves_raw = entry.get("serves", [group_surface] if group_surface else [])
        serves: list[str] = []
        if not isinstance(serves_raw, list) or not serves_raw:
            errors.append(
                f"{rel}:{group_name}: `serves` must be a non-empty list of surfaces"
            )
            serves_raw = [group_surface] if group_surface else []
        for surface in serves_raw:
            if surface not in SURFACES:
                errors.append(
                    f"{rel}:{group_name}: `serves` holds {surface!r}; must be one of "
                    f"{list(SURFACES)!r}"
                )
                continue
            if surface in serves:
                errors.append(f"{rel}:{group_name}: `serves` lists {surface!r} twice")
                continue
            serves.append(surface)
        if group_surface and group_surface not in serves:
            errors.append(
                f"{rel}:{group_name}: `serves` {serves!r} does not contain the "
                f"group's default `surface` {group_surface!r}"
            )
        group_styles_raw = entry.get("styles")
        styles: list[str] = []
        if group_styles_raw is not None:
            if not isinstance(group_styles_raw, list) or not group_styles_raw:
                errors.append(
                    f"{rel}:{group_name}: `styles` must be a non-empty list when declared"
                )
            else:
                for style in group_styles_raw:
                    if not isinstance(style, str) or not STYLE_NAME.match(style):
                        errors.append(
                            f"{rel}:{group_name}: style {style!r} is not a "
                            f"lowercase name"
                        )
                        continue
                    if style in styles:
                        errors.append(
                            f"{rel}:{group_name}: style {style!r} is declared twice"
                        )
                        continue
                    styles.append(style)
        default_style = styles[0] if styles else "default"

        group_tokens = _check_token_map(
            f"{group_name}",
            f"{rel}:{group_name}",
            entry.get("color_mappings"),
            roles,
            baseline_keys,
            used_baseline,
            errors,
        )
        globally_declared |= set(group_tokens)
        declared = set(defaults) | set(group_tokens)

        # The group's own ink pin answers for its default surface. A group that
        # serves more surfaces derives the rest at render time; the row-level
        # check below covers every surface a row actually renders on.
        if group_surface is not None:
            for ink in INK_TOKENS:
                if ink not in declared:
                    continue
                resolved = group_tokens.get(ink, defaults.get(ink))
                surface_checked += 1
                if not ink_satisfies(group_surface, resolved):
                    expected = (
                        "on_backdrop"
                        if group_surface == "wallpaper"
                        else "a role in the on-surface family (on_*)"
                    )
                    errors.append(
                        f"{rel}:{group_name}: surface is {group_surface!r} but {ink} "
                        f"resolves to {resolved!r}; a {group_surface} glyph's ink must "
                        f"be {expected}"
                    )

        template_dir = entry.get("template_dir", ".")
        if not isinstance(template_dir, str) or not template_dir:
            errors.append(
                f"{rel}:{group_name}: `template_dir` must be a non-empty string "
                f"(default \".\")"
            )
            template_dir = "."
        base = troot / template_dir
        if Path(template_dir).is_absolute() or not _is_within(base, troot):
            errors.append(
                f"{rel}:{group_name}: `template_dir` {template_dir!r} escapes {TEMPLATES}/"
            )
            base = troot

        variants = entry.get("variants")
        if not isinstance(variants, list) or not variants:
            errors.append(f"{rel}:{group_name}: `variants` must be a non-empty list")
            continue
        names: set[str] = set()
        cells: set[tuple[str, str]] = set()
        states_seen: set[str] = set()
        variant_states: dict[str, str] = {}
        group_used: set[str] = set()
        for index, variant in enumerate(variants):
            where = f"{rel}:{group_name}[{index}]"
            if not isinstance(variant, dict):
                errors.append(f"{where}: a variant must be a mapping")
                continue
            variants_count += 1
            name = variant.get("name")
            template = variant.get("template")
            output = variant.get("output")
            if not isinstance(name, str) or not name:
                errors.append(f"{where}: missing `name`")
                name = f"#{index}"
            elif name in names:
                errors.append(f"{rel}:{group_name}: duplicate variant name {name!r}")
            names.add(str(name))

            state = variant.get("state", name)
            if not isinstance(state, str) or not STATE_NAME.match(state):
                errors.append(
                    f"{where} ({name}): `state` must be a lowercase state key, got "
                    f"{state!r}"
                )
                state = str(name)
            style = variant.get("style")
            if styles:
                if style is None:
                    errors.append(
                        f"{where} ({name}): group declares `styles` {styles!r}, so the "
                        f"variant must declare its `style`"
                    )
                    style = default_style
                elif style not in styles:
                    errors.append(
                        f"{where} ({name}): `style` {style!r} is not declared in the "
                        f"group's styles {styles!r}"
                    )
            elif style is not None:
                errors.append(
                    f"{where} ({name}): `style` is {style!r} but the group declares no "
                    f"`styles` axis"
                )
                style = None
            state = str(state)
            style = str(style) if style is not None else default_style
            if (state, style) in cells:
                errors.append(
                    f"{where} ({name}): the (state, style) cell "
                    f"({state!r}, {style!r}) is already drawn by another variant"
                )
            cells.add((state, style))
            variant_states[str(name)] = state
            states_seen.add(state)

            variant_surface = variant.get("surface")
            if variant_surface is not None:
                if variant_surface not in SURFACES:
                    errors.append(
                        f"{where} ({name}): `surface` is {variant_surface!r}; must be "
                        f"one of {list(SURFACES)!r}"
                    )
                    variant_surface = None
                elif variant_surface not in serves:
                    errors.append(
                        f"{where} ({name}): `surface` {variant_surface!r} is not in the "
                        f"group's `serves` {serves!r} -- declare the surface dimension "
                        f"on the group instead of a name-convention row"
                    )
            surface = variant_surface or group_surface

            variant_tokens = _check_token_map(
                f"{group_name}/{name}",
                f"{where} ({name})",
                variant.get("color_mappings"),
                roles,
                baseline_keys,
                used_baseline,
                errors,
            )
            globally_declared |= set(variant_tokens)
            allowed = declared | set(variant_tokens)

            # A pin that restates what the row already inherits is dead data: the
            # schema_major 2 contract keeps variant pins for genuine tints and
            # params only.
            for token, value in variant_tokens.items():
                inherited = group_tokens.get(token, defaults.get(token))
                if token in group_tokens or token in defaults:
                    if value == inherited:
                        errors.append(
                            f"{where} ({name}): {token!r} pins {value!r}, which is what "
                            f"the row already inherits -- a variant pin is reserved for "
                            f"a genuine tint or param; delete the redundant pin"
                        )

            # The surface-ink contract for the surface this row renders on. A
            # variant-level ink pin is an explicit tint and is not re-derived.
            if surface is not None:
                for ink in INK_TOKENS:
                    if ink not in allowed:
                        continue
                    if ink in variant_tokens:
                        continue
                    resolved = group_tokens.get(ink, defaults.get(ink))
                    surface_checked += 1
                    if surface == "wallpaper":
                        wallpaper_checked += 1
                    if not ink_satisfies(surface, resolved):
                        expected = (
                            "on_backdrop"
                            if surface == "wallpaper"
                            else "a role in the on-surface family (on_*)"
                        )
                        errors.append(
                            f"{where} ({name}): surface is {surface!r} but {ink} "
                            f"resolves to {resolved!r}; a {surface} glyph's ink must "
                            f"be {expected} (or an explicit variant tint)"
                        )

            if not isinstance(output, str) or not output:
                errors.append(f"{where} ({name}): missing `output`")
            elif not OUTPUT_NAME.match(output) or "{{" in output:
                errors.append(
                    f"{where} ({name}): `output` must be a bare file name "
                    f"(no path separators, no `..`, no placeholder), got {output!r}"
                )

            if not isinstance(template, str) or not template:
                errors.append(f"{where} ({name}): missing `template`")
                continue
            if template.startswith("/"):
                errors.append(
                    f"{where} ({name}): `template` must be relative to the group's "
                    f"template root, got the absolute path {template!r}"
                )
                continue
            template_path = base / template
            if not _is_within(template_path, troot):
                errors.append(
                    f"{where} ({name}): `template` {template!r} escapes {TEMPLATES}/"
                )
                continue
            if not _is_within(template_path, base):
                errors.append(
                    f"{where} ({name}): `template` {template!r} escapes the group's "
                    f"template_dir {template_dir!r}"
                )
                continue
            if not template_path.is_file():
                under = TEMPLATES if template_dir == "." else f"{TEMPLATES}/{template_dir}"
                errors.append(
                    f"{where} ({name}): `template` {template!r} does not resolve under "
                    f"{under}/"
                )
                continue

            referenced_paths.add(template_path.resolve())
            text = template_path.read_text()
            used: set[str] = set()
            for match in TOKEN.finditer(text):
                strict = STRICT_TOKEN.fullmatch(match.group(0))
                if strict is None:
                    errors.append(
                        f"{template_path.relative_to(root)}: malformed placeholder "
                        f"{match.group(0)!r} (syntax is exactly {{{{COLOR_NAME}}}} or "
                        f"{{{{OPACITY_NAME}}}})"
                    )
                    continue
                used.add(strict.group(1))
            for token in sorted(used - allowed):
                errors.append(
                    f"{template_path.relative_to(root)}: placeholder {token} is not "
                    f"declared for group {group_name!r} ({rel}) in {DEFAULTS} or its "
                    f"color_mappings"
                )
            group_used |= used

        # A token declared at group level that no template of the group reads is
        # forward compatibility, not a failure -- but it is reported, so a leftover
        # param from a retired row does not hide.
        unused_tokens = sorted(set(group_tokens) - group_used)
        if unused_tokens:
            notes.append(
                f"{group_name}: declared but unused by its templates: "
                + ", ".join(unused_tokens)
            )

        # The state -> variant table is fixed resolution data, not an editing
        # surface: every value must name a live variant, and a variant's declared
        # state must resolve through it.
        bar = entry.get("bar_mappings")
        states: dict[str, object] = {}
        if bar is not None:
            if not isinstance(bar, dict):
                errors.append(f"{rel}:{group_name}: `bar_mappings` must be a mapping")
            else:
                raw_states = bar.get("states")
                if raw_states is not None and not isinstance(raw_states, dict):
                    errors.append(
                        f"{rel}:{group_name}: `bar_mappings.states` must be a mapping"
                    )
                elif isinstance(raw_states, dict):
                    for key, value in raw_states.items():
                        key = str(key)
                        if key in ("true", "false", "on", "off", "yes", "no"):
                            errors.append(
                                f"{rel}:{group_name}: state key {key!r} is a YAML 1.1 "
                                f"boolean trap; use a prefixed key (e.g. `bluetooth-on`)"
                            )
                        if not isinstance(value, str) or value not in names:
                            errors.append(
                                f"{rel}:{group_name}: bar_mappings.states[{key!r}] is "
                                f"{value!r}, which names no variant in this group"
                            )
                            continue
                        states[key] = value
        if styles and states:
            for name, state in variant_states.items():
                style = next(
                    (s for (st, s) in cells if st == state and s == default_style),
                    default_style,
                )
                if state in states and states[state] != name:
                    target = states[state]
                    if variant_states.get(str(target)) != state:
                        errors.append(
                            f"{rel}:{group_name}: bar_mappings.states[{state!r}] -> "
                            f"{target!r}, whose declared state is "
                            f"{variant_states.get(str(target))!r}; a state must resolve "
                            f"to a row of that state"
                        )
            for state in sorted(states_seen):
                if state not in states:
                    errors.append(
                        f"{rel}:{group_name}: variants draw state {state!r} but "
                        f"`bar_mappings.states` has no entry for it"
                    )
        if styles:
            missing_cells = [
                (state, style)
                for state in sorted(states_seen)
                for style in styles
                if (state, style) not in cells
            ]
            style_cells_missing += len(missing_cells)
            if missing_cells:
                preview = ", ".join(
                    f"{state}@{style}" for state, style in missing_cells[:6]
                )
                notes.append(
                    f"{group_name}: {len(missing_cells)} (state, style) cell(s) not "
                    f"drawn: {preview}" + (" ..." if len(missing_cells) > 6 else "")
                )

    # Global rule + XML well-formedness for EVERY template, referenced or not.
    all_svgs = sorted(troot.rglob("*.svg"))
    for svg in all_svgs:
        svg_rel = svg.relative_to(root).as_posix()
        try:
            ET.parse(svg)
        except ET.ParseError as exc:
            errors.append(f"{svg_rel}: not well-formed XML ({exc})")
            continue
        text = svg.read_text()
        for match in TOKEN.finditer(text):
            strict = STRICT_TOKEN.fullmatch(match.group(0))
            if strict is None:
                continue  # reported through the per-group scan when referenced
            body = strict.group(1)
            if body not in globally_declared:
                errors.append(
                    f"{svg_rel}: placeholder {body} is declared in neither {DEFAULTS} "
                    f"nor any group's color_mappings"
                )
    unreferenced = [
        p.relative_to(root).as_posix()
        for p in all_svgs
        if p.resolve() not in referenced_paths
    ]
    if unreferenced:
        notes.append(
            f"{len(unreferenced)} template(s) referenced by no variant: "
            + ", ".join(unreferenced[:5])
            + (" ..." if len(unreferenced) > 5 else "")
        )

    # The Phase A baseline is a ratchet: an entry that no longer matches a live
    # pin means the pin was migrated and the exemption must go with it. Without
    # this, Phase B could "finish" while the list still vouched for values that
    # are no longer in the corpus -- and the next `colorN` pin would be legal.
    for entry in baseline:
        key = (entry["scope"], entry["token"], entry["value"])
        if key not in used_baseline:
            errors.append(
                f"{VOCABULARY}: `phase_a_legacy_baseline` entry {key} matches no live "
                f"pin -- the baseline is shrink-only; delete the migrated entry"
            )
    if baseline:
        notes.append(
            f"{len(baseline)} pin(s) still carry a pre-migration value (Phase A legacy "
            f"baseline); Phase B drives this to 0"
        )
    if wallpaper_checked:
        notes.append(
            f"{wallpaper_checked} row(s) render on `wallpaper` and were held to "
            f"`on_backdrop` ink"
        )
    if surface_checked:
        notes.append(
            f"{surface_checked} surface-ink check(s) passed (wallpaper -> on_backdrop, "
            f"dark-glass/solid -> on-surface family)"
        )
    if style_cells_missing:
        notes.append(
            f"{style_cells_missing} (state, style) grid cell(s) are not drawn; a "
            f"consumer selecting one blanks loudly instead of inventing art"
        )

    # The reviewed proposal must name every group and variant: new art cannot land
    # without the page that says which role and which surface it is for.
    proposal = root / PROPOSAL
    if not proposal.is_file():
        errors.append(
            f"{PROPOSAL}: missing -- the role proposal is the reviewed record for "
            f"every group and variant"
        )
    else:
        text = proposal.read_text()
        missing_doc: list[str] = []
        for group_name in data:
            if f"`{group_name}`" not in text:
                missing_doc.append(f"group `{group_name}`")
            entry = data[group_name]
            if isinstance(entry, dict) and isinstance(entry.get("variants"), list):
                for variant in entry["variants"]:
                    if isinstance(variant, dict) and isinstance(variant.get("name"), str):
                        if f"`{variant['name']}`" not in text:
                            missing_doc.append(f"{group_name}/`{variant['name']}`")
        if missing_doc:
            errors.append(
                f"{PROPOSAL}: {len(missing_doc)} group/variant name(s) in {rel} are "
                f"missing from the proposal: " + ", ".join(missing_doc[:8])
                + (" ..." if len(missing_doc) > 8 else "")
            )

    return {
        "files": 1,
        "groups": groups_count,
        "variants": variants_count,
        "svgs": len(all_svgs),
        "baseline_remaining": len(baseline),
        "roles": len(roles),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the icons corpus")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent

    errors: list[str] = []
    notes: list[str] = []
    load_schema(root, errors)
    roles, baseline = load_vocabulary(root, errors)
    defaults = load_defaults(root, errors)
    counts = check_mappings(root, defaults, roles, baseline, errors, notes)

    print(
        f"validate-icons: root={root} manifest={MANIFEST} "
        f"schema_major={EXPECTED_SCHEMA_MAJOR} "
        f"groups={counts.get('groups', 0)} variants={counts.get('variants', 0)} "
        f"svgs={counts.get('svgs', 0)} defaults={len(defaults)} "
        f"roles={counts.get('roles', 0)} "
        f"legacy_baseline={counts.get('baseline_remaining', 0)}"
    )
    for note in notes:
        print(f"validate-icons: note: {note}")
    if errors:
        print(f"validate-icons: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        "validate-icons: PASS -- one group map (" + MANIFEST + "), every template "
        f"resolves under {TEMPLATES}/, every COLOR_*/OPACITY_* token is declared and "
        f"typed, every surface a row renders on satisfies the ink contract, styles/"
        f"state are consistent, the proposal names every group and variant, every SVG "
        f"parses"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
