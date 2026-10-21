#!/usr/bin/env python3
"""validate-icons -- the icons corpus: mappings resolve, tokens are declared, SVGs parse.

WHAT THIS GATE PROVES, and why each part is separate:

  1. EVERY MAPPING TEMPLATE RESOLVES. Each `variants[].template` in the ONE
     group-map file (`icons/mappings/icons.yaml`) names a real file under
     `icons/templates/`, joined EXACTLY as the consumer joins it: relative to the
     group's template root (`templates/<template_dir>`, default `.`), not to the
     mapping file's directory. A stale entry here is otherwise discovered at render
     time on a user's machine, never at release time.

  2. EVERY PLACEHOLDER IS DECLARED. Each `{{COLOR_*}}` token used by a template
     the mapping renders must be declared for that group: in `mappings/defaults.yaml`
     (the group-independent vocabulary) or in that group's `color_mappings` /
     variant `color_mappings`. This mirrors the consumer's merge order
     (defaults < group < variant), so an undeclared token is a token no palette
     can satisfy.

  3. EVERY SVG IS WELL-FORMED XML. A malformed template fails the tag here, not
     in a renderer.

  4. THE SMALL SHAPE RULES THE CONTRACT STATES. `variants[].name` is unique inside
     its group, `output` is a bare file name (no path separators, no `..`, no
     placeholder), and a `template` may not escape the templates root.

  5. ONE MANIFEST, ONE VOCABULARY. `icons/mappings/` holds exactly `icons.yaml`
     (the group map) and `defaults.yaml` (the COLOR_* vocabulary). A second
     `*.yaml` there is a contract violation: the consumer loads ONE mapping file,
     so a per-group split is a second source of truth that drifts by construction.
     The six legacy per-concern files (battery, email-client, network, power-menu,
     wallpaper-selector, wlogout) were retired in v0.2.0 for exactly that reason.

WHAT IT REPORTS WITHOUT FAILING: a token declared for one group and unused there
(forward compatibility is allowed) and a template no variant references.

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
VOCABULARY_FILES = ("icons.yaml", "defaults.yaml")

TOKEN = re.compile(r"\{\{\s*([^{}]*?)\s*\}\}")
BARE_TOKEN = re.compile(r"\{\{(COLOR_[A-Z0-9_]+)\}\}")
COLOR_NAME = re.compile(r"^COLOR_[A-Z0-9_]+$")
OUTPUT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class CorpusError(Exception):
    """A violation, with the path/reason a reader needs to fix it."""


class YamlSubsetError(Exception):
    """A mapping file used YAML this parser deliberately refuses to guess at."""


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
        key, sep, rest = body.partition(":")
        if not sep or not key.strip():
            raise YamlSubsetError(
                f"{source}:{lineno}: a sequence item must start with `key: value` "
                f"(the mappings' shape); got {text!r}"
            )
        item: dict[str, object] = {}
        key, rest = key.strip(), rest.strip()
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
    if not isinstance(data.get("schema_major"), int):
        errors.append(f"{SCHEMA}: missing an integer `schema_major` (spine AD-12)")
    paths = data.get("paths")
    if not isinstance(paths, dict):
        errors.append(f"{SCHEMA}: `paths` must be a mapping")
        return
    if paths.get("templates_root") != TEMPLATES:
        errors.append(
            f"{SCHEMA}: paths.templates_root is {paths.get('templates_root')!r}; this "
            f"validator joins every template under {TEMPLATES!r} -- keep the contract and "
            f"the checker in step"
        )
    if paths.get("mappings_root") != MAPPINGS:
        errors.append(
            f"{SCHEMA}: paths.mappings_root is {paths.get('mappings_root')!r}; this "
            f"validator reads {MAPPINGS!r}"
        )
    if paths.get("defaults") != DEFAULTS:
        errors.append(f"{SCHEMA}: paths.defaults is {paths.get('defaults')!r}; expected {DEFAULTS!r}")


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
            errors.append(f"{DEFAULTS}: {name!r} is not a COLOR_* token name")
        if not isinstance(value, str) or not value:
            errors.append(f"{DEFAULTS}: {name!r} must map to a non-empty palette role")
    return defaults


def _check_color_mappings(where: str, value: object, errors: list[str]) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, dict):
        errors.append(f"{where}: `color_mappings` must be a mapping")
        return set()
    names: set[str] = set()
    for name, role in value.items():
        if not COLOR_NAME.match(str(name)):
            errors.append(f"{where}: {name!r} is not a COLOR_* token name")
        if not isinstance(role, str) or not role:
            errors.append(f"{where}: {name!r} must map to a non-empty palette role")
        names.add(str(name))
    return names


def check_mappings(
    root: Path, defaults: dict[str, object], errors: list[str], notes: list[str]
) -> dict[str, int]:
    """Check the one group map; return the counts this gate reports."""
    troot = root / TEMPLATES
    if not troot.is_dir():
        errors.append(f"{TEMPLATES}/: missing -- mappings cannot resolve against nothing")
        return {"files": 0, "groups": 0, "variants": 0}

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

    for group_name, entry in data.items():
        group_name = str(group_name)
        if not isinstance(entry, dict):
            errors.append(f"{rel}: group {group_name!r} must be a mapping")
            continue
        groups_count += 1
        group_tokens = _check_color_mappings(
            f"{rel}:{group_name}", entry.get("color_mappings"), errors
        )
        globally_declared |= group_tokens
        declared = set(defaults) | group_tokens

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
            variant_tokens = _check_color_mappings(
                f"{where} ({name})", variant.get("color_mappings"), errors
            )
            globally_declared |= variant_tokens
            allowed = declared | variant_tokens

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
                body = match.group(1).strip()
                if not BARE_TOKEN.fullmatch(match.group(0)):
                    errors.append(
                        f"{template_path.relative_to(root)}: malformed placeholder "
                        f"{match.group(0)!r} (syntax is exactly {{{{COLOR_NAME}}}})"
                    )
                    continue
                used.add(body)
            for token in sorted(used - allowed):
                errors.append(
                    f"{template_path.relative_to(root)}: placeholder {token} is not "
                    f"declared for group {group_name!r} ({rel}) in {DEFAULTS} or its "
                    f"color_mappings"
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
            body = match.group(1).strip()
            if BARE_TOKEN.fullmatch(match.group(0)) and body not in globally_declared:
                errors.append(
                    f"{svg_rel}: placeholder {body} is declared in neither {DEFAULTS} nor "
                    f"any group's color_mappings"
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

    return {
        "files": 1,
        "groups": groups_count,
        "variants": variants_count,
        "svgs": len(all_svgs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the icons corpus")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent

    errors: list[str] = []
    notes: list[str] = []
    load_schema(root, errors)
    defaults = load_defaults(root, errors)
    counts = check_mappings(root, defaults, errors, notes)

    print(
        f"validate-icons: root={root} manifest={MANIFEST} "
        f"groups={counts.get('groups', 0)} variants={counts.get('variants', 0)} "
        f"svgs={counts.get('svgs', 0)} defaults={len(defaults)}"
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
        f"resolves under {TEMPLATES}/, every used placeholder is declared, every SVG parses"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
