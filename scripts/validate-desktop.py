#!/usr/bin/env python3
"""validate-desktop -- the `desktop` class contract, asserted against the corpus.

WHAT THIS GATE PROVES (spine AD-10, layer 1 = static, owned by this repo):

  1. EVERY ENTRY IS A DESKTOP ENTRY THE SPEC CAN PARSE. `configparser` reads the
     file (a malformed line, a duplicate key or missing `[Desktop Entry]` group
     fails), and the required keys are present and non-empty: `Type`, `Name`,
     `Exec`, `Icon`, and `TryExec`. `Type` must be one of the three values the
     spec defines. A `.desktop` rofi's drun mode lists but cannot launch is the
     exact silent failure this class exists to prevent.

  2. `Exec` NAMES A DECLARED BINARY. `Exec` is tokenized with the spec's quoting
     rules (double quotes, `\\" \\` \\$ \\\\` escapes) and its field codes
     (`%f %F %u %U %i %c %k %d %D %n %N %v %m`) are stripped. argv[0]'s
     **basename** must appear in the entry's declared `requires` -- which is the
     AD-10 wording ("every Exec/TryExec names a binary in the entry's declared
     requires") and also keeps an ABSOLUTE override (`/usr/bin/code`) honest:
     the name layer 2 resolves is `code`, not a path.

  3. `TryExec` IS PRESENT AND AGREES. The pre-split corpus carried zero
     `TryExec=` keys, so a missing binary left a dead menu entry. It is now
     required, must be declared in `requires`, and must name the same program
     `Exec` launches: a `TryExec` for a different binary would hide a working
     entry (or show a dead one).

  4. `desktop.yaml` AGREES WITH THE `.desktop` SET, EXACTLY, BOTH WAYS. Every
     entry has a record and every record names an entry. Each record declares
     only `{file, requires, optional}`, with binary-name-shaped, disjoint lists;
     the names must occur in that entry's own `Exec` line, so a `requires` entry
     cannot outlive the command it described. `schema_major` is required (spine
     AD-12) and must be 1.

  5. THE SCRIPTS ARE REAL EXECUTABLES. Every file under `desktop/scripts/` is a
     regular file with an 0755-shaped mode and a `#!` shebang. `shellcheck`
     itself runs in the `validate-desktop` make target (it is a shell tool, not
     a Python parse); this script proves the mode and the shebang so a script
     that cannot execute fails even where shellcheck is absent.

WHAT IT DOES NOT PROVE (stated, not implied): that a declared binary is
INSTALLED. That is layer 2 (the consumer's deploy-time resolution) and layer 3
(the consumer's verify), because only a host can answer it (AD-10). Adding a
package check here would make a data repo assert host facts it cannot know.

WHY NO PyYAML. A fresh clone must pass `make gates` with no virtualenv and no
network. This script carries the same deliberately small YAML subset parser as
`validate-catalog.py` / `validate-icons.py` (nested mappings, sequence-of-
mappings, scalar lists, `null`, `[]`, quoted or bare scalars, full-line
comments). Anything outside that subset is an ERROR, never a guess.

Usage: ``python3 scripts/validate-desktop.py [--root REPO_ROOT]``
Exit 0 = the class satisfies all five rules.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
import configparser
import re
import sys
from pathlib import Path

DESKTOP_DIR = "desktop"
APPLICATIONS_DIR = "desktop/applications"
SCRIPTS_DIR = "desktop/scripts"
CONTRACT = "desktop/desktop.yaml"

ENTRY_SUFFIX = ".desktop"
ENTRY_GROUP = "Desktop Entry"
ENTRY_TYPES = ("Application", "Link", "Directory")
CONTRACT_KEYS = ("schema_major", "entries")
RECORD_KEYS = ("file", "requires", "optional")

#: The Exec field codes (freedesktop Desktop Entry spec, "The Exec key"). A bare
#: token that is one of these is a placeholder, not a program argument.
FIELD_CODES = frozenset("fFuUickdDnNvm")

#: A binary name a consumer can resolve with `command -v`. Deliberately
#: conservative: no slashes (a path belongs in Exec, not in requires), no
#: whitespace/glob/metacharacters.
BINARY_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]*$")

#: A single field-code token (`%F`) -- stripped from argv before the checks.
FIELD_CODE_TOKEN = re.compile(r"^%([A-Za-z])$")

#: A field-code-looking run inside a longer token -- an ERROR, because the spec
#: requires field codes to stand alone (a literal `%` is written `%%`).
EMBEDDED_FIELD_CODE = re.compile(r"%(?!%)([A-Za-z])")


class DesktopError(Exception):
    """A violation, with the file and the reason a reader needs to fix it."""


class YamlSubsetError(Exception):
    """`desktop.yaml` used YAML this parser deliberately refuses to guess at."""


# --------------------------------------------------------------------------- #
# The YAML subset (same shape as validate-catalog.py / validate-icons.py)
# --------------------------------------------------------------------------- #


def _scalar(text: str, source: str, lineno: int):
    if text == "":
        raise YamlSubsetError(f"{source}:{lineno}: empty value")
    if text[0] in "\"'":
        if len(text) < 2 or text[-1] != text[0]:
            raise YamlSubsetError(
                f"{source}:{lineno}: unterminated quoted scalar {text!r}"
            )
        return text[1:-1]
    if text[0] in "[{":
        if text == "[]":
            return []
        if text == "{}":
            return {}
        raise YamlSubsetError(
            f"{source}:{lineno}: flow collections other than `[]`/`{{}}` are not "
            f"supported ({text!r}); use a nested block instead"
        )
    if text[0] in "|>&*!%@`":
        raise YamlSubsetError(
            f"{source}:{lineno}: block scalars / anchors / tags are not supported "
            f"({text!r})"
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
        # Two legal shapes: a scalar item (`- code`) or a mapping item
        # (`- file: code.desktop`). The subset refuses to guess, so the presence of
        # a colon decides -- a scalar carrying a colon is YAML this parser does not
        # implement (a mapping value with an inline colon), and is an error.
        if ":" not in body:
            out.append(_scalar(body, source, lineno))
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                raise YamlSubsetError(
                    f"{source}:{lines[i][2]}: a scalar list item cannot have nested "
                    f"content"
                )
            continue
        key, _, rest = body.partition(":")
        if not key.strip():
            raise YamlSubsetError(f"{source}:{lineno}: empty key in a list item")
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
    if i < len(lines) and lines[i][0] > indent:
        raise YamlSubsetError(f"{source}:{lines[i][2]}: unexpected indentation")
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
# Desktop Entry parsing
# --------------------------------------------------------------------------- #


def parse_desktop(path: Path, root: Path) -> configparser.RawConfigParser:
    """Parse one entry per the Desktop Entry spec's syntax; return the parser."""
    rel = _rel(path, root)
    parser = configparser.RawConfigParser(
        interpolation=None,
        delimiters=("=",),
        comment_prefixes=("#",),
        strict=True,
    )
    # Key names are case-SENSITIVE in the spec (`Exec` is not `exec`).
    parser.optionxform = str
    try:
        parser.read_string(path.read_text(), source=rel)
    except configparser.MissingSectionHeaderError as exc:
        raise DesktopError(
            f"{rel}: no group header — a desktop entry starts with {ENTRY_GROUP!r} ({exc})"
        ) from exc
    except configparser.DuplicateOptionError as exc:
        raise DesktopError(f"{rel}: a key is declared twice ({exc})") from exc
    except configparser.Error as exc:  # malformed line, duplicate group, ...
        raise DesktopError(f"{rel}: not a parseable desktop entry ({exc})") from exc
    if not parser.has_section(ENTRY_GROUP):
        raise DesktopError(
            f"{rel}: missing the {ENTRY_GROUP!r} group — every other key is invisible "
            f"to a launcher without it"
        )
    return parser


