#!/usr/bin/env python3
"""validate-skins -- the `skins` class contract, asserted against the corpus.

WHAT THIS GATE PROVES (frozen skin spec v1):

  1. THE LOCAL CONTRACT IS HONEST. `skins/schema.json` carries `schema_major: 1`,
     names the canonical `contracts` paths, and proves its vendored claim:
     `skins/contracts/{skin-token,skin-manifest}.schema.json` are byte copies
     whose sha256 matches `skins/contracts/PIN`. The 51-role palette list is
     `palette.v1`, checked against `icons/mappings/vocabulary.json` (the
     repository's vocabulary of record): 50 theme-producer Material roles +
     `on_backdrop`, no aliases.

  2. EVERY MANIFEST HAS THE FROZEN SHAPE. The three required manifests exist,
     no extra manifest hides beside them, `name` equals the file stem, and every
     token group (`shape`, `rhythm`, `surface`, `ink`, `type`, `layout`) carries
     exactly its frozen token names. A `structure`, `variant`, `state`,
     `density` or `paint` key fails: those are the app's business.

  3. TOKEN VALUE TYPES COME FROM THE CANONICAL SCHEMA, NOT A LOOKALIKE.
     `skins/schema.json` delegates every token property by external `$ref` to
     the vendored `skin-manifest.schema.json` definitions. Numeric tokens
     (`radius-*`, `border-w`, `hairline-w`, `gap`, `title-size`, `text-size`
     and all layout tokens) are unitless JSON numbers; a string such as `"12px"` is rejected
     because AGS's parser rejects it. `cell-pad` is the literal `"Npx Npx"`
     string. Every `@role` must be in `palette.v1`. No hex literal, no CSS
     transition, no animation.

  4. PLACEHOLDER COVERAGE IS TWO-WAY AND THE UNIT RULE HOLDS. Every
     `{{SKIN_*}}` used by the GTK template is a token declared in the schema,
     and every required token is present in every manifest. Expanding each
     manifest through the template renders a numeric token as `<n>px` in its
     CSS length position; `cell-pad` is emitted verbatim. An underscore spelling
     that names no token fails.

  5. THE TEMPLATE SET NAMES ITS TARGETS. The contract freezes one template per
     target config directory, named `<configDir>.gtk.css.j2`; the expander
     renders `<configDir>.css`. Every file in `skins/templates/` must match
     `^[a-z0-9][a-z0-9_-]*\\.gtk\\.css\\.j2$`, and the target reported in the
     summary is the prefix before `.gtk.css.j2`. A stale name such as
     `ags-bar.gtk.css.j2` fails here instead of leaving the bar's `ags` target
     unreachable at runtime. Every discovered template is expanded through
     every manifest (glass/flat/paper), so a template that only renders for one
     skin cannot pass unnoticed.

  6. THE RESOLVED DOCUMENT SCHEMA IS VENDORED WITH THE PAIR. `skin-json.schema.
     json` is a byte copy from the same `contracts` tag and is pinned by sha256;
     it is the schema the platform uses to parse the runtime-emitted
     `current/skin.json` (version 1 + the six groups, numeric tokens raw).

WHY STDLIB ONLY. A fresh clone must pass `make gates` with no virtualenv and no
network. The manifest format is TOML (`tomllib`, Python >= 3.11), the contract is
JSON, and the mini-validator below covers the exact JSON-Schema subset the
vendored canonical definitions use (`$ref`, `const`, `enum`, `type`, `minimum`,
`pattern`, `minLength`, `allOf`/`anyOf`/`oneOf`/`not`). The fixture suite under
`skins/tests/` mirrors each negative case; `jsonschema`/`pytest` are NOT
required for this gate.

Usage: ``python3 scripts/validate-skins.py [--root REPO_ROOT]``
Exit 0 = all manifests, the template and their coverage agree with the contract.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
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
    "token": "skins/contracts/skin-token.schema.json",
    "manifest": "skins/contracts/skin-manifest.schema.json",
    "resolved": "skins/contracts/skin-json.schema.json",
}
#: Only the token/manifest pair is referenced by `$ref` from skins/schema.json;
#: the resolved-document schema describes the runtime output, not the manifest
#: envelope, so it is vendored and pinned without being a delegate.
DELEGATES = {
    "token": VENDORED["token"],
    "manifest": VENDORED["manifest"],
}
VENDORED_FILES = {
    posixpath.basename(rel): rel for rel in VENDORED.values()
}
CANONICAL_PATHS = {
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
PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
SKIN_PLACEHOLDER = re.compile(r"^SKIN_[A-Z0-9_]+$")
ROLE_REFERENCE = re.compile(r"@([a-z][a-z0-9_]*)")

#: Patterns every manifest and template is scanned for, in addition to the
#: schema's own `frozen.forbidden_patterns`. They are the frozen spec's hard
#: bans, not a style preference: GTK 4.24 ignores transitions.
HARD_FORBIDDEN = {
    "literal hex colour": HEX_LITERAL,
    "CSS transition": re.compile(r"\btransition\s*:"),
    "CSS animation": re.compile(r"\banimation\s*:"),
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
    resolved = _deref(
        target, root, target_rel, where, errors, stack + (key,)
    )
    # Draft 2020-12 allows siblings of $ref; canonical definitions do not use
    # them, but preserving them keeps this resolver honest if one appears.
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
    """Validate the JSON-Schema subset the vendored canonical pair declares."""
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
        maximum = spec.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            messages.append(f"must be <= {maximum}, got {value!r}")
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


def _validate_value(
    spec: dict,
    value,
    where: str,
    errors: list[str],
) -> None:
    for message in _value_messages(spec, value):
        errors.append(f"{where}: {message}")


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
        errors.append(f"{PIN}: missing; a vendored canonical pair must be pinned")
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


def _check_delegation(schema: dict, errors: list[str]) -> None:
    """Prove token value types are canonical $refs, not a local lookalike."""
    props = schema.get("properties")
    frozen = schema.get("frozen")
    groups = frozen.get("token_groups", {}) if isinstance(frozen, dict) else {}
    if not isinstance(props, dict) or not isinstance(groups, dict):
        return
    for group, tokens in groups.items():
        group_props = props.get(group, {}).get("properties", {})
        for token in tokens:
            spec = group_props.get(token)
            if not isinstance(spec, dict):
                errors.append(f"{SCHEMA}: {group}.{token} has no value specification")
                continue
            ref = spec.get("$ref")
            if not isinstance(ref, str) or not ref.startswith(
                "contracts/skin-manifest.schema.json#"
            ):
                errors.append(
                    f"{SCHEMA}: {group}.{token} must delegate by $ref to the "
                    f"vendored skin-manifest schema, got {spec!r}"
                )
            local_grammar = set(spec) - {"$ref", "$comment", "description", "title"}
            if local_grammar:
                errors.append(
                    f"{SCHEMA}: {group}.{token} declares local value grammar "
                    f"{sorted(local_grammar)} beside its canonical $ref"
                )


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
        errors.append(
            f"{SCHEMA}: canonical.delegates must be exactly {DELEGATES}"
        )
    resolved_document = canonical.get("resolved_document")
    if not isinstance(resolved_document, dict):
        errors.append(
            f"{SCHEMA}: canonical.resolved_document must name the vendored "
            f"resolved skin.json schema"
        )
    else:
        if resolved_document.get("path") != VENDORED["resolved"]:
            errors.append(
                f"{SCHEMA}: canonical.resolved_document.path must be "
                f"{VENDORED['resolved']!r}"
            )
        if not isinstance(resolved_document.get("note"), str) or not resolved_document[
            "note"
        ].strip():
            errors.append(
                f"{SCHEMA}: canonical.resolved_document.note must describe the "
                f"runtime-emitted skin.json"
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
            errors.append(
                f"{rel}: sha256 {actual} does not match {PIN} ({recorded})"
            )
    extras = sorted(set(expected_hashes) - set(VENDORED_FILES))
    if extras:
        errors.append(f"{PIN}: unexpected sha256 entries {extras}")
    _check_delegation(schema, errors)


def _token_groups(schema: dict, errors: list[str]) -> dict[str, list[str]]:
    frozen = schema.get("frozen")
    if not isinstance(frozen, dict):
        errors.append(f"{SCHEMA}: missing the `frozen` token declaration")
        return {}
    groups = frozen.get("token_groups")
    if not isinstance(groups, dict) or not groups:
        errors.append(f"{SCHEMA}: `frozen.token_groups` must be a non-empty mapping")
        return {}
    result: dict[str, list[str]] = {}
    for group, tokens in groups.items():
        if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
            errors.append(f"{SCHEMA}: token group {group!r} must be a list of names")
            continue
        if len(set(tokens)) != len(tokens):
            errors.append(f"{SCHEMA}: token group {group!r} has duplicate names")
        result[group] = tokens
    if frozen.get("manifest_format") != "toml":
        errors.append(f"{SCHEMA}: frozen.manifest_format must be 'toml'")
    required = frozen.get("required_files")
    if not isinstance(required, list) or not all(isinstance(n, str) for n in required):
        errors.append(f"{SCHEMA}: frozen.required_files must be a list of stems")
        return result
    if set(required) != {"glass", "flat", "paper"}:
        errors.append(
            f"{SCHEMA}: frozen.required_files must be glass, flat and paper"
        )
    return result


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


def _validate_manifest(
    path: Path,
    root: Path,
    schema: dict,
    groups: dict[str, list[str]],
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

    frozen = schema["frozen"]
    allowed_top = {"schema_major", "name"} | set(groups)
    for key in data:
        if key not in allowed_top:
            hint = ""
            if key in frozen.get("forbidden_keys", []):
                hint = " (structure/variant keys are forbidden by the frozen spec)"
            errors.append(f"{rel}: unknown top-level key {key!r}{hint}")
    for key in ("schema_major", "name"):
        if key not in data:
            errors.append(f"{rel}: missing required key {key!r}")

    if data.get("schema_major") != 1:
        errors.append(f"{rel}: schema_major must be 1, got {data.get('schema_major')!r}")
    if data.get("name") != path.stem:
        errors.append(
            f"{rel}: name {data.get('name')!r} must equal the file stem {path.stem!r}"
        )

    props = schema.get("properties", {})
    if not isinstance(props, dict):
        errors.append(f"{SCHEMA}: properties must be a mapping")
        return data

    for group, token_names in groups.items():
        value = data.get(group)
        if not isinstance(value, dict):
            errors.append(f"{rel}: missing token group {group!r}")
            continue
        extra = sorted(set(value) - set(token_names))
        missing = sorted(set(token_names) - set(value))
        if extra:
            errors.append(f"{rel}: {group}: unknown token(s) {extra}")
        if missing:
            errors.append(f"{rel}: {group}: missing token(s) {missing}")
        group_props = props.get(group, {}).get("properties", {})
        for token in token_names:
            if token not in value:
                continue
            spec = group_props.get(token)
            if not isinstance(spec, dict):
                errors.append(f"{SCHEMA}: no value spec for {group}.{token}")
                continue
            where = f"{group}.{token}"
            resolved = _deref(
                spec, root, SCHEMA, f"{rel}: {where}", errors
            )
            _validate_value(resolved, value[token], f"{rel}: {where}", errors)
            if isinstance(value[token], str):
                _check_role_names(value[token], rel, where, roles, errors)
    return data


def _placeholder_map(groups: dict[str, list[str]]) -> dict[str, str]:
    return {
        f"SKIN_{token.upper().replace('-', '_')}": f"{group}.{token}"
        for group, tokens in groups.items()
        for token in tokens
    }


def _css_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def _css_token_value(value) -> str:
    """The v1 unit rule: a numeric token is a CSS length, rendered as `<n>px`.

    `cell-pad` and every paint/ink/font token are strings and are emitted
    verbatim; only JSON numbers gain the `px` suffix.
    """
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{_css_number(value)}px"
    return str(value)


def expand_template(
    template: str, manifest: dict, groups: dict[str, list[str]]
) -> str:
    """Expand `{{SKIN_*}}` placeholders using the unit rule."""
    for placeholder, dotted in _placeholder_map(groups).items():
        group, token = dotted.split(".", 1)
        value = manifest.get(group, {}).get(token)
        if value is None:
            continue
        template = template.replace(
            "{{" + placeholder + "}}", _css_token_value(value)
        )
    return template


def _check_expansion(
    root: Path,
    templates: list[Path],
    manifests: list[dict],
    groups: dict[str, list[str]],
    errors: list[str],
    notes: list[str],
) -> None:
    """Expand every manifest through every template and enforce the unit rule."""
    for path in templates:
        rel = _rel(path, root)
        target = path.name[: -len(TEMPLATE_SUFFIX)]
        text = path.read_text()
        rendered_for: list[str] = []
        for manifest in manifests:
            name = manifest.get("name")
            rendered_for.append(str(name))
            expanded = expand_template(text, manifest, groups)
            leftovers = sorted(set(PLACEHOLDER.findall(expanded)))
            if leftovers:
                errors.append(
                    f"{rel}: unexpanded placeholder(s) {leftovers} after "
                    f"rendering {name!r}"
                )
            for group, tokens in groups.items():
                for token in tokens:
                    value = manifest.get(group, {}).get(token)
                    expected = _css_token_value(value)
                    placeholder = f"{{{{SKIN_{token.upper().replace('-', '_')}}}}}"
                    if placeholder in text and expected not in expanded:
                        errors.append(
                            f"{rel}: {group}.{token} did not render as {expected!r}"
                        )
        notes.append(
            f"{rel}: target={target} expanded for {','.join(rendered_for)}"
        )
    notes.append(
        f"expanded {len(manifests)} manifest(s) through {len(templates)} "
        f"template(s) with the unit rule (number -> <n>px, cell-pad verbatim)"
    )


def _check_template(
    path: Path,
    root: Path,
    expected: dict[str, str],
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
            if name not in expected:
                errors.append(
                    f"{rel}:{lineno}: {name} is not a token in {SCHEMA} "
                    f"(expected one of {sorted(expected)})"
                )

    for role in ROLE_REFERENCE.findall(text):
        if role not in roles:
            errors.append(
                f"{rel}: names role {role!r}, which is not in palette.v1 "
                f"(no aliases, no carrier indices)"
            )

    unused = sorted(set(expected) - used)
    if unused:
        notes.append(f"{rel}: {len(unused)} declared token(s) not used by this template: {unused}")
    return used


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
    if schema.get("schema_major") != 1:
        errors.append(f"{SCHEMA}: schema_major must be 1, got {schema.get('schema_major')!r}")

    _check_canonical(schema, root, errors)
    roles = _check_palette_roles(schema, root, errors, notes)
    roles_set = set(roles)
    groups = _token_groups(schema, errors)
    stats["roles"] = len(roles)
    stats["tokens"] = sum(len(t) for t in groups.values())

    frozen = schema.get("frozen", {})
    manifest_format = frozen.get("manifest_format") if isinstance(frozen, dict) else None
    if manifest_format != "toml":
        errors.append(f"{SCHEMA}: only the TOML manifest format is supported")

    patterns: dict[str, re.Pattern[str]] = dict(HARD_FORBIDDEN)
    declared_patterns = frozen.get("forbidden_patterns", []) if isinstance(frozen, dict) else []
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
        for group, tokens in groups.items():
            if not tokens:
                errors.append(f"{SCHEMA}: token group {group!r} is empty")
        for path in found:
            data = _validate_manifest(
                path, root, schema, groups, roles_set, patterns, errors
            )
            manifest_data.append(data)
            stats["manifests"] += 1

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
    expected = _placeholder_map(groups)
    for path in templates:
        _check_template(path, root, expected, roles_set, patterns, errors, notes)
        stats["templates"] += 1
    if templates and manifest_data:
        _check_expansion(
            root, templates, manifest_data, groups, errors, notes
        )

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
        f"tokens={stats['tokens']} roles={stats['roles']}"
    )
    for note in notes:
        print(f"validate-skins: note: {note}")
    if errors:
        print(f"validate-skins: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        "validate-skins: PASS -- vendored canonical hashes/types, manifests, "
        "template naming/targets, unit-rule expansion, role vocabulary and "
        "template coverage agree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
