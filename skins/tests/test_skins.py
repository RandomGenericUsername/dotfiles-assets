"""Fixture tests for the skins class (mirror of ``scripts/validate-skins.py``).

Run with the repository's development dependencies:

    make test-skins

The corpus itself is validated by the stdlib-only ``make validate-skins`` gate;
these tests add the positive frozen-value assertions and the negative fixtures
that prove the gate actually bites.
"""

from __future__ import annotations

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
FIXTURES = Path(__file__).parent / "fixtures" / "invalid"
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
    rendered = template
    for placeholder, value in token_value_map(manifest).items():
        rendered = rendered.replace("{{" + placeholder + "}}", value)
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


def test_schema_points_at_contracts_without_a_false_vendoring_claim() -> None:
    data = schema()
    assert data["schema_major"] == 1
    canonical = data["canonical"]
    assert canonical["repository"] == "contracts"
    assert set(canonical["paths"]) == {
        "schemas/skin-token.schema.json",
        "schemas/skin-manifest.schema.json",
    }
    assert canonical["tag"] is None
    assert canonical["vendored"] is False


def test_palette_roles_equal_the_repository_vocabulary() -> None:
    vocabulary = json.loads((ROOT / "icons" / "mappings" / "vocabulary.json").read_text())
    assert schema()["palette"]["roles"] == vocabulary["roles"]
    assert len(schema()["palette"]["roles"]) == 51


def test_manifest_documents_validate_against_the_local_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema_data = schema()
    jsonschema.Draft202012Validator.check_schema(schema_data)
    validator = jsonschema.Draft202012Validator(schema_data)
    for path in MANIFESTS.glob("*.toml"):
        with path.open("rb") as handle:
            manifest = tomllib.load(handle)
        errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
        assert errors == [], [error.message for error in errors]


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
        "12px",
        "9px",
        "7px",
        "20px",
    ]
    assert glass["shape"]["border-w"] == "1.5px"
    assert glass["rhythm"] == {"gap": "8px", "cell-pad": "8px 9px"}
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
        "title-size": "12.5px",
        "text-size": "13px",
    }
    assert glass["layout"] == {
        "panel-width": "312px",
        "bt-list-spacing": "4px",
        "bar-row-height": "0px",
        "chip-min": "0px",
    }

    assert [flat["shape"][k] for k in ("radius-panel", "radius-card", "radius-cell")] == [
        "0px",
        "0px",
        "0px",
    ]
    assert flat["shape"]["border-w"] == "0px"
    assert flat["rhythm"] == {"gap": "8px", "cell-pad": "7px 8px"}
    assert flat["surface"]["bg-panel"] == "transparent"
    assert flat["surface"]["shadow"] == "none"
    assert flat["layout"]["bar-row-height"] == "28px"
    assert flat["layout"]["chip-min"] == "48px"

    assert [paper["shape"][k] for k in ("radius-panel", "radius-card", "radius-cell")] == [
        "6px",
        "4px",
        "3px",
    ]
    assert paper["surface"]["bg-panel"] == "@surface_container_lowest"
    assert paper["surface"]["bg-card"] == "@surface_container_low"
    assert paper["surface"]["border"] == "alpha(@on_surface, 0.22)"
    assert paper["surface"]["shadow"] == "0 10px 28px rgba(0,0,0,0.22)"
    assert paper["layout"] == {
        "panel-width": "312px",
        "bt-list-spacing": "6px",
        "bar-row-height": "30px",
        "chip-min": "52px",
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


def test_false_vendoring_claim_fails(tmp_path: Path) -> None:
    data = schema()
    data["canonical"]["vendored"] = True
    data["canonical"]["tag"] = "v0.4.0"
    bad_schema = tmp_path / "schema-vendored.json"
    bad_schema.write_text(json.dumps(data))
    root = make_root(tmp_path, schema_override=bad_schema)
    errors = errors_for(root)
    assert any("vendored is true but no vendored copy" in error for error in errors), errors
