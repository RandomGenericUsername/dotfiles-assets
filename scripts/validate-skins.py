#!/usr/bin/env python3
"""validate-skins -- the `skins` class contract, asserted against the corpus.

WHAT THIS GATE PROVES (frozen skin spec v1):

  1. THE LOCAL CONTRACT IS HONEST. `skins/schema.json` carries `schema_major: 1`,
     names the canonical `contracts` paths, and does not claim a vendored copy it
     cannot prove. The 51-role palette list is `palette.v1`, checked against
     `icons/mappings/vocabulary.json` (the repository's vocabulary of record):
     50 theme-producer Material roles + `on_backdrop`, no aliases.

  2. EVERY MANIFEST HAS THE FROZEN SHAPE. The three required manifests exist,
     no extra manifest hides beside them, `name` equals the file stem, and every
     token group (`shape`, `rhythm`, `surface`, `ink`, `type`, `layout`) carries
     exactly its frozen token names. A `structure`, `variant`, `state`,
     `density` or `paint` key fails: those are the app's business.

  3. VALUES ARE ROLE EXPRESSIONS, NEVER LITERAL COLOURS. Surface/border values
     are `transparent`, `@role`, `alpha(@role, n)` or
     `color-mix(in srgb, @role n%, transparent|@role)`; `blur` is `none` or
     `blur(Npx) [saturate(N)]`; `shadow` is `none` or the app-local offset/blur
     rgba form. Every `@role` must be in `palette.v1`. No hex literal, no CSS
     transition, no animation.

  4. PLACEHOLDER COVERAGE IS TWO-WAY. Every `{{SKIN_*}}` used by the GTK template
     is a token declared in the schema, and every required token is present in
     every manifest. An underscore spelling that names no token fails.

WHY STDLIB ONLY. A fresh clone must pass `make gates` with no virtualenv and no
network. The manifest format is TOML (`tomllib`, Python >= 3.11), the contract is
JSON, and the mini-validator below covers the exact JSON-Schema subset the local
target uses (`$ref`, `const`, `type`, `pattern`, `minLength`). The fixture suite
under `skins/tests/` mirrors each negative case; `jsonschema`/`pytest` are NOT
required for this gate.

Usage: ``python3 scripts/validate-skins.py [--root REPO_ROOT]``
Exit 0 = all manifests, the template and their coverage agree with the contract.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

SKINS_DIR = "skins"
SCHEMA = "skins/schema.json"
MANIFESTS_DIR = "skins/manifests"
TEMPLATES_DIR = "skins/templates"
VOCABULARY = "icons/mappings/vocabulary.json"

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


class ContractError(Exception):
    """A violation that must be reported by path."""


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


def _resolve(spec: dict, defs: dict) -> dict:
    """Resolve the one `$ref` shape the local schema uses (`#/$defs/<name>`)."""
    seen = 0
    while isinstance(spec, dict) and "$ref" in spec:
        ref = spec["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            raise ContractError(f"unsupported $ref {ref!r}")
        spec = defs.get(ref.removeprefix("#/$defs/"))
        if not isinstance(spec, dict):
            raise ContractError(f"unresolved $ref {ref!r}")
        seen += 1
        if seen > 10:
            raise ContractError(f"cyclic $ref {ref!r}")
    return spec


def _validate_value(
    spec: dict,
    value,
    defs: dict,
    where: str,
    errors: list[str],
) -> None:
    """Validate the JSON-Schema subset the local skin target declares."""
    try:
        spec = _resolve(spec, defs)
    except ContractError as exc:
        errors.append(f"{where}: {exc}")
        return
    if "const" in spec and value != spec["const"]:
        errors.append(f"{where}: must be {spec['const']!r}, got {value!r}")
    if "type" in spec:
        wanted = spec["type"]
        if wanted == "string" and not isinstance(value, str):
            errors.append(f"{where}: must be a string, got {type(value).__name__}")
            return
        if wanted == "object" and not isinstance(value, dict):
            errors.append(f"{where}: must be a table/mapping")
            return
    if isinstance(value, str):
        minimum = spec.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{where}: must be at least {minimum} character(s)")
        pattern = spec.get("pattern")
        if isinstance(pattern, str):
            compiled = _compile(pattern, where, errors)
            if compiled is not None and not compiled.search(value):
                errors.append(f"{where}: {value!r} does not match {pattern}")


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


def _check_canonical(schema: dict, root: Path, errors: list[str]) -> None:
    canonical = schema.get("canonical")
    if not isinstance(canonical, dict):
        errors.append(f"{SCHEMA}: missing the `canonical` pointer")
        return
    if canonical.get("repository") != "contracts":
        errors.append(f"{SCHEMA}: canonical.repository must be 'contracts'")
    paths = canonical.get("paths")
    expected = {
        "schemas/skin-token.schema.json",
        "schemas/skin-manifest.schema.json",
    }
    if not isinstance(paths, list) or set(paths) != expected:
        errors.append(
            f"{SCHEMA}: canonical.paths must be exactly {sorted(expected)}"
        )
    vendored = canonical.get("vendored")
    tag = canonical.get("tag")
    if vendored is True:
        # Vendoring is allowed, but only with a pinned tag and a byte-equality
        # test. This validator has no vendored copy to hash, so a claim here
        # would be exactly the false statement the contract forbids.
        if not isinstance(tag, str) or not tag:
            errors.append(
                f"{SCHEMA}: canonical.vendored is true but canonical.tag is not pinned"
            )
        errors.append(
            f"{SCHEMA}: canonical.vendored is true but no vendored copy/byte-equality "
            f"test exists in this tree; either add both or set vendored=false"
        )
    elif vendored is not False:
        errors.append(f"{SCHEMA}: canonical.vendored must be true or false")
    if vendored is False and tag is not None:
        errors.append(
            f"{SCHEMA}: canonical.tag is set while canonical.vendored is false"
        )
    for rel in paths if isinstance(paths, list) else []:
        if not isinstance(rel, str):
            errors.append(f"{SCHEMA}: canonical.paths entries must be strings")
            continue
        if (root / rel).exists():
            errors.append(
                f"{SCHEMA}: canonical path {rel!r} exists in this repo but is not "
                f"declared as vendored; do not silently mirror a contracts path"
            )


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
    defs = schema.get("$defs", {})
    if not isinstance(props, dict) or not isinstance(defs, dict):
        errors.append(f"{SCHEMA}: properties/$defs must be mappings")
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
            _validate_value(spec, value[token], defs, f"{rel}: {where}", errors)
            if isinstance(value[token], str):
                _check_role_names(value[token], rel, where, roles, errors)
    return data


def _placeholder_map(groups: dict[str, list[str]]) -> dict[str, str]:
    return {
        f"SKIN_{token.upper().replace('-', '_')}": f"{group}.{token}"
        for group, tokens in groups.items()
        for token in tokens
    }


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
    stats: dict = {"manifests": 0, "templates": 0, "tokens": 0, "roles": 0}

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
            _validate_manifest(path, root, schema, groups, roles_set, patterns, errors)
            stats["manifests"] += 1

    templates_dir = root / TEMPLATES_DIR
    templates: list[Path] = []
    if not templates_dir.is_dir():
        errors.append(f"{TEMPLATES_DIR}/: missing")
    else:
        templates = sorted(templates_dir.glob("*.j2"))
        if not templates:
            errors.append(f"{TEMPLATES_DIR}/: no *.j2 template")
    expected = _placeholder_map(groups)
    for path in templates:
        _check_template(path, root, expected, roles_set, patterns, errors, notes)
        stats["templates"] += 1

    return errors, notes, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the skins class")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent

    errors, notes, stats = validate(root)
    print(
        f"validate-skins: root={root} manifests={stats['manifests']} "
        f"templates={stats['templates']} tokens={stats['tokens']} roles={stats['roles']}"
    )
    for note in notes:
        print(f"validate-skins: note: {note}")
    if errors:
        print(f"validate-skins: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("validate-skins: PASS -- manifests, schema pointer, role vocabulary and template coverage agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