def parse_exec(value: str) -> list[str]:
    """Tokenize an `Exec` value per the spec, dropping field-code arguments.

    Quoting: arguments may be wrapped in double quotes; inside them the only
    escapes are `\\"`, `` \\` ``, `\\$` and `\\\\`. Field codes must be standalone
    arguments and are removed, so argv[0] is the program, never `%F`.
    """
    tokens: list[str] = []
    current: list[str] = []
    started = False
    in_quotes = False
    i = 0
    while i < len(value):
        char = value[i]
        if in_quotes:
            if char == "\\" and i + 1 < len(value) and value[i + 1] in '"`$\\':
                current.append(value[i + 1])
                i += 2
                continue
            if char == '"':
                in_quotes = False
                i += 1
                continue
            current.append(char)
            i += 1
            continue
        if char == '"':
            in_quotes = True
            started = True
            i += 1
            continue
        if char == " ":
            if started or current:
                tokens.append("".join(current))
                current = []
                started = False
            i += 1
            continue
        current.append(char)
        started = True
        i += 1
    if in_quotes:
        raise DesktopError(f"Exec={value!r}: unterminated double quote")
    if started or current:
        tokens.append("".join(current))

    argv: list[str] = []
    for token in tokens:
        match = FIELD_CODE_TOKEN.match(token)
        if match:
            if match.group(1) not in FIELD_CODES:
                raise DesktopError(
                    f"Exec={value!r}: {token!r} is not a field code — an unknown "
                    f"placeholder would be passed through as a literal argument"
                )
            continue
        embedded = EMBEDDED_FIELD_CODE.search(token)
        if embedded and embedded.group(1) in FIELD_CODES:
            raise DesktopError(
                f"Exec={value!r}: field code {embedded.group(0)!r} is embedded in "
                f"{token!r} — the spec requires field codes to be standalone arguments"
            )
        argv.append(token)
    if not argv:
        raise DesktopError(
            f"Exec={value!r}: names no program (only field codes or whitespace)"
        )
    return argv


