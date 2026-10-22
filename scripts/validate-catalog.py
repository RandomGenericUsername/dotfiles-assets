#!/usr/bin/env python3
"""validate-catalog -- the corpus envelope: catalog <-> class dirs, schema JSON, AD-11.

WHAT THIS GATE PROVES, and why each part is separate:

  1. CATALOG <-> DIRS AGREE. `catalog.yaml` names five classes; the tree holds
     five class directories. Either side alone is a claim: a class directory with
     no catalog entry is undocumented corpus, and a catalog entry with no
     directory is a path every consumer will address and nothing will answer. Both
     fail here. Subdirectories are checked the same way, because a class's inner
     layout is part of the paths consumers read.

  2. SCHEMA CONTRACTS ARE WELL-FORMED AND VERSIONED. Every schema-bearing class
     names a contract file; that file must parse, carry an integer `schema_major`
     (spine AD-12), and agree with the `schema_major` the catalog declares. A
     contract is JSON (`icons/schema.json`, every `*.vars.schema.json`) or YAML
     (`desktop/desktop.yaml`, the per-entry `requires`/`optional` record a consumer
     resolves before deploy): both are read with the same strict subset, so the
     version rule is the same rule. Every `*.vars.schema.json` under a schema-bearing
     class is checked too, so a template's contract cannot rot just because the
     catalog was not edited.

     The `templates` class bears one contract PER TEMPLATE, so its catalog
     `schema` value is the GLOB `templates/**/*.vars.schema.json` rather than one
     arbitrary representative. A glob must match at least one file, every match
     must live under the declaring class, and every match's `schema_major` must
     equal the catalog's — the class-level version is a statement about the whole
     set, and half a set at `schema_major: 2` is exactly the drift this catches.

  3. GENERATED AND MUTABLE ARTIFACTS ARE ABSENT (spine AD-11). `icons.json`,
     `settings.toml`, a rendered `kitty.conf` / `btop.conf` / `.zshrc`, and a
     mutable `active-theme` are produced by the consumer or by the runtime.
     Committing one makes this repository a second source of truth that drifts by
     construction. This is mechanical on purpose: a convention nobody executes is
     a convention that gets broken by the first hurried commit.

WHAT IT DOES NOT PROVE (stated, not implied): that the CORPUS is valid. The class
validators carry that, each landing with its corpus: `validate-icons`,
`validate-content`, `validate-templates` and `validate-desktop` all exist at this
tag. A validator with no corpus is a rule nobody has seen work.

WHY NO PyYAML. A fresh clone must pass `make gates` with no virtualenv and no
network: a validation verb that requires `uv sync` first is not a fresh-clone verb.
So this script parses the deliberately small YAML subset `catalog.yaml` and the
YAML contract (`desktop/desktop.yaml`) actually use -- nested mappings, sequence
items that are either scalars (`- hypr`) or mappings (`- file: x.desktop`),
scalar lists, `null`, `[]`, quoted or bare scalars, full line comments. Anything
outside that subset (tabs, block scalars, flow collections, anchors, multi-line
values) is a hard ERROR rather than a guess, so a future edit cannot silently
change what this gate checked.

Usage: ``python3 scripts/validate-catalog.py [--root REPO_ROOT]``
Exit 0 = the envelope is sound. Exit 1 = at least one violation, listed by path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CATALOG = "catalog.yaml"

# The five class names are a CONTRACT, not a convenience: a class directory may
# not be renamed and a file may not move between classes without a MAJOR tag,
# because consumers address class paths literally (spine AD-3/AD-4). Hard-coding
# the set is what makes a rename fail here instead of in five consumers.
CLASSES = ("icons", "templates", "configs", "content", "desktop")

CLASS_FIELDS = ("dir", "subdirs", "schema", "schema_major", "contents")

# AD-11: never assets. Matched on the exact file name only -- `btop.conf.j2` is a
# template (allowed), `btop.conf` is rendered output (forbidden), and conflating
# the two would either ban the class or wave the artifact through.
FORBIDDEN_BASENAMES = (
    "icons.json",
    "settings.toml",
    "kitty.conf",
    "btop.conf",
    ".zshrc",
    "active-theme",
)

# Walked past: VCS metadata, the ticket worktrees (a checkout of this same repo,
# so its artifacts would be reported twice), dependency trees, bytecode.
SKIP_DIRS = {".git", ".worktrees", ".venv", "node_modules", "__pycache__"}

# A catalog value may not name a deployment path (AD-2/AD-6). These patterns are
# the shapes a destination actually takes, not a word list of banned words.
DESTINATION_PATTERNS = (
    re.compile(r"^~"),
    re.compile(r"^/"),
    re.compile(r"\.local/share"),
    re.compile(r"(^|[\s/])spine([\s/]|$)"),
)

CLASS_DIR_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
TAG = re.compile(r"^v\d+\.\d+\.\d+$")


class CatalogError(Exception):
    """A violation, with the path/reason a reader needs to fix it."""


class YamlSubsetError(Exception):
    """`catalog.yaml` used YAML this parser deliberately refuses to guess at."""


# --------------------------------------------------------------------------- #
# The YAML subset
# --------------------------------------------------------------------------- #


def _scalar(text: str, lineno: int):
    """Parse one scalar, or raise if it is outside the supported subset."""
    if text == "":
        raise YamlSubsetError(f"line {lineno}: empty value")
    if text[0] in "\"'":
        if len(text) < 2 or text[-1] != text[0]:
            raise YamlSubsetError(f"line {lineno}: unterminated quoted scalar {text!r}")
        return text[1:-1]
    if text[0] in "[{":
        if text == "[]":
            return []
        if text == "{}":
            return {}
        raise YamlSubsetError(
            f"line {lineno}: flow collections other than `[]`/`{{}}` are not supported "
            f"({text!r}); use a nested block instead"
        )
    if text[0] in "|>&*!%@`":
        raise YamlSubsetError(
            f"line {lineno}: block scalars / anchors / tags are not supported ({text!r})"
        )
    if text in ("null", "~"):
        return None
    if text in ("true", "false"):
        return text == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if ": " in text:
        raise YamlSubsetError(
            f"line {lineno}: a nested mapping must be a block, not inline ({text!r})"
        )
    return text


def _block(lines: list[tuple[int, str, int]], i: int, indent: int):
    """Parse the block starting at `lines[i]` with `indent`; return (value, next i)."""
    if lines[i][1].startswith("- "):
        return _sequence(lines, i, indent)
    return _mapping(lines, i, indent)


def _mapping(lines: list[tuple[int, str, int]], i: int, indent: int):
    out: dict[str, object] = {}
    while i < len(lines) and lines[i][0] == indent:
        text, lineno = lines[i][1], lines[i][2]
        if text.startswith("- "):
            raise YamlSubsetError(f"line {lineno}: list item where a key was expected")
        key, sep, rest = text.partition(":")
        if not sep or not key.strip():
            raise YamlSubsetError(f"line {lineno}: expected `key: value`, got {text!r}")
        key, rest = key.strip(), rest.strip()
        if key in out:
            raise YamlSubsetError(f"line {lineno}: duplicate key {key!r}")
        i += 1
        if rest:
            out[key] = _scalar(rest, lineno)
            continue
        if i < len(lines) and lines[i][0] > indent:
            if lines[i][0] != indent + 2:
                raise YamlSubsetError(
                    f"line {lines[i][2]}: expected exactly two spaces of indent "
                    f"under {key!r}, got {lines[i][0] - indent}"
                )
            out[key], i = _block(lines, i, indent + 2)
        else:
            raise YamlSubsetError(f"line {lineno}: key {key!r} has no value")
    if i < len(lines) and lines[i][0] > indent:
        raise YamlSubsetError(f"line {lines[i][2]}: unexpected indentation")
    return out, i


def _sequence(lines: list[tuple[int, str, int]], i: int, indent: int):
    out: list[object] = []
    while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
        text, lineno = lines[i][1], lines[i][2]
        item = text[2:].strip()
        if item == "":
            raise YamlSubsetError(f"line {lineno}: empty list item")
        if item.startswith("- "):
            raise YamlSubsetError(f"line {lineno}: nested sequences are not supported")
        # A scalar item (`- hypr`) or a mapping item (`- file: code.desktop`). The
        # colon decides, because the subset refuses to guess: a scalar that carries
        # a colon is an inline mapping this parser does not implement.
        if ":" not in item:
            out.append(_scalar(item, lineno))
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                raise YamlSubsetError(
                    f"line {lines[i][2]}: a scalar list item cannot have nested content"
                )
            continue
        key, _, rest = item.partition(":")
        if not key.strip():
            raise YamlSubsetError(f"line {lineno}: empty key in a list item")
        record: dict[str, object] = {}
        key, rest = key.strip(), rest.strip()
        i += 1
        if rest:
            record[key] = _scalar(rest, lineno)
        else:
            if i < len(lines) and lines[i][0] > indent:
                if lines[i][0] != indent + 2:
                    raise YamlSubsetError(
                        f"line {lines[i][2]}: expected exactly two spaces of indent "
                        f"under {key!r}, got {lines[i][0] - indent}"
                    )
                record[key], i = _block(lines, i, indent + 2)
            else:
                raise YamlSubsetError(f"line {lineno}: key {key!r} has no value")
        while i < len(lines) and lines[i][0] > indent:
            if lines[i][0] != indent + 2:
                raise YamlSubsetError(
                    f"line {lines[i][2]}: a sequence item's keys must sit at "
                    f"{indent + 2} spaces"
                )
            continuation, i = _mapping(lines, i, indent + 2)
            for ckey, cvalue in continuation.items():
                if ckey in record:
                    raise YamlSubsetError(
                        f"line {lines[i - 1][2]}: duplicate key {ckey!r} in a list item"
                    )
                record[ckey] = cvalue
        out.append(record)
    if i < len(lines) and lines[i][0] > indent:
        raise YamlSubsetError(f"line {lines[i][2]}: unexpected indentation")
    return out, i


def parse_yaml_subset(text: str, source: str) -> dict:
    """Parse `catalog.yaml`'s subset, or raise YamlSubsetError naming the line."""
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
    value, i = _block(lines, 0, 0)
    if i != len(lines):
        raise YamlSubsetError(f"{source}:{lines[i][2]}: trailing content")
    if not isinstance(value, dict):
        raise YamlSubsetError(f"{source}: top level must be a mapping")
    return value


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def _scalars(value, path: str):
    """Yield every (dotted key path, scalar) under `value`, for the destination scan."""
    if isinstance(value, dict):
        for key, inner in value.items():
            yield from _scalars(inner, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _scalars(inner, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def check_catalog(root: Path, catalog: dict, errors: list[str]) -> dict:
    """Check the catalog document itself; return the class mapping for later checks."""
    for key in ("catalog", "repo", "tag", "classes"):
        if key not in catalog:
            errors.append(f"{CATALOG}: missing top-level key {key!r}")
    if not isinstance(catalog.get("catalog"), int):
        errors.append(f"{CATALOG}: `catalog` must be an integer schema version")
    if not isinstance(catalog.get("repo"), str) or not catalog.get("repo"):
        errors.append(f"{CATALOG}: `repo` must name the repository")
    tag = catalog.get("tag")
    if not isinstance(tag, str) or not TAG.match(tag):
        errors.append(f"{CATALOG}: `tag` must be a released vX.Y.Z tag, got {tag!r}")

    for key, value in _scalars(catalog, ""):
        for pattern in DESTINATION_PATTERNS:
            if pattern.search(value):
                errors.append(
                    f"{CATALOG}: {key} names a deployment path ({value!r}) -- this file "
                    f"is repo-local inventory; the consumer's manifest owns destinations"
                )

    classes = catalog.get("classes")
    if not isinstance(classes, dict):
        errors.append(f"{CATALOG}: `classes` must be a mapping")
        return {}

    declared = tuple(classes)
    if set(declared) != set(CLASSES):
        missing = [c for c in CLASSES if c not in classes]
        extra = [c for c in declared if c not in CLASSES]
        errors.append(
            f"{CATALOG}: class names must be exactly {list(CLASSES)}; "
            f"missing={missing} unexpected={extra} (a rename is a MAJOR change)"
        )
    return classes


def check_class_dirs(root: Path, classes: dict, errors: list[str]) -> int:
    """Check each class directory + its declared subdirs; return the dir count."""
    checked = 0
    for name, entry in classes.items():
        if not isinstance(entry, dict):
            errors.append(f"{CATALOG}: class {name!r} must be a mapping")
            continue
        missing_fields = [f for f in CLASS_FIELDS if f not in entry]
        if missing_fields:
            errors.append(f"{CATALOG}: class {name!r} is missing {missing_fields}")
            continue
        extra_fields = [f for f in entry if f not in CLASS_FIELDS]
        if extra_fields:
            errors.append(
                f"{CATALOG}: class {name!r} has unknown field(s) {extra_fields}; this "
                f"parser only understands {list(CLASS_FIELDS)} and will not ignore a field "
                f"it cannot check"
            )

        directory = entry["dir"]
        if directory != name:
            errors.append(
                f"{CATALOG}: class {name!r} declares dir {directory!r}; the class name IS "
                f"the directory name (consumers address it literally)"
            )
        class_dir = root / str(directory)
        if not class_dir.is_dir():
            errors.append(f"{directory}/: catalog names this class but the directory is absent")
            continue
        checked += 1

        subdirs = entry["subdirs"]
        if not isinstance(subdirs, list) or not all(isinstance(s, str) for s in subdirs):
            errors.append(f"{CATALOG}: class {name!r} `subdirs` must be a list of names")
            continue
        on_disk = sorted(p.name for p in class_dir.iterdir() if p.is_dir())
        for sub in subdirs:
            if not CLASS_DIR_NAME.match(sub):
                errors.append(f"{CATALOG}: class {name!r} subdir {sub!r} is not a valid name")
            if not (class_dir / sub).is_dir():
                errors.append(f"{directory}/{sub}/: declared in the catalog but absent")
            else:
                checked += 1
        for stray in sorted(set(on_disk) - set(subdirs)):
            errors.append(
                f"{directory}/{stray}/: directory not declared in the catalog "
                f"(declare it, or remove it -- an undeclared path is corpus nothing tracks)"
            )

        # A class dir or subdir must hold SOMETHING: either corpus, or the
        # `.gitkeep` that says "empty on purpose in this tag". A directory git
        # cannot keep is a directory a consumer will find missing after a clone.
        for where in [class_dir] + [class_dir / s for s in subdirs]:
            entries = [p for p in where.iterdir() if p.name != ".gitkeep"]
            if not entries and not (where / ".gitkeep").exists():
                errors.append(
                    f"{where.relative_to(root)}/: empty with no .gitkeep -- it will not "
                    f"survive a clone"
                )
    return checked


def _check_vars_schema(path: Path, data: dict, errors: list[str]) -> None:
    """Check the `*.vars.schema.json` envelope (the deep rules need the corpus)."""
    rel = path.name
    if not isinstance(data.get("schema_major"), int):
        errors.append(f"{rel}: missing an integer `schema_major` (spine AD-12)")
    required, optional = data.get("required"), data.get("optional")
    if not isinstance(required, list) or not all(isinstance(n, str) for n in required):
        errors.append(f"{rel}: `required` must be a list of variable names")
        required = []
    if not isinstance(optional, list) or not all(isinstance(n, str) for n in optional):
        errors.append(f"{rel}: `optional` must be a list of variable names")
        optional = []
    overlap = sorted(set(required) & set(optional))
    if overlap:
        errors.append(f"{rel}: {overlap} appear in both `required` and `optional`")
    properties = data.get("properties")
    if properties is not None and not isinstance(properties, dict):
        errors.append(f"{rel}: `properties` must be a mapping")
    elif isinstance(properties, dict):
        undeclared = [n for n in list(required) + list(optional) if n not in properties]
        if undeclared:
            errors.append(f"{rel}: {undeclared} have no `properties` entry (no type)")
    if not isinstance(data.get("template"), str) or not data.get("template"):
        errors.append(f"{rel}: missing the sibling `template` file name")


def check_schemas(root: Path, classes: dict, errors: list[str]) -> list[tuple[str, int, str]]:
    """Check every schema-bearing class; return (class, schema_major, path) triples."""
    bearing: list[tuple[str, int, str]] = []
    for name, entry in classes.items():
        if not isinstance(entry, dict) or "schema" not in entry:
            continue
        schema_rel, major = entry.get("schema"), entry.get("schema_major")
        if major is None:
            if schema_rel is not None:
                errors.append(
                    f"{CATALOG}: class {name!r} declares a schema but no `schema_major`"
                )
            continue
        if not isinstance(major, int) or major < 1:
            errors.append(f"{CATALOG}: class {name!r} `schema_major` must be an integer >= 1")
            continue
        if not isinstance(schema_rel, str) or not schema_rel:
            errors.append(
                f"{CATALOG}: class {name!r} bears a schema_major but names no schema file"
            )
            continue
        if not schema_rel.startswith(f"{name}/"):
            errors.append(
                f"{CATALOG}: class {name!r} schema {schema_rel!r} is outside its class dir"
            )
        # One contract per member (templates) is expressed as a glob; one contract
        # for the class (icons) as a path. A glob is not a wildcard escape hatch:
        # it must match, and every match is held to the same version.
        if any(ch in schema_rel for ch in "*?["):
            paths = sorted(root.glob(schema_rel))
            if not paths:
                errors.append(f"{schema_rel}: named by the catalog but matches no file")
                continue
        else:
            paths = [root / schema_rel]
        for path in paths:
            rel = str(path.relative_to(root))
            if not rel.startswith(f"{name}/"):
                errors.append(
                    f"{CATALOG}: class {name!r} schema {rel!r} is outside its class dir"
                )
            if not path.is_file():
                errors.append(f"{rel}: named by the catalog but absent")
                continue
            try:
                if path.suffix in (".yaml", ".yml"):
                    data = parse_yaml_subset(path.read_text(), rel)
                else:
                    data = json.loads(path.read_text())
            except (json.JSONDecodeError, YamlSubsetError) as exc:
                errors.append(f"{rel}: not a parseable contract ({exc})")
                continue
            if not isinstance(data, dict):
                errors.append(f"{rel}: a schema document must be a JSON object")
                continue
            if not isinstance(data.get("schema_major"), int):
                errors.append(f"{rel}: missing an integer `schema_major` (spine AD-12)")
            elif data["schema_major"] != major:
                errors.append(
                    f"{rel}: schema_major {data['schema_major']} disagrees with the "
                    f"catalog's {major}"
                )
            if rel.endswith(".vars.schema.json"):
                _check_vars_schema(path, data, errors)
        bearing.append((name, major, schema_rel))

    # Every vars schema in a schema-bearing class is a contract, catalogued or not:
    # S3 adds one per template, and a contract the catalog never mentions must not
    # therefore go unchecked.
    for name, _major, _schema in bearing:
        class_dir = root / name
        if not class_dir.is_dir():
            continue
        for path in sorted(class_dir.rglob("*.vars.schema.json")):
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError as exc:
                errors.append(f"{path.relative_to(root)}: invalid JSON ({exc})")
                continue
            if isinstance(data, dict):
                _check_vars_schema(path, data, errors)
    return bearing


def check_ad11(root: Path, errors: list[str]) -> int:
    """Fail on any generated/mutable artifact in the tree; return files examined."""
    examined = 0
    forbidden = set(FORBIDDEN_BASENAMES)
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_dir():
            continue
        examined += 1
        if path.name in forbidden:
            errors.append(
                f"{rel}: generated or mutable artifact (spine AD-11) -- it is produced by "
                f"the consumer or the runtime and would drift here by construction"
            )
    return examined


# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the assets corpus envelope")
    parser.add_argument(
        "--root", default=None, help="repo root (default: parent of scripts/)"
    )
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    catalog_path = root / CATALOG
    if not catalog_path.is_file():
        print(f"validate-catalog: FAIL -- {CATALOG} is missing at {root}")
        return 1
    try:
        catalog = parse_yaml_subset(catalog_path.read_text(), CATALOG)
    except YamlSubsetError as exc:
        print(f"validate-catalog: FAIL -- {exc}")
        return 1

    errors: list[str] = []
    classes = check_catalog(root, catalog, errors)
    dir_count = check_class_dirs(root, classes, errors)
    bearing = check_schemas(root, classes, errors)
    examined = check_ad11(root, errors)

    print(
        f"validate-catalog: root={root} repo={catalog.get('repo')} "
        f"tag={catalog.get('tag')} catalog_schema={catalog.get('catalog')}"
    )
    print(
        f"validate-catalog: classes ({len(classes)}): " + " ".join(classes)
        if classes
        else "validate-catalog: classes (0)"
    )
    majors = ", ".join(f"{n}={m} ({s})" for n, m, s in bearing)
    print(f"validate-catalog: schema_major ({len(bearing)}): {majors or '(none)'}")
    non_bearing = [n for n in classes if n not in {b[0] for b in bearing}]
    print(
        "validate-catalog: no schema_major (null, deliberate): "
        + (" ".join(non_bearing) or "(none)")
    )
    print(
        f"validate-catalog: catalog <-> class dirs: {len(classes)} classes, "
        f"{dir_count} directories checked"
    )
    print(
        f"validate-catalog: AD-11 absence: {examined} files scanned for "
        + ", ".join(FORBIDDEN_BASENAMES)
    )

    if errors:
        print(f"validate-catalog: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("validate-catalog: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
