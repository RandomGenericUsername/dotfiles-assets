"""Fixture tests for the skins class (mirror of ``scripts/validate-skins.py``).

Run with the repository's development dependencies:

    make test-skins

The corpus itself is validated by the stdlib-only ``make validate-skins`` gate;
these tests add the positive frozen-value assertions and the negative fixtures
that prove the gate actually bites.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "skins" / "schema.json"
MANIFESTS = ROOT / "skins" / "manifests"
TEMPLATE = ROOT / "skins" / "templates" / "ags-bar.gtk.css.j2"
CONTRACTS = ROOT / "skins" / "contracts"
PIN = CONTRACTS / "PIN"
FIXTURES = Path(__file__).parent / "fixtures" / "invalid"
VENDORED = {
    "skin-token.schema.json": "skins/contracts/skin-token.schema.json",
    "skin-manifest.schema.json": "skins/contracts/skin-manifest.schema.json",
}
PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")

_SPEC = importlib.util.spec_from_file_location(
    "validate_skins", ROOT / "scripts" / "validate-skins.py"
)
assert _SPEC and _SPEC.loader
validate_skins = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_skins"] = validate_skins
_SPEC.loader.exec_module(validate_skins)


def load_manifest(name: str) -> dict:
    with (MANIFESTS / f"{name}.toml").open("rb") as handle:
        return tomllib.load(handle)


def schema() -> dict:
    return json.loads(SCHEMA.read_text())


def token_value_map(manifest: dict) -> dict[str, str]:
    groups = schema()["frozen"]["token_groups"]
    return {
        f"SKIN_{token.upper().replace('-', '_')}": manifest[group][token]
        for group, tokens in groups.items()
        for token in tokens
    }


def render(template: str, manifest: dict) -> str:
    rendered = validate_skins.expand_template(
        template, manifest, schema()["frozen"]["token_groups"]
    )
    assert "{{" not in rendered, "unexpanded placeholder in template"
    return rendered


def make_root(
    tmp_path: Path,
    *,
    manifest_override: tuple[str, Path] | None = None,
    template_override: Path | None = None,
    schema_override: Path | None = None,
    drop: str | None = None,
) -> Path:
    root = tmp_path / "repo"
    (root / "skins" / "manifests").mkdir(parents=True)
    (root / "skins" / "templates").mkdir(parents=True)
    shutil.copytree(CONTRACTS, root / "skins" / "contracts")
    shutil.copy2(schema_override or SCHEMA, root / "skins" / "schema.json")
    for path in MANIFESTS.glob("*.toml"):
        if drop is not None and path.stem == drop:
            continue
        shutil.copy2(path, root / "skins" / "manifests" / path.name)
    if manifest_override is not None:
        stem, source = manifest_override
        shutil.copy2(source, root / "skins" / "manifests" / f"{stem}.toml")
    template = template_override or TEMPLATE
    shutil.copy2(template, root / "skins" / "templates" / template.name)
    vocabulary = root / "icons" / "mappings" / "vocabulary.json"
    vocabulary.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "icons" / "mappings" / "vocabulary.json", vocabulary)
    return root


def errors_for(root: Path) -> list[str]:
    errors, _notes, _stats = validate_skins.validate(root)
    return errors


# --------------------------------------------------------------------------- #
# Positive corpus
# --------------------------------------------------------------------------- #


def test_corpus_passes_the_gate() -> None:
    errors, notes, stats = validate_skins.validate(ROOT)
    assert errors == []
    assert stats == {"manifests": 3, "templates": 1, "tokens": 23, "roles": 51}
    assert any("palette roles ==" in note for note in notes)


def pin_metadata() -> tuple[dict[str, str], dict[str, str]]:
    metadata: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for line in PIN.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("sha256 "):
            _label, digest, name = line.split()
            hashes[name] = digest
        elif "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
    return metadata, hashes


def test_schema_vendors_the_pinned_contracts_pair() -> None:
    data = schema()
    assert data["schema_major"] == 1
    canonical = data["canonical"]
    assert canonical["repository"] == "contracts"
    assert set(canonical["paths"]) == {
        "schemas/skin-token.schema.json",
        "schemas/skin-manifest.schema.json",
    }
    assert canonical["vendored"] is True
    assert canonical["tag"] == "v0.5.1"
    assert canonical["pin"] == "skins/contracts/PIN"
    assert canonical["delegates"] == {
        "token": "skins/contracts/skin-token.schema.json",
        "manifest": "skins/contracts/skin-manifest.schema.json",
    }
    metadata, _hashes = pin_metadata()
    assert metadata["contracts"] == canonical["tag"]


def test_vendored_files_match_the_pin_hashes() -> None:
    _metadata, hashes = pin_metadata()
    assert set(hashes) == set(VENDORED)
    for name, rel in VENDORED.items():
        path = ROOT / rel
        assert path.is_file(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == hashes[name]


def test_vendored_canonical_schemas_type_numeric_tokens_as_numbers() -> None:
    token_schema = json.loads(
        (ROOT / VENDORED["skin-token.schema.json"]).read_text()
    )
    manifest_schema = json.loads(
        (ROOT / VENDORED["skin-manifest.schema.json"]).read_text()
    )
    numeric = {
        "radius-panel",
        "radius-card",
        "radius-cell",
        "radius-pill",
        "border-w",
        "gap",
        "title-size",
        "text-size",
        "panel-width",
        "bt-list-spacing",
        "bar-row-height",
        "chip-min",
    }
    for token in numeric:
        ref = token_schema["properties"][token]["$ref"]
        assert ref in {
            "#/definitions/number",
            "#/definitions/nonNegativeNumber",
        }
    assert manifest_schema["definitions"]["number"]["type"] == "number"
    assert manifest_schema["definitions"]["nonNegativeNumber"]["type"] == "number"
    assert manifest_schema["definitions"]["cellPad"]["type"] == "string"


def test_local_schema_delegates_to_the_vendored_pair_not_a_lookalike() -> None:
    data = schema()
    assert "$defs" not in data
    groups = data["frozen"]["token_groups"]
    for group, tokens in groups.items():
        props = data["properties"][group]["properties"]
        for token in tokens:
            spec = props[token]
            assert set(spec) == {"$ref"}, f"{group}.{token}: {spec}"
            assert spec["$ref"].startswith(
                "contracts/skin-manifest.schema.json#"
            ), f"{group}.{token}: {spec['$ref']}"


def test_palette_roles_equal_the_repository_vocabulary() -> None:
    vocabulary = json.loads((ROOT / "icons" / "mappings" / "vocabulary.json").read_text())
    assert schema()["palette"]["roles"] == vocabulary["roles"]
    assert len(schema()["palette"]["roles"]) == 51


def test_manifest_documents_validate_against_the_local_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    from referencing import Registry, Resource

    schema_data = schema()
    jsonschema.Draft202012Validator.check_schema(schema_data)
    registry = Registry().with_resources(
        [
            (rel, Resource.from_contents(json.loads((ROOT / rel).read_text())))
            for rel in VENDORED.values()
        ]
    )
    validator = jsonschema.Draft202012Validator(schema_data, registry=registry)
    for path in MANIFESTS.glob("*.toml"):
        with path.open("rb") as handle:
            manifest = tomllib.load(handle)
        errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
        assert errors == [], [error.message for error in errors]


def test_numeric_string_is_not_a_valid_token_value() -> None:
    manifest = load_manifest("glass")
    manifest["shape"]["radius-panel"] = "12px"
    errors: list[str] = []
    spec = schema()["properties"]["shape"]["properties"]["radius-panel"]
    resolved = validate_skins._deref(  # noqa: SLF001 - the gate's own resolver
        spec, ROOT, "skins/schema.json", "shape.radius-panel", errors
    )
    assert errors == []
    validate_skins._validate_value(  # noqa: SLF001 - the gate's own type check
        resolved, manifest["shape"]["radius-panel"], "shape.radius-panel", errors
    )
    assert any("must be a number" in error for error in errors), errors


def test_every_required_token_is_present_in_every_manifest() -> None:
    groups = schema()["frozen"]["token_groups"]
    for path in MANIFESTS.glob("*.toml"):
        with path.open("rb") as handle:
            manifest = tomllib.load(handle)
        assert manifest["name"] == path.stem
        for group, tokens in groups.items():
            assert set(manifest[group]) == set(tokens), f"{path.name}: {group}"


def test_template_placeholders_are_schema_tokens() -> None:
    expected = set(token_value_map(load_manifest("glass")))
    used = {match.strip() for match in PLACEHOLDER.findall(TEMPLATE.read_text())}
    assert used
    assert used <= expected
    assert not {token for token in used if not token.startswith("SKIN_")}


@pytest.mark.parametrize("name", ["glass", "flat", "paper"])
def test_no_literal_hex_or_transition_in_manifest(name: str) -> None:
    text = (MANIFESTS / f"{name}.toml").read_text()
    assert not HEX.search(text)
    assert "transition" not in text
    assert "animation" not in text


def test_template_has_no_literal_hex_or_transition() -> None:
    text = TEMPLATE.read_text()
    assert not HEX.search(text)
    assert not re.search(r"\btransition\s*:", text)
    assert not re.search(r"\banimation\s*:", text)
    assert "overflow HIDDEN" in text


# --------------------------------------------------------------------------- #
# Frozen v1 values and the glass expansion
# --------------------------------------------------------------------------- #


def test_frozen_manifest_values() -> None:
    glass = load_manifest("glass")
    flat = load_manifest("flat")
    paper = load_manifest("paper")

    assert [glass["shape"][k] for k in ("radius-panel", "radius-card", "radius-cell", "radius-pill")] == [
        12,
        9,
        7,
        20,
    ]
    assert glass["shape"]["border-w"] == 1.5
    assert glass["rhythm"] == {"gap": 8, "cell-pad": "8px 9px"}
    assert glass["surface"] == {
        "bg-panel": "alpha(@surface, 0.94)",
        "bg-card": "alpha(@surface_container_high, 0.18)",
        "border": "@primary",
        "shadow": "none",
        "blur": "none",
    }
    assert glass["ink"]["ink-dim"] == "alpha(@on_surface, 0.62)"
    assert glass["type"] == {
        "font-family": "inherit",
        "title-size": 12.5,
        "text-size": 13,
    }
    assert glass["layout"] == {
        "panel-width": 312,
        "bt-list-spacing": 4,
        "bar-row-height": 0,
        "chip-min": 0,
    }

    assert [flat["shape"][k] for k in ("radius-panel", "radius-card", "radius-cell")] == [
        0,
        0,
        0,
    ]
    assert flat["shape"]["border-w"] == 0
    assert flat["rhythm"] == {"gap": 8, "cell-pad": "7px 8px"}
    assert flat["surface"]["bg-panel"] == "transparent"
    assert flat["surface"]["shadow"] == "none"
    assert flat["layout"]["bar-row-height"] == 28
    assert flat["layout"]["chip-min"] == 48

    assert [paper["shape"][k] for k in ("radius-panel", "radius-card", "radius-cell")] == [
        6,
        4,
        3,
    ]
    assert paper["surface"]["bg-panel"] == "@surface_container_lowest"
    assert paper["surface"]["bg-card"] == "@surface_container_low"
    assert paper["surface"]["border"] == "alpha(@on_surface, 0.22)"
    assert paper["surface"]["shadow"] == "0 10px 28px rgba(0,0,0,0.22)"
    assert paper["layout"] == {
        "panel-width": 312,
        "bt-list-spacing": 6,
        "bar-row-height": 30,
        "chip-min": 52,
    }


def test_glass_expands_to_the_frozen_values() -> None:
    css = render(TEMPLATE.read_text(), load_manifest("glass"))
    assert "background-color: alpha(@surface, 0.94);" in css
    assert "background-color: alpha(@surface_container_high, 0.18);" in css
    assert "border: 1.5px solid @primary;" in css
    assert "box-shadow: none;" in css
    assert "backdrop-filter: none;" in css
    assert "border-radius: 12px;" in css
    assert "padding: 11px;" in css
    assert "padding: 10px 11px;" in css
    assert "padding: 8px 9px;" in css
    assert "border-radius: 9px;" in css
    assert "border-radius: 7px;" in css
    assert "border-radius: 20px;" in css
    assert "min-width: 312px;" in css
    assert "font-size: 12.5px;" in css
    assert "font-size: 13px;" in css


def test_flat_and_paper_expand_with_their_own_surfaces() -> None:
    flat = render(TEMPLATE.read_text(), load_manifest("flat"))
    assert "background-color: transparent;" in flat
    assert "border: 0px solid transparent;" in flat
    assert "border: 0px solid alpha(@on_surface, 0.10);" in flat
    assert "box-shadow: none;" in flat
    assert "padding: 7px 8px;" in flat

    paper = render(TEMPLATE.read_text(), load_manifest("paper"))
    assert "background-color: @surface_container_lowest;" in paper
    assert "background-color: @surface_container_low;" in paper
    assert "border: 1px solid alpha(@on_surface, 0.22);" in paper
    assert "border: 1px solid alpha(@on_surface, 0.10);" in paper
    assert "box-shadow: 0 10px 28px rgba(0,0,0,0.22);" in paper


# --------------------------------------------------------------------------- #
# Negative fixtures
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("fixture", "needle"),
    [
        ("literal-hex.toml", "literal hex colour"),
        ("unknown-role.toml", "not in palette.v1"),
        ("structure.toml", "structure/variant keys are forbidden"),
        ("missing-token.toml", "missing token(s)"),
        ("numeric-string.toml", "must be a number"),
    ],
)
def test_bad_manifest_fails(tmp_path: Path, fixture: str, needle: str) -> None:
    root = make_root(
        tmp_path, manifest_override=("glass", FIXTURES / fixture)
    )
    errors = errors_for(root)
    assert any(needle in error for error in errors), errors


@pytest.mark.parametrize(
    ("fixture", "needle"),
    [
        ("template-transition.j2", "CSS transition"),
        ("template-unknown-placeholder.j2", "is not a token"),
    ],
)
def test_bad_template_fails(tmp_path: Path, fixture: str, needle: str) -> None:
    root = make_root(tmp_path, template_override=FIXTURES / fixture)
    errors = errors_for(root)
    assert any(needle in error for error in errors), errors


def test_missing_manifest_fails(tmp_path: Path) -> None:
    root = make_root(tmp_path, drop="paper")
    errors = errors_for(root)
    assert any("missing required manifest(s) ['paper']" in error for error in errors), errors


def test_vendored_hash_mismatch_fails(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    target = root / "skins" / "contracts" / "skin-token.schema.json"
    target.write_text(target.read_text() + "\n")
    errors = errors_for(root)
    assert any("does not match" in error for error in errors), errors


def test_pinned_tag_disagreement_fails(tmp_path: Path) -> None:
    data = schema()
    data["canonical"]["tag"] = "v0.4.0"
    bad_schema = tmp_path / "schema-tag.json"
    bad_schema.write_text(json.dumps(data))
    root = make_root(tmp_path, schema_override=bad_schema)
    errors = errors_for(root)
    assert any("disagrees with canonical.tag" in error for error in errors), errors