def basename(program: str) -> str:
    return program.rsplit("/", 1)[-1]


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DesktopError(message)


def _string_list(value: object, where: str, *, allow_empty: bool) -> list[str]:
    _require(
        isinstance(value, list) and all(isinstance(item, str) for item in value),
        f"{where} must be a list of binary names",
    )
    names = list(value)  # type: ignore[arg-type]
    if not allow_empty:
        _require(bool(names), f"{where} is empty — every entry launches something")
    _require(len(set(names)) == len(names), f"{where} names a binary twice")
    for name in names:
        _require(
            bool(BINARY_NAME.match(name)),
            f"{where} name {name!r} is not a binary name (no path, no whitespace, "
            f"no shell metacharacters)",
        )
    return names


def load_contract(root: Path, errors: list[str]) -> dict[str, dict[str, object]]:
    """Parse `desktop.yaml`; return `{file: record}` for the cross-checks."""
    path = root / CONTRACT
    if not path.is_file():
        errors.append(
            f"{CONTRACT}: missing — layer 2 resolves these lists before it deploys, "
            f"so an entry without a record has no deploy contract"
        )
        return {}
    try:
        data = parse_yaml_subset(path.read_text(), CONTRACT)
    except YamlSubsetError as exc:
        errors.append(str(exc))
        return {}

    for key in data:
        if key not in CONTRACT_KEYS:
            errors.append(f"{CONTRACT}: unknown top-level key {key!r}; the contract is {list(CONTRACT_KEYS)}")
    major = data.get("schema_major")
    if not isinstance(major, int) or major < 1:
        errors.append(f"{CONTRACT}: missing an integer `schema_major` >= 1 (spine AD-12)")
    elif major != 1:
        errors.append(
            f"{CONTRACT}: schema_major {major} is not 1 — this validator implements the "
            f"version-1 shape; a new major needs a new contract and a consumer window"
        )

    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        errors.append(f"{CONTRACT}: `entries` must be a list of records")
        return {}
    if not raw_entries:
        errors.append(f"{CONTRACT}: `entries` is empty — the class ships six entries")

    records: dict[str, dict[str, object]] = {}
    for index, record in enumerate(raw_entries):
        where = f"{CONTRACT}: entries[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{where} must be a mapping")
            continue
        unknown = sorted(set(record) - set(RECORD_KEYS))
        if unknown:
            errors.append(
                f"{where} has unknown key(s) {unknown}; a record is exactly "
                f"{list(RECORD_KEYS)} — a key nothing reads is a rule nothing enforces"
            )
            continue
        missing = [key for key in RECORD_KEYS if key not in record]
        if missing:
            errors.append(f"{where} is missing {missing}")
            continue
        filename = record["file"]
        if (
            not isinstance(filename, str)
            or not filename.endswith(ENTRY_SUFFIX)
            or "/" in filename
        ):
            errors.append(
                f"{where}.file must be a bare *{ENTRY_SUFFIX} file name, got {filename!r}"
            )
            continue
        if filename in records:
            errors.append(f"{where}.file {filename!r} is declared twice")
            continue
        if not (root / APPLICATIONS_DIR / filename).is_file():
            errors.append(
                f"{where}.file {filename!r} has no entry at {APPLICATIONS_DIR}/{filename}"
            )
            continue
        try:
            requires = _string_list(record["requires"], f"{where}.requires", allow_empty=False)
            optional = _string_list(record["optional"], f"{where}.optional", allow_empty=True)
        except DesktopError as exc:
            errors.append(str(exc))
            continue
        overlap = sorted(set(requires) & set(optional))
        if overlap:
            errors.append(f"{where}: {overlap} appear in both `requires` and `optional`")
            continue
        records[filename] = {"requires": requires, "optional": optional}
    return records


