#!/usr/bin/env python3
"""validate-skins -- the `skins` class contract, asserted against the corpus.

WHAT THIS GATE PROVES (Appearance token model v2, contracts v0.7.0):

  1. THE LOCAL CONTRACT IS HONEST. `skins/schema.json` carries
     `schema_major: 2`, names the canonical `contracts` paths and proves its
     vendored claim: every file under `skins/contracts/` is a byte copy whose
     sha256 matches `skins/contracts/PIN`. The three appearance schemas are the
     delegates (`appearance-manifest`, `appearance-json`,
     `appearance-artifact`); the frozen v1 skin schemas are pinned at the same
     tag for provenance. The 51-role palette list is `palette.v1`, checked
     against `icons/mappings/vocabulary.json`.

  2. EVERY MANIFEST IS A V2 APPEARANCE MANIFEST. The required manifests exist
     (currently `glass`, `flat`, `paper` and `terminal`), no extra manifest hides
     beside them, `name` equals the file stem,
     and the document validates against the vendored `appearance-manifest`
     schema (nested `surface`, `state`, `type`, `ink`, `layout.<app>` and
     optional `mode.dark`/`mode.light` overrides). A `structure`, `variant`,
     `transition` or `animation` property fails; layout keys must be namespaced
     app names with numeric values.

  3. EVERY MODE RESOLVES TO A VALID tokens.json. For each manifest the gate
     resolves the base groups plus the selected `mode.dark`/`mode.light`
     override (a provided group replaces the base group as a whole) and
     validates the result against the vendored `appearance-json` schema. The
     resolved document is `version: 2` plus the five fully resolved groups.

  4. PLACEHOLDER COVERAGE IS TWO-WAY AND THE UNIT RULE HOLDS. Every
     `{{SKIN_*}}` in a template is the flattened path of a v2 token
     (`surface.panel.bg` -> `SKIN_SURFACE_PANEL_BG`), every template expands
     for every manifest × mode, no placeholder is left unresolved, and a
     layout token (`SKIN_LAYOUT_*`) in CSS is an error. Numeric lengths render
     as `<n>px`, letter-spacing as `<n>em`, font-weight stays unitless; paints
     and strings render verbatim.

  5. THE TEMPLATE SET NAMES ITS TARGETS. The contract freezes one template per
     target config directory, named `<configDir>.gtk.css.j2`; the expander
     renders `<configDir>.css`. Every file in `skins/templates/` must match
     `^[a-z0-9][a-z0-9_-]*\\.gtk\\.css\\.j2$`, and the target reported in the
     summary is the prefix before `.gtk.css.j2`.

WHY STDLIB ONLY. A fresh clone must pass `make gates` with no virtualenv and no
network. The manifest format is TOML (`tomllib`, Python >= 3.11), the contract is
JSON, and the mini-validator below covers the exact JSON-Schema subset the
vendored canonical definitions use (`$ref`, `const`, `enum`, `type`, `minimum`,
`exclusiveMinimum`, `maximum`, `pattern`, `minLength`, `minProperties`,
`required`, `properties`, `patternProperties`, `additionalProperties`,
`propertyNames`, `allOf`/`anyOf`/`oneOf`/`not`). The fixture suite under
`skins/tests/` mirrors each negative case; `jsonschema`/`pytest` are NOT
required for this gate.

Usage: ``python3 scripts/validate-skins.py [--root REPO_ROOT]``
Exit 0 = all manifests, modes, templates and their coverage agree with v2.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import posixpath
import re
import sys
import tomllib
from pathlib import Path

SKINS_DIR = "skins"
SCHEMA = "skins/schema.json"
MANIFESTS_DIR = "skins/manifests"
TEMPLATES_DIR = "skins/templates"
VOCABULARY = "icons/mappings/vocabulary.json"

CONTRACTS_DIR = "skins/contracts"
PIN = "skins/contracts/PIN"
VENDORED = {
    "appearance-manifest": "skins/contracts/appearance-manifest.schema.json",
    "appearance-json": "skins/contracts/appearance-json.schema.json",
    "appearance-artifact": "skins/contracts/appearance-artifact.schema.json",
    "skin-token": "skins/contracts/skin-token.schema.json",
    "skin-manifest": "skins/contracts/skin-manifest.schema.json",
    "skin-json": "skins/contracts/skin-json.schema.json",
}
DELEGATES = {
    "manifest": VENDORED["appearance-manifest"],
    "json": VENDORED["appearance-json"],
    "artifact": VENDORED["appearance-artifact"],
}
LEGACY = {
    VENDORED["skin-token"],
    VENDORED["skin-manifest"],
    VENDORED["skin-json"],
}
VENDORED_FILES = {posixpath.basename(rel): rel for rel in VENDORED.values()}
CANONICAL_PATHS = {
    "schemas/appearance-manifest.schema.json",
    "schemas/appearance-json.schema.json",
    "schemas/appearance-artifact.schema.json",
    "schemas/skin-token.schema.json",
    "schemas/skin-manifest.schema.json",
    "schemas/skin-json.schema.json",
}
PIN_HASH = re.compile(r"^sha256\s+([0-9a-f]{64})\s+(\S+)$")
SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
#: `<configDir>.gtk.css.j2`; the target config directory is the prefix.
TEMPLATE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*\.gtk\.css\.j2$")
TEMPLATE_SUFFIX = ".gtk.css.j2"

HEX_LITERAL = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
STRUCTURE_PROPERTY = re.compile(r"\b(?:structure|variant|variants|transition|animation)\s*:")
PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
SKIN_PLACEHOLDER = re.compile(r"^SKIN_[A-Z0-9_]+$")
ROLE_REFERENCE = re.compile(r"@([a-z][a-z0-9_]*)")
GROUPS = ("surface", "state", "type", "ink", "layout")
CSS_GROUPS = ("surface", "state", "type", "ink")
MODES = ("dark", "light")
FORBIDDEN_TOP_KEYS = {
    "structure",
    "variant",
    "variants",
    "transition",
    "animation",
    "density",
    "paint",
}

#: Patterns every manifest and template is scanned for, in addition to the
#: schema's own `frozen.forbidden_patterns`. They are the frozen spec's hard
#: bans, not a style preference: GTK 4.24 ignores transitions.
HARD_FORBIDDEN = {
    "literal hex colour": HEX_LITERAL,
    "CSS transition": re.compile(r"\btransition\s*:"),
    "CSS animation": re.compile(r"\banimation\s*:"),
    "structure/variant property": STRUCTURE_PROPERTY,
}


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _compile(pattern: str, where: str, errors: list[str]) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern)
    except re.error as exc:
        errors.append(f"{where}: invalid regex {pattern!r} ({exc})")
        return None


def _pointer(document, fragment: str, where: str, errors: list[str]):
    """Resolve a JSON Pointer fragment (`#/definitions/x`) inside a document."""
    pointer = fragment[1:] if fragment.startswith("#") else fragment
    if pointer in ("", "/"):
        return document
    if not pointer.startswith("/"):
        errors.append(f"{where}: unsupported $ref fragment {fragment!r}")
        return None
    node = document
    for raw in pointer.lstrip("/").split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and key in node:
            node = node[key]
        elif isinstance(node, list) and key.isdigit() and int(key) < len(node):
            node = node[int(key)]
        else:
            errors.append(f"{where}: unresolved $ref fragment {fragment!r}")
            return None
    return node


def _deref(
    spec,
    root: Path,
    current_rel: str,
    where: str,
    errors: list[str],
    stack: tuple[tuple[str, str], ...] = (),
):
    """Inline every `$ref` (local or external) so value checks need no resolver."""
    if isinstance(spec, list):
        return [
            _deref(item, root, current_rel, where, errors, stack) for item in spec
        ]
    if not isinstance(spec, dict):
        return spec
    if "$ref" not in spec:
        return {
            key: _deref(value, root, current_rel, where, errors, stack)
            for key, value in spec.items()
        }
    ref = spec["$ref"]
    if not isinstance(ref, str):
        errors.append(f"{where}: $ref must be a string, got {ref!r}")
        return {}
    file_part, _, fragment = ref.partition("#")
    target_rel = current_rel
    if file_part:
        target_rel = posixpath.normpath(
            posixpath.join(posixpath.dirname(current_rel), file_part)
        )
    target_path = root / target_rel
    try:
        document = json.loads(target_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{where}: cannot load $ref {ref!r} ({exc})")
        return {}
    target = _pointer(document, "#" + fragment, where, errors)
    key = (target_rel, fragment)
    if key in stack:
        errors.append(f"{where}: cyclic $ref {ref!r}")
        return {}
    resolved = _deref(target, root, target_rel, where, errors, stack + (key,))
    siblings = {k: v for k, v in spec.items() if k != "$ref"}
    if siblings:
        sibling_spec = _deref(siblings, root, current_rel, where, errors, stack)
        return {"allOf": [resolved, sibling_spec]}
    return resolved


def _matches_type(value, wanted: str) -> bool:
    if wanted == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if wanted == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if wanted == "string":
        return isinstance(value, str)
    if wanted == "object":
        return isinstance(value, dict)
    if wanted == "array":
        return isinstance(value, list)
    if wanted == "boolean":
        return isinstance(value, bool)
    if wanted == "null":
        return value is None
    return True


def _value_messages(spec: dict, value) -> list[str]:
    """Validate the JSON-Schema subset the vendored canonical set declares."""
    if not isinstance(spec, dict):
        return []
    messages: list[str] = []
    if "const" in spec and value != spec["const"]:
        messages.append(f"must be {spec['const']!r}, got {value!r}")
    if "enum" in spec and value not in spec["enum"]:
        messages.append(f"must be one of {spec['enum']!r}, got {value!r}")
    if "type" in spec:
        wanted = spec["type"]
        wanted_types = wanted if isinstance(wanted, list) else [wanted]
        if not any(_matches_type(value, item) for item in wanted_types):
            label = " or ".join(str(item) for item in wanted_types)
            messages.append(
                f"must be a {label}, got {type(value).__name__} ({value!r})"
            )
            return messages
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = spec.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            messages.append(f"must be >= {minimum}, got {value!r}")
        exclusive_minimum = spec.get("exclusiveMinimum")
        if isinstance(exclusive_minimum, (int, float)) and value <= exclusive_minimum:
            messages.append(f"must be > {exclusive_minimum}, got {value!r}")
        maximum = spec.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            messages.append(f"must be <= {maximum}, got {value!r}")
        exclusive_maximum = spec.get("exclusiveMaximum")
        if isinstance(exclusive_maximum, (int, float)) and value >= exclusive_maximum:
            messages.append(f"must be < {exclusive_maximum}, got {value!r}")
    if isinstance(value, str):
        min_length = spec.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            messages.append(f"must be at least {min_length} character(s)")
        pattern = spec.get("pattern")
        if isinstance(pattern, str):
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                messages.append(f"invalid schema pattern {pattern!r} ({exc})")
            else:
                if not compiled.search(value):
                    messages.append(f"{value!r} does not match {pattern}")
    if isinstance(value, dict):
        required = spec.get("required")
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    messages.append(f"missing required property {key!r}")
        properties = spec.get("properties") if isinstance(spec.get("properties"), dict) else {}
        pattern_properties = (
            spec.get("patternProperties")
            if isinstance(spec.get("patternProperties"), dict)
            else {}
        )
        additional = spec.get("additionalProperties", None)
        for key, item in value.items():
            matched = False
            if key in properties:
                matched = True
                messages.extend(_value_messages(properties[key], item))
            for pattern, sub in pattern_properties.items():
                try:
                    matches = re.search(pattern, key)
                except re.error as exc:
                    messages.append(f"invalid patternProperties regex {pattern!r} ({exc})")
                    continue
                if matches:
                    matched = True
                    messages.extend(_value_messages(sub, item))
            if not matched:
                if additional is False:
                    messages.append(f"unexpected property {key!r}")
                elif isinstance(additional, dict):
                    messages.extend(_value_messages(additional, item))
            if "propertyNames" in spec:
                for message in _value_messages(spec["propertyNames"], key):
                    messages.append(f"property name {key!r}: {message}")
        min_properties = spec.get("minProperties")
        if isinstance(min_properties, int) and len(value) < min_properties:
            messages.append(f"must have at least {min_properties} property/properties")
    for sub in spec.get("allOf", []) if isinstance(spec.get("allOf"), list) else []:
        messages.extend(_value_messages(sub, value))
    if isinstance(spec.get("anyOf"), list) and spec["anyOf"]:
        branches = [_value_messages(sub, value) for sub in spec["anyOf"]]
        if all(branch for branch in branches):
            messages.append(
                "does not satisfy any allowed form "
                f"({branches[0][0] if branches[0] else 'no match'})"
            )
    if isinstance(spec.get("oneOf"), list) and spec["oneOf"]:
        branches = [_value_messages(sub, value) for sub in spec["oneOf"]]
        matches = sum(1 for branch in branches if not branch)
        if matches != 1:
            messages.append(
                f"must satisfy exactly one allowed form (matched {matches})"
            )
    if "not" in spec and isinstance(spec["not"], dict):
        if not _value_messages(spec["not"], value):
            messages.append("matches a forbidden form")
    return messages


def _validate_value(spec: dict, value, where: str, errors: list[str]) -> None:
    for message in _value_messages(spec, value):
        errors.append(f"{where}: {message}")


def _load_json(path: Path, rel: str, errors: list[str]) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{rel}: cannot load ({exc})")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{rel}: must be a JSON object")
        return {}
    return data


def _load_contract_schema(
    root: Path, rel: str, where: str, errors: list[str]
) -> dict:
    path = root / rel
    if not path.is_file():
        errors.append(f"{rel}: missing vendored canonical schema")
        return {}
    document = _load_json(path, rel, errors)
    return _deref(document, root, rel, where, errors)


def _check_palette_roles(
    schema: dict, root: Path, errors: list[str], notes: list[str]
) -> list[str]:
    palette = schema.get("palette")
    if not isinstance(palette, dict):
        errors.append(f"{SCHEMA}: missing the `palette` role declaration")
        return []
    roles = palette.get("roles")
    if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
        errors.append(f"{SCHEMA}: `palette.roles` must be a list of role names")
        return []
    if palette.get("role_count") != len(roles):
        errors.append(
            f"{SCHEMA}: palette.role_count {palette.get('role_count')!r} != {len(roles)} roles"
        )
    if len(set(roles)) != len(roles):
        errors.append(f"{SCHEMA}: palette roles must be unique")
    if len(roles) != 51:
        errors.append(f"{SCHEMA}: palette roles must be 51 (50 Material + on_backdrop)")

    vocabulary_path = root / VOCABULARY
    if not vocabulary_path.is_file():
        notes.append(
            f"{VOCABULARY} is absent; skipped the role-list equality check "
            f"(palette.v1 still enforced from {SCHEMA})"
        )
        return roles
    try:
        vocabulary = json.loads(vocabulary_path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"{VOCABULARY}: invalid JSON ({exc})")
        return roles
    source_roles = vocabulary.get("roles")
    if not isinstance(source_roles, list):
        errors.append(f"{VOCABULARY}: missing `roles`")
        return roles
    missing = sorted(set(source_roles) - set(roles))
    extra = sorted(set(roles) - set(source_roles))
    if missing or extra:
        errors.append(
            f"{SCHEMA}: palette roles disagree with {VOCABULARY}; "
            f"missing={missing} extra={extra}"
        )
    else:
        notes.append(f"palette roles == {VOCABULARY} ({len(roles)} roles)")
    return roles


def _read_pin(root: Path, errors: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    path = root / PIN
    if not path.is_file():
        errors.append(f"{PIN}: missing; a vendored canonical set must be pinned")
        return {}, {}
    metadata: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_HASH.match(line)
        if match:
            digest, name = match.groups()
            if name in hashes:
                errors.append(f"{PIN}:{lineno}: duplicate sha256 entry for {name}")
            hashes[name] = digest
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
            continue
        errors.append(f"{PIN}:{lineno}: unrecognised line {line!r}")
    return metadata, hashes


def _check_canonical(schema: dict, root: Path, errors: list[str]) -> None:
    canonical = schema.get("canonical")
    if not isinstance(canonical, dict):
        errors.append(f"{SCHEMA}: missing the `canonical` pointer")
        return
    if canonical.get("repository") != "contracts":
        errors.append(f"{SCHEMA}: canonical.repository must be 'contracts'")
    paths = canonical.get("paths")
    if not isinstance(paths, list) or set(paths) != CANONICAL_PATHS:
        errors.append(
            f"{SCHEMA}: canonical.paths must be exactly {sorted(CANONICAL_PATHS)}"
        )
    vendored = canonical.get("vendored")
    tag = canonical.get("tag")
    if vendored is not True:
        errors.append(
            f"{SCHEMA}: canonical.vendored must be true; this class requires the "
            f"pinned byte copies under skins/contracts/"
        )
    if not isinstance(tag, str) or not tag:
        errors.append(f"{SCHEMA}: canonical.tag must pin the vendored contracts tag")
    vendored_paths = canonical.get("vendored_paths")
    expected_vendored = set(VENDORED.values())
    if not isinstance(vendored_paths, list) or set(vendored_paths) != expected_vendored:
        errors.append(
            f"{SCHEMA}: canonical.vendored_paths must be exactly "
            f"{sorted(expected_vendored)}"
        )
    delegates = canonical.get("delegates")
    if not isinstance(delegates, dict) or delegates != DELEGATES:
        errors.append(f"{SCHEMA}: canonical.delegates must be exactly {DELEGATES}")
    legacy = canonical.get("legacy")
    if not isinstance(legacy, dict) or set(legacy.get("frozen_v1", [])) != LEGACY:
        errors.append(
            f"{SCHEMA}: canonical.legacy.frozen_v1 must name the three vendored "
            f"v1 skin schemas"
        )
    resolved_document = canonical.get("resolved_document")
    if not isinstance(resolved_document, dict):
        errors.append(
            f"{SCHEMA}: canonical.resolved_document must name the vendored "
            f"resolved tokens.json schema"
        )
    else:
        if resolved_document.get("path") != VENDORED["appearance-json"]:
            errors.append(
                f"{SCHEMA}: canonical.resolved_document.path must be "
                f"{VENDORED['appearance-json']!r}"
            )
        if not isinstance(resolved_document.get("note"), str) or not resolved_document[
            "note"
        ].strip():
            errors.append(
                f"{SCHEMA}: canonical.resolved_document.note must describe the "
                f"runtime-emitted tokens.json"
            )
    if canonical.get("pin") != PIN:
        errors.append(f"{SCHEMA}: canonical.pin must be {PIN!r}")

    for rel in paths if isinstance(paths, list) else []:
        if not isinstance(rel, str):
            errors.append(f"{SCHEMA}: canonical.paths entries must be strings")
            continue
        if (root / rel).exists():
            errors.append(
                f"{SCHEMA}: canonical path {rel!r} exists in this repo but is not "
                f"declared as vendored; do not silently mirror a contracts path"
            )

    metadata, expected_hashes = _read_pin(root, errors)
    pin_tag = metadata.get("contracts")
    if pin_tag != tag:
        errors.append(
            f"{PIN}: contracts={pin_tag!r} disagrees with canonical.tag {tag!r}"
        )
    source_commit = metadata.get("source-commit", "")
    if not SOURCE_COMMIT.match(source_commit):
        errors.append(
            f"{PIN}: source-commit must be the 40-hex contracts commit the "
            f"vendored bytes came from, got {source_commit!r}"
        )
    if not expected_hashes:
        errors.append(f"{PIN}: no sha256 entries")
    for name, rel in VENDORED_FILES.items():
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: missing vendored canonical schema")
            continue
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        recorded = expected_hashes.get(name)
        if recorded is None:
            errors.append(f"{PIN}: missing sha256 entry for {name}")
        elif recorded != actual:
            errors.append(f"{rel}: sha256 {actual} does not match {PIN} ({recorded})")
    extras = sorted(set(expected_hashes) - set(VENDORED_FILES))
    if extras:
        errors.append(f"{PIN}: unexpected sha256 entries {extras}")


def _check_forbidden_text(
    text: str, rel: str, errors: list[str], patterns: dict[str, re.Pattern[str]]
) -> None:
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, pattern in patterns.items():
            if pattern.search(line):
                errors.append(f"{rel}:{lineno}: {label} is forbidden -- {line.strip()!r}")


def _check_role_names(
    value: str, rel: str, where: str, roles: set[str], errors: list[str]
) -> None:
    for role in ROLE_REFERENCE.findall(value):
        if role not in roles:
            errors.append(
                f"{rel}: {where} names role {role!r}, which is not in palette.v1 "
                f"(no aliases, no carrier indices)"
            )


def _walk_strings(value, prefix: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_strings(item, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{prefix}[{index}]")
    elif isinstance(value, str):
        yield prefix, value


def _validate_manifest(
    path: Path,
    root: Path,
    manifest_schema: dict,
    roles: set[str],
    patterns: dict[str, re.Pattern[str]],
    errors: list[str],
) -> dict:
    rel = _rel(path, root)
    try:
        text = path.read_text()
    except OSError as exc:
        errors.append(f"{rel}: cannot read ({exc})")
        return {}
    _check_forbidden_text(text, rel, errors, patterns)
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"{rel}: invalid TOML ({exc})")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{rel}: manifest must be a TOML table")
        return {}

    for key in data:
        if key in FORBIDDEN_TOP_KEYS:
            errors.append(
                f"{rel}: unknown top-level key {key!r} "
                f"(structure/variant keys are forbidden by the frozen spec)"
            )
    if data.get("schemaVersion") != 2:
        errors.append(
            f"{rel}: schemaVersion must be 2 (the manifest envelope is schema_major 2), "
            f"got {data.get('schemaVersion')!r}"
        )
    if data.get("name") != path.stem:
        errors.append(
            f"{rel}: name {data.get('name')!r} must equal the file stem {path.stem!r}"
        )
    _validate_value(manifest_schema, data, rel, errors)
    for where, value in _walk_strings(data):
        _check_role_names(value, rel, where, roles, errors)
    return data


def _resolve_manifest(manifest: dict, mode: str) -> dict:
    """Resolve base groups plus the selected mode override (whole-group replace)."""
    base = manifest.get("groups", {})
    overrides = manifest.get("mode", {}).get(mode, {})
    resolved: dict = {"version": 2}
    for group in GROUPS:
        if isinstance(overrides, dict) and group in overrides:
            resolved[group] = copy.deepcopy(overrides[group])
        else:
            resolved[group] = copy.deepcopy(base.get(group))
    return resolved


def _leaves(value, prefix: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _leaves(item, f"{prefix}.{key}" if prefix else key)
    else:
        yield prefix, value


def _flatten(path: str) -> str:
    return "SKIN_" + re.sub(r"[^A-Za-z0-9]+", "_", path).upper()


def _css_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def _css_token_value(path: str, value) -> str:
    """Render a resolved token value in its CSS position.

    Lengths render as `<n>px`; letter-spacing as `<n>em`; font-weight is
    unitless; paints/fonts/strings render verbatim.
    """
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        number = _css_number(value)
        if path.endswith("letter-spacing"):
            return f"{number}em"
        if path.endswith("font-weight"):
            return number
        if path.endswith(("border-width", "radius", "padding", "font-size")) or path.startswith(
            "type.size-"
        ):
            return f"{number}px"
        return number
    return str(value)


def _css_paths(resolved: dict) -> dict[str, str]:
    """Flattened placeholder -> token path for every non-layout CSS token."""
    result: dict[str, str] = {}
    for group in CSS_GROUPS:
        for path, _value in _leaves(resolved.get(group, {}), group):
            result[_flatten(path)] = path
    return result


def _layout_placeholders(resolved: dict) -> set[str]:
    return {_flatten(path) for path, _value in _leaves(resolved.get("layout", {}), "layout")}


def expand_template(template: str, resolved: dict) -> str:
    """Expand flattened v2 placeholders using the resolved token values."""
    by_path = {
        _flatten(path): (path, value)
        for group in CSS_GROUPS
        for path, value in _leaves(resolved.get(group, {}), group)
    }

    def replace(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        item = by_path.get(name)
        if item is None:
            return match.group(0)
        path, value = item
        return _css_token_value(path, value)

    return PLACEHOLDER.sub(replace, template)


def _check_expansion(
    root: Path,
    templates: list[Path],
    resolved_docs: list[tuple[str, str, dict]],
    errors: list[str],
    notes: list[str],
    used_paths: set[str],
) -> None:
    """Expand every template for every manifest × mode and enforce the unit rule."""
    for path in templates:
        rel = _rel(path, root)
        target = path.name[: -len(TEMPLATE_SUFFIX)]
        text = path.read_text()
        placeholders = {raw.strip() for raw in PLACEHOLDER.findall(text)}
        for manifest_name, mode, resolved in resolved_docs:
            expanded = expand_template(text, resolved)
            leftovers = sorted(set(PLACEHOLDER.findall(expanded)))
            if leftovers:
                errors.append(
                    f"{rel}: unexpanded placeholder(s) {leftovers} after "
                    f"rendering {manifest_name!r} mode={mode}"
                )
            by_path = {
                _flatten(path_name): (path_name, value)
                for group in CSS_GROUPS
                for path_name, value in _leaves(resolved.get(group, {}), group)
            }
            for name in placeholders:
                item = by_path.get(name)
                if item is None:
                    continue
                token_path, value = item
                expected = _css_token_value(token_path, value)
                if expected not in expanded:
                    errors.append(
                        f"{rel}: {token_path} did not render as {expected!r} "
                        f"for {manifest_name!r} mode={mode}"
                    )
                used_paths.add(token_path)
        notes.append(
            f"{rel}: target={target} expanded for "
            f"{','.join(f'{name}:{mode}' for name, mode, _ in resolved_docs)}"
        )
    notes.append(
        f"expanded {len(resolved_docs)} manifest×mode document(s) through "
        f"{len(templates)} template(s) with the unit rule "
        f"(length -> <n>px, letter-spacing -> <n>em, font-weight unitless)"
    )


def _check_template(
    path: Path,
    root: Path,
    legal_placeholders: dict[str, str],
    layout_placeholders: set[str],
    roles: set[str],
    patterns: dict[str, re.Pattern[str]],
    errors: list[str],
    notes: list[str],
) -> set[str]:
    rel = _rel(path, root)
    try:
        text = path.read_text()
    except OSError as exc:
        errors.append(f"{rel}: cannot read ({exc})")
        return set()
    _check_forbidden_text(text, rel, errors, patterns)

    used: set[str] = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        for raw in PLACEHOLDER.findall(line):
            name = raw.strip()
            if not SKIN_PLACEHOLDER.match(name):
                errors.append(
                    f"{rel}:{lineno}: placeholder {{{{ {name} }}}} is not a SKIN_* token"
                )
                continue
            used.add(name)
            if name in layout_placeholders:
                errors.append(
                    f"{rel}:{lineno}: {name} is a layout token; templates MUST NOT "
                    f"expand layout.<app> into CSS"
                )
                continue
            if name not in legal_placeholders:
                errors.append(
                    f"{rel}:{lineno}: {name} is not a token in the v2 appearance "
                    f"model (expected one of {sorted(legal_placeholders)})"
                )

    for role in ROLE_REFERENCE.findall(text):
        if role not in roles:
            errors.append(
                f"{rel}: names role {role!r}, which is not in palette.v1 "
                f"(no aliases, no carrier indices)"
            )

    unused = sorted(set(legal_placeholders) - used)
    if unused:
        notes.append(
            f"{rel}: {len(unused)} declared token(s) not used by this template: {unused}"
        )
    return used


def _check_css_token_paths(
    schema: dict, resolved_docs: list[tuple[str, str, dict]], errors: list[str]
) -> None:
    frozen = schema.get("frozen") if isinstance(schema.get("frozen"), dict) else {}
    declared = frozen.get("css_token_paths")
    if not isinstance(declared, list) or not all(isinstance(item, str) for item in declared):
        errors.append(f"{SCHEMA}: frozen.css_token_paths must be a list of token paths")
        return
    derived: set[str] = set()
    for _name, _mode, resolved in resolved_docs:
        derived.update(_css_paths(resolved).values())
    if set(declared) != derived:
        errors.append(
            f"{SCHEMA}: frozen.css_token_paths disagree with the resolved v2 "
            f"vocabulary; missing={sorted(derived - set(declared))} "
            f"extra={sorted(set(declared) - derived)}"
        )


def validate(root: Path) -> tuple[list[str], list[str], dict]:
    """Validate the skins class; return (errors, notes, stats)."""
    errors: list[str] = []
    notes: list[str] = []
    stats: dict = {
        "manifests": 0,
        "templates": 0,
        "targets": [],
        "tokens": 0,
        "roles": 0,
        "expansions": 0,
    }

    schema_path = root / SCHEMA
    if not schema_path.is_file():
        return ([f"{SCHEMA}: missing at {schema_path}"], notes, stats)
    try:
        schema = json.loads(schema_path.read_text())
    except json.JSONDecodeError as exc:
        return ([f"{SCHEMA}: invalid JSON ({exc})"], notes, stats)
    if not isinstance(schema, dict):
        return ([f"{SCHEMA}: must be a JSON object"], notes, stats)
    if schema.get("schema_major") != 2:
        errors.append(f"{SCHEMA}: schema_major must be 2, got {schema.get('schema_major')!r}")

    _check_canonical(schema, root, errors)
    roles = _check_palette_roles(schema, root, errors, notes)
    roles_set = set(roles)
    stats["roles"] = len(roles)

    manifest_schema = _load_contract_schema(
        root, VENDORED["appearance-manifest"], "appearance manifest", errors
    )
    resolved_schema = _load_contract_schema(
        root, VENDORED["appearance-json"], "appearance tokens", errors
    )
    _load_contract_schema(
        root, VENDORED["appearance-artifact"], "appearance artifact", errors
    )

    frozen = schema.get("frozen") if isinstance(schema.get("frozen"), dict) else {}
    manifest_format = frozen.get("manifest_format")
    if manifest_format != "toml":
        errors.append(f"{SCHEMA}: only the TOML manifest format is supported")

    patterns: dict[str, re.Pattern[str]] = dict(HARD_FORBIDDEN)
    declared_patterns = frozen.get("forbidden_patterns", [])
    if not isinstance(declared_patterns, list) or not all(
        isinstance(p, str) for p in declared_patterns
    ):
        errors.append(f"{SCHEMA}: frozen.forbidden_patterns must be a list of regex strings")
        declared_patterns = []
    for pattern in declared_patterns:
        compiled = _compile(pattern, f"{SCHEMA}: frozen.forbidden_patterns", errors)
        if compiled is not None:
            patterns[f"pattern {pattern!r}"] = compiled

    manifests_dir = root / MANIFESTS_DIR
    required = set(frozen.get("required_files", [])) if isinstance(frozen, dict) else set()
    found: list[Path] = []
    manifest_data: list[dict] = []
    if not manifests_dir.is_dir():
        errors.append(f"{MANIFESTS_DIR}/: missing")
    else:
        found = sorted(manifests_dir.glob("*.toml"))
        found_stems = {p.stem for p in found}
        missing = sorted(required - found_stems)
        extra = sorted(found_stems - required)
        if missing:
            errors.append(f"{MANIFESTS_DIR}/: missing required manifest(s) {missing}")
        if extra:
            errors.append(
                f"{MANIFESTS_DIR}/: unexpected manifest(s) {extra}; the frozen set is "
                f"{sorted(required)}"
            )
        for path in found:
            data = _validate_manifest(
                path, root, manifest_schema, roles_set, patterns, errors
            )
            manifest_data.append(data)
            stats["manifests"] += 1

    resolved_docs: list[tuple[str, str, dict]] = []
    for manifest in manifest_data:
        name = str(manifest.get("name"))
        for mode in MODES:
            resolved = _resolve_manifest(manifest, mode)
            _validate_value(
                resolved_schema, resolved, f"{name} ({mode} tokens.json)", errors
            )
            resolved_docs.append((name, mode, resolved))
    stats["expansions"] = len(resolved_docs)
    if resolved_docs:
        _check_css_token_paths(schema, resolved_docs, errors)
        stats["tokens"] = len(_css_paths(resolved_docs[0][2]))

    legal_placeholders: dict[str, str] = {}
    layout_placeholders: set[str] = set()
    for _name, _mode, resolved in resolved_docs:
        legal_placeholders.update(_css_paths(resolved))
        layout_placeholders.update(_layout_placeholders(resolved))

    templates_dir = root / TEMPLATES_DIR
    templates: list[Path] = []
    if not templates_dir.is_dir():
        errors.append(f"{TEMPLATES_DIR}/: missing")
    else:
        for path in sorted(p for p in templates_dir.iterdir() if p.is_file()):
            rel = _rel(path, root)
            if not TEMPLATE_NAME.match(path.name):
                errors.append(
                    f"{rel}: template name {path.name!r} does not match "
                    f"{TEMPLATE_NAME.pattern}; the target configDir is the prefix "
                    f"before {TEMPLATE_SUFFIX}"
                )
                continue
            templates.append(path)
            stats["targets"].append(path.name[: -len(TEMPLATE_SUFFIX)])
        stats["targets"] = sorted(set(stats["targets"]))
        if not templates:
            errors.append(
                f"{TEMPLATES_DIR}/: no template named <configDir>{TEMPLATE_SUFFIX}"
            )

    used_paths: set[str] = set()
    for path in templates:
        _check_template(
            path,
            root,
            legal_placeholders,
            layout_placeholders,
            roles_set,
            patterns,
            errors,
            notes,
        )
        stats["templates"] += 1
    if templates and resolved_docs:
        _check_expansion(
            root, templates, resolved_docs, errors, notes, used_paths
        )

    unused = sorted(set(legal_placeholders.values()) - used_paths)
    if unused:
        notes.append(
            f"{len(unused)} v2 CSS token(s) are not used by any template: {unused}"
        )
    for group in ("state", "type", "ink"):
        expected = {
            path
            for path in legal_placeholders.values()
            if path.startswith(group + ".")
        }
        if expected and not (expected & used_paths):
            errors.append(f"{SCHEMA}: the template set uses no {group} token")
    return errors, notes, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the skins class")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent

    errors, notes, stats = validate(root)
    targets = ",".join(stats["targets"]) or "-"
    print(
        f"validate-skins: root={root} manifests={stats['manifests']} "
        f"templates={stats['templates']} targets={targets} "
        f"tokens={stats['tokens']} roles={stats['roles']} "
        f"modes={len(MODES)} expansions={stats['expansions']}"
    )
    for note in notes:
        print(f"validate-skins: note: {note}")
    if errors:
        print(f"validate-skins: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        "validate-skins: PASS -- vendored v0.7.0 hashes, v2 manifests, mode "
        "resolution, tokens.json schema, flattened placeholder coverage, role "
        "vocabulary and unit-rule expansion agree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