def check_entry(
    path: Path,
    root: Path,
    record: dict[str, object],
    errors: list[str],
) -> bool:
    """Apply rules 1-4 to one entry; return True when it carried a valid TryExec."""
    rel = _rel(path, root)
    try:
        parser = parse_desktop(path, root)
    except DesktopError as exc:
        errors.append(str(exc))
        return False

    values: dict[str, str] = {}
    try:
        for key in ("Type", "Name", "Exec", "Icon", "TryExec"):
            raw = parser.get(ENTRY_GROUP, key, fallback=None)
            if raw is None or not raw.strip():
                raise DesktopError(
                    f"{rel}: missing or empty {key} — "
                    + {
                        "Type": "a launcher needs the entry type",
                        "Name": "an unnamed entry is unsearchable",
                        "Exec": "an entry with no command launches nothing",
                        "Icon": "an empty Icon shows a broken/missing glyph",
                        "TryExec": "without TryExec a missing binary still lists a dead entry",
                    }[key]
                )
            values[key] = raw.strip()
    except DesktopError as exc:
        errors.append(str(exc))
        return False

    entry_type = values["Type"]
    if entry_type not in ENTRY_TYPES:
        errors.append(
            f"{rel}: Type {entry_type!r} is not one of {list(ENTRY_TYPES)}"
        )
        return False

    try:
        argv = parse_exec(values["Exec"])
    except DesktopError as exc:
        errors.append(f"{rel}: {exc}")
        return False

    requires = list(record["requires"])  # type: ignore[arg-type]
    optional = list(record["optional"])  # type: ignore[arg-type]
    program = basename(argv[0])
    try_exec = basename(values["TryExec"])

    if program not in requires:
        errors.append(
            f"{rel}: Exec launches {program!r} (argv[0] {argv[0]!r}), which is not in "
            f"its declared requires {requires} — layer 2 resolves that list, so an "
            f"undeclared launcher is never checked on a host"
        )
    if try_exec not in requires:
        errors.append(
            f"{rel}: TryExec {values['TryExec']!r} is not in its declared requires "
            f"{requires} — the binary that decides whether the entry is viable must be "
            f"one the consumer resolves"
        )
    if try_exec != program:
        errors.append(
            f"{rel}: TryExec {values['TryExec']!r} does not name the program Exec "
            f"launches ({program!r}) — a TryExec for another binary either hides a "
            f"working entry or shows a dead one"
        )

    # The declared names must come from this entry's own command line (rule 4):
    # argv[0], TryExec, or a non-flag argument (the payload a wrapper runs).
    referenced = {program, try_exec}
    referenced.update(token for token in argv[1:] if not token.startswith("-"))
    for name in requires + optional:
        if name not in referenced:
            errors.append(
                f"{rel}: {name!r} is declared in desktop.yaml but does not occur in this "
                f"entry's Exec line ({argv}) — the record must describe the command"
            )
    return True


def check_scripts(root: Path, errors: list[str]) -> list[Path]:
    base = root / SCRIPTS_DIR
    if not base.is_dir():
        errors.append(f"{SCRIPTS_DIR}/: missing — the class ships its helper scripts")
        return []
    scripts = sorted(p for p in base.iterdir() if p.is_file() and p.name != ".gitkeep")
    for path in scripts:
        rel = _rel(path, root)
        mode = path.stat().st_mode
        if not mode & 0o111:
            errors.append(
                f"{rel}: not executable (mode {mode & 0o777:04o}) — a keybind that runs "
                f"it would fail; the corpus ships executables"
            )
        head = path.open("rb").read(2)
        if head != b"#!":
            errors.append(f"{rel}: no `#!` shebang — not a runnable script")
    return scripts


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the desktop class contract")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    applications = root / APPLICATIONS_DIR
    if not applications.is_dir():
        print(f"validate-desktop: FAIL -- {APPLICATIONS_DIR}/ is missing at {root}")
        return 1

    errors: list[str] = []
    records = load_contract(root, errors)

    entries = sorted(applications.glob(f"*{ENTRY_SUFFIX}"))
    on_disk = {path.name for path in entries}
    for missing in sorted(on_disk - set(records)):
        errors.append(
            f"{APPLICATIONS_DIR}/{missing}: no record in {CONTRACT} — layer 2 would "
            f"deploy an entry it never resolved"
        )
    for orphan in sorted(set(records) - on_disk):
        errors.append(f"{CONTRACT}: record {orphan!r} names no entry on disk")

    with_tryexec = 0
    requires_total = 0
    optional_total = 0
    for path in entries:
        record = records.get(path.name)
        if record is None:
            # The missing record is already reported above; still parse the file so
            # a malformed entry is named rather than buried behind the missing record.
            try:
                parse_desktop(path, root)
            except DesktopError as exc:
                errors.append(str(exc))
            continue
        if check_entry(path, root, record, errors):
            with_tryexec += 1
        requires_total += len(record["requires"])  # type: ignore[arg-type]
        optional_total += len(record["optional"])  # type: ignore[arg-type]

    scripts = check_scripts(root, errors)

    print(
        f"validate-desktop: root={root} entries={len(entries)} "
        f"with_TryExec={with_tryexec} contract_records={len(records)} "
        f"requires={requires_total} optional={optional_total} scripts={len(scripts)}"
    )
    print(
        "validate-desktop: every entry parses (Desktop Entry: Type, Name, Exec, Icon) "
        "and Exec argv[0] names a declared binary"
    )
    print(
        "validate-desktop: NOTE -- shellcheck runs in the `validate-desktop` make "
        "target (a shell tool, not a Python parse); this script proves the script "
        "modes and shebangs"
    )

    if errors:
        print(f"validate-desktop: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("validate-desktop: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
