"""Fixture tests for the skins class (mirror of ``scripts/validate-skins.py``).

Run with the repository's development dependencies:

    make test-skins

The corpus itself is validated by the stdlib-only ``make validate-skins`` gate;
these tests add the positive frozen-value assertions and the negative fixtures
that prove the gate actually bites. The model is the v2 Appearance token set
from ``contracts`` v0.7.0, not the frozen v1 skin vocabulary.
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
TEMPLATES = ROOT / "skins" / "templates"
TEMPLATE = TEMPLATES / "ags.gtk.css.j2"
CONTRACTS = ROOT / "skins" / "contracts"
FIXTURES = Path(__file__).parent / "fixtures" / "invalid"

VENDORED = {
    "appearance-manifest.schema.json": "skins/contracts/appearance-manifest.schema.json",
    "appearance-json.schema.json": "skins/contracts/appearance-json.schema.json",
    "appearance-artifact.schema.json": "skins/contracts/appearance-artifact.schema.json",
    "skin-token.schema.json": "skins/contracts/skin-token.schema.json",
    "skin-manifest.schema.json": "skins/contracts/skin-manifest.schema.json",
    "skin-json.schema.json": "skins/contracts/skin-json.schema.json",
}
LAYOUT_PLACEHOLDER = re.compile(r"SKIN_LAYOUT_[A-Z0-9_]+")
PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")

#: target configDir -> (top-level selectors the app really applies, genuine
#: v2 token placeholders the extraction must use).
APP_TEMPLATES = {
    "ags": {
        "selectors": [
            "window.settings-panel",
            ".settings-surface",
            ".settings-card",
            ".settings-net",
            ".settings-badge",
            ".settings-rowact",
        ],
        "tokens": {
            "SKIN_SURFACE_PANEL_BG",
            "SKIN_SURFACE_PANEL_BORDER",
            "SKIN_SURFACE_PANEL_BORDER_WIDTH",
            "SKIN_SURFACE_PANEL_RADIUS",
            "SKIN_SURFACE_PANEL_PADDING",
            "SKIN_SURFACE_PANEL_SHADOW",
            "SKIN_SURFACE_PANEL_BLUR",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_BORDER_WIDTH",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CARD_PADDING",
            "SKIN_SURFACE_CELL_BG",
            "SKIN_SURFACE_CELL_HOVER_BG",
            "SKIN_SURFACE_CELL_RADIUS",
            "SKIN_SURFACE_CELL_PADDING",
            "SKIN_SURFACE_CONTROL_BG",
            "SKIN_SURFACE_CONTROL_BORDER",
            "SKIN_SURFACE_CONTROL_BORDER_WIDTH",
            "SKIN_SURFACE_CONTROL_RADIUS",
            "SKIN_SURFACE_CONTROL_PADDING",
            "SKIN_SURFACE_CONTROL_FONT_SIZE",
            "SKIN_SURFACE_CONTROL_FONT_WEIGHT",
            "SKIN_SURFACE_PILL_BG",
            "SKIN_SURFACE_PILL_BORDER",
            "SKIN_SURFACE_PILL_BORDER_WIDTH",
            "SKIN_SURFACE_PILL_RADIUS",
            "SKIN_SURFACE_PILL_PADDING",
            "SKIN_SURFACE_PILL_FONT_SIZE",
            "SKIN_SURFACE_PILL_LETTER_SPACING",
            "SKIN_STATE_HOVER_RING",
            "SKIN_STATE_SELECTED_FILL",
            "SKIN_STATE_SELECTED_INK",
            "SKIN_INK_INK",
            "SKIN_INK_INK_DIM",
            "SKIN_INK_ACCENT",
            "SKIN_INK_ACCENT_MUTED",
            "SKIN_INK_INK_OVER",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_SIZE_CAPTION",
            "SKIN_TYPE_SIZE_META",
            "SKIN_TYPE_SIZE_BODY",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_DISPLAY",
        },
    },
    "ags-clipboard": {
        "selectors": [
            "window#clipboard-window",
            ".clipboard-panel",
            ".clipboard-search",
            ".clipboard-card",
            ".clipboard-head",
            ".clipboard-empty",
        ],
        "tokens": {
            "SKIN_SURFACE_PANEL_BG",
            "SKIN_SURFACE_PANEL_BORDER",
            "SKIN_SURFACE_PANEL_BORDER_WIDTH",
            "SKIN_SURFACE_PANEL_RADIUS",
            "SKIN_SURFACE_PANEL_SHADOW",
            "SKIN_SURFACE_PANEL_BLUR",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CONTROL_RADIUS",
            "SKIN_INK_INK",
            "SKIN_INK_INK_DIM",
            "SKIN_INK_ACCENT",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_BODY",
        },
    },
    "ags-notifications": {
        "selectors": [
            "window#notifications-window",
            ".notif-card",
            ".notif-tile",
            ".notif-chip",
            ".wallpaper-progress-card",
            ".speedtest-progress-cell",
        ],
        "tokens": {
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CARD_PADDING",
            "SKIN_SURFACE_CELL_PADDING",
            "SKIN_SURFACE_CELL_RADIUS",
            "SKIN_SURFACE_PANEL_SHADOW",
            "SKIN_SURFACE_PILL_RADIUS",
            "SKIN_INK_INK",
            "SKIN_INK_INK_DIM",
            "SKIN_INK_ACCENT",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_BODY",
            "SKIN_TYPE_SIZE_META",
        },
    },
    "ags-wallpaper-selector": {
        "selectors": [
            "window#wallpaper-selector-window",
            ".ws-panel",
            ".ws-search",
            ".ws-card",
            ".ws-hoverbar",
            ".ws-live",
        ],
        "tokens": {
            "SKIN_SURFACE_PANEL_BG",
            "SKIN_SURFACE_PANEL_BORDER",
            "SKIN_SURFACE_PANEL_BORDER_WIDTH",
            "SKIN_SURFACE_PANEL_RADIUS",
            "SKIN_SURFACE_PANEL_SHADOW",
            "SKIN_SURFACE_PANEL_BLUR",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CARD_PADDING",
            "SKIN_SURFACE_CONTROL_RADIUS",
            "SKIN_SURFACE_PILL_RADIUS",
            "SKIN_SURFACE_PILL_PADDING",
            "SKIN_INK_INK",
            "SKIN_INK_INK_DIM",
            "SKIN_INK_ACCENT",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_BODY",
            "SKIN_TYPE_SIZE_META",
        },
    },
    "ags-capture": {
        "selectors": [
            "window#capture-window",
            "window#capture-overlay",
            ".capture-bar",
            ".capture-panel",
            ".capture-view",
            ".rec-cluster",
            "switch.palette-switch",
        ],
        "tokens": {
            "SKIN_SURFACE_PANEL_BG",
            "SKIN_SURFACE_PANEL_BORDER",
            "SKIN_SURFACE_PANEL_BORDER_WIDTH",
            "SKIN_SURFACE_PANEL_RADIUS",
            "SKIN_SURFACE_PANEL_SHADOW",
            "SKIN_SURFACE_PANEL_BLUR",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CARD_PADDING",
            "SKIN_SURFACE_CELL_RADIUS",
            "SKIN_SURFACE_CELL_PADDING",
            "SKIN_SURFACE_CONTROL_RADIUS",
            "SKIN_SURFACE_CONTROL_PADDING",
            "SKIN_SURFACE_PILL_RADIUS",
            "SKIN_STATE_HOVER_FILL",
            "SKIN_STATE_SELECTED_FILL",
            "SKIN_STATE_SELECTED_INK",
            "SKIN_STATE_FOCUS_RING",
            "SKIN_STATE_DISABLED_INK",
            "SKIN_INK_INK",
            "SKIN_INK_INK_DIM",
            "SKIN_INK_ACCENT",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_BODY",
            "SKIN_TYPE_SIZE_META",
        },
    },
    "ags-icme": {
        "selectors": [
            "window#icon-color-mapping-editor-window",
            ".icme-left",
            ".vcard",
            ".tree .item",
            ".cell",
            ".inspector-nav",
        ],
        "tokens": {
            "SKIN_SURFACE_PANEL_BG",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CELL_BG",
            "SKIN_SURFACE_CELL_RADIUS",
            "SKIN_SURFACE_CELL_PADDING",
            "SKIN_SURFACE_CONTROL_RADIUS",
            "SKIN_SURFACE_PILL_RADIUS",
            "SKIN_STATE_HOVER_FILL",
            "SKIN_STATE_SELECTED_FILL",
            "SKIN_STATE_SELECTED_INK",
            "SKIN_INK_INK",
            "SKIN_INK_INK_DIM",
            "SKIN_INK_ACCENT",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_BODY",
            "SKIN_TYPE_SIZE_META",
        },
    },
    "ags-btop-studio": {
        "selectors": [
            ".btop-theme-studio",
            ".studio-header",
            ".titem",
            ".canvas",
            ".live-frame",
            ".key-hit",
        ],
        "tokens": {
            "SKIN_SURFACE_PANEL_BG",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_RADIUS",
            "SKIN_SURFACE_CARD_PADDING",
            "SKIN_SURFACE_CELL_BG",
            "SKIN_SURFACE_CELL_BORDER",
            "SKIN_SURFACE_CELL_RADIUS",
            "SKIN_SURFACE_CELL_PADDING",
            "SKIN_SURFACE_CONTROL_RADIUS",
            "SKIN_SURFACE_PILL_RADIUS",
            "SKIN_STATE_HOVER_FILL",
            "SKIN_INK_INK",
            "SKIN_INK_ACCENT",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_FONT_WEIGHT",
            "SKIN_TYPE_LETTER_SPACING",
            "SKIN_TYPE_SIZE_TITLE",
            "SKIN_TYPE_SIZE_BODY",
            "SKIN_TYPE_SIZE_META",
        },
    },
}

PIN = CONTRACTS / "PIN"

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


def css_token_paths() -> list[str]:
    return list(schema()["frozen"]["css_token_paths"])


def resolved(name: str, mode: str = "dark") -> dict:
    return validate_skins._resolve_manifest(load_manifest(name), mode)


def render(template: str, name: str = "glass", mode: str = "dark") -> str:
    rendered = validate_skins.expand_template(template, resolved(name, mode))
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
    assert stats == {
        "manifests": 3,
        "templates": 7,
        "targets": sorted(APP_TEMPLATES),
        "tokens": 57,
        "roles": 51,
        "expansions": 6,
    }
    assert any("palette roles ==" in note for note in notes)
    for target in APP_TEMPLATES:
        note = next(
            (item for item in notes if f"target={target} expanded for" in item),
            "",
        )
        assert note, target
        for manifest_name in ("glass", "flat", "paper"):
            for mode in ("dark", "light"):
                assert f"{manifest_name}:{mode}" in note, f"{target}: {note}"


def test_template_target_is_the_filename_prefix() -> None:
    assert TEMPLATE.name == "ags.gtk.css.j2"
    assert TEMPLATE.name[: -len(".gtk.css.j2")] == "ags"
    assert validate_skins.TEMPLATE_NAME.match(TEMPLATE.name)
    assert not (TEMPLATE.parent / "ags-bar.gtk.css.j2").exists()
    assert sorted(path.name[: -len(".gtk.css.j2")] for path in TEMPLATES.glob("*.j2")) == sorted(
        APP_TEMPLATES
    )


@pytest.mark.parametrize("target", sorted(APP_TEMPLATES))
def test_app_template_expands_for_every_manifest_and_mode(target: str) -> None:
    path = TEMPLATES / f"{target}.gtk.css.j2"
    text = path.read_text()
    for manifest_name in ("glass", "flat", "paper"):
        for mode in ("dark", "light"):
            css = render(text, manifest_name, mode)
            assert "{{" not in css, f"{path.name}: {manifest_name}:{mode}"
    for selector in APP_TEMPLATES[target]["selectors"]:
        assert re.search(
            rf"(?m)^\s*{re.escape(selector)}\s*(?:,|\{{)", text
        ), f"{path.name}: missing selector {selector}"


@pytest.mark.parametrize("target", sorted(APP_TEMPLATES))
def test_app_template_placeholder_coverage(target: str) -> None:
    text = (TEMPLATES / f"{target}.gtk.css.j2").read_text()
    expected_paths = set(css_token_paths())
    expected = {validate_skins._flatten(path) for path in expected_paths}
    used = {match.strip() for match in PLACEHOLDER.findall(text)}
    assert used
    assert used <= expected, f"{target}: unknown placeholders {sorted(used - expected)}"
    assert not {name for name in used if not name.startswith("SKIN_")}
    missing = APP_TEMPLATES[target]["tokens"] - used
    assert missing == set(), f"{target}: expected genuine tokens missing: {sorted(missing)}"


@pytest.mark.parametrize("target", sorted(APP_TEMPLATES))
def test_app_template_has_no_literal_hex_transition_or_structure(target: str) -> None:
    text = (TEMPLATES / f"{target}.gtk.css.j2").read_text()
    assert not HEX.search(text), f"{target}: literal hex colour"
    assert not re.search(r"\btransition\s*:", text), f"{target}: transition"
    assert not re.search(r"\banimation\s*:", text), f"{target}: animation"
    assert "@keyframes" not in text, f"{target}: keyframes"
    for key in ("structure", "variant"):
        assert not re.search(rf"\b{key}\s*:", text), f"{target}: {key} property"


@pytest.mark.parametrize("target", sorted(APP_TEMPLATES))
def test_app_template_does_not_expand_layout_tokens(target: str) -> None:
    text = (TEMPLATES / f"{target}.gtk.css.j2").read_text()
    assert not LAYOUT_PLACEHOLDER.search(text), f"{target}: layout placeholder"
    for manifest_name in ("glass", "flat", "paper"):
        for mode in ("dark", "light"):
            css = render(text, manifest_name, mode)
            assert not LAYOUT_PLACEHOLDER.search(css), f"{target}: {manifest_name}:{mode}"


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


def test_schema_vendors_the_pinned_contracts_set() -> None:
    data = schema()
    assert data["schema_major"] == 2
    canonical = data["canonical"]
    assert canonical["repository"] == "contracts"
    assert set(canonical["paths"]) == {
        "schemas/appearance-manifest.schema.json",
        "schemas/appearance-json.schema.json",
        "schemas/appearance-artifact.schema.json",
        "schemas/skin-token.schema.json",
        "schemas/skin-manifest.schema.json",
        "schemas/skin-json.schema.json",
    }
    assert canonical["vendored"] is True
    assert canonical["tag"] == "v0.7.0"
    assert canonical["pin"] == "skins/contracts/PIN"
    assert canonical["delegates"] == {
        "manifest": "skins/contracts/appearance-manifest.schema.json",
        "json": "skins/contracts/appearance-json.schema.json",
        "artifact": "skins/contracts/appearance-artifact.schema.json",
    }
    assert set(canonical["legacy"]["frozen_v1"]) == {
        "skins/contracts/skin-token.schema.json",
        "skins/contracts/skin-manifest.schema.json",
        "skins/contracts/skin-json.schema.json",
    }
    assert canonical["resolved_document"]["path"] == (
        "skins/contracts/appearance-json.schema.json"
    )
    assert "tokens.json" in canonical["resolved_document"]["note"]
    metadata, _hashes = pin_metadata()
    assert metadata["contracts"] == canonical["tag"]
    assert metadata["source-commit"] == "3ea6d8354f23d0b9239e06392897e53496f25144"
    assert set(canonical["vendored_paths"]) == set(VENDORED.values())


def test_vendored_files_match_the_pin_hashes() -> None:
    _metadata, hashes = pin_metadata()
    assert set(hashes) == set(VENDORED)
    for name, rel in VENDORED.items():
        path = ROOT / rel
        assert path.is_file(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == hashes[name]


def test_manifest_documents_validate_against_the_vendored_manifest_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    manifest_schema = json.loads(
        (CONTRACTS / "appearance-manifest.schema.json").read_text()
    )
    jsonschema.Draft7Validator.check_schema(manifest_schema)
    validator = jsonschema.Draft7Validator(manifest_schema)
    for path in MANIFESTS.glob("*.toml"):
        with path.open("rb") as handle:
            manifest = tomllib.load(handle)
        errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
        assert errors == [], [error.message for error in errors]


def test_resolved_tokens_validate_for_every_manifest_and_mode() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    token_schema = json.loads((CONTRACTS / "appearance-json.schema.json").read_text())
    jsonschema.Draft7Validator.check_schema(token_schema)
    validator = jsonschema.Draft7Validator(token_schema)
    for name in ("glass", "flat", "paper"):
        for mode in ("dark", "light"):
            tokens = resolved(name, mode)
            assert tokens["version"] == 2
            assert set(tokens) == {"version", *validate_skins.GROUPS}
            errors = sorted(
                validator.iter_errors(tokens), key=lambda error: list(error.path)
            )
            assert errors == [], f"{name}:{mode}: {[e.message for e in errors]}"


def test_appearance_artifact_schema_accepts_a_generation() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    artifact_schema = json.loads(
        (CONTRACTS / "appearance-artifact.schema.json").read_text()
    )
    jsonschema.Draft7Validator.check_schema(artifact_schema)
    digest = "0" * 64
    artifact = {
        "version": 2,
        "skin": "glass",
        "mode": "dark",
        "paletteHash": digest,
        "skinHash": digest,
        "appearanceHash": digest,
        "generationHash": digest,
        "tokenRef": "tokens.json",
    }
    assert list(jsonschema.Draft7Validator(artifact_schema).iter_errors(artifact)) == []


def test_manifest_rejects_a_numeric_string() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    manifest_schema = json.loads(
        (CONTRACTS / "appearance-manifest.schema.json").read_text()
    )
    manifest = load_manifest("glass")
    manifest["groups"]["surface"]["panel"]["radius"] = "12px"
    errors = list(jsonschema.Draft7Validator(manifest_schema).iter_errors(manifest))
    assert errors, "the manifest schema must reject a numeric string"


def test_resolved_document_rejects_a_numeric_string() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    token_schema = json.loads((CONTRACTS / "appearance-json.schema.json").read_text())
    tokens = resolved("glass")
    tokens["surface"]["panel"]["radius"] = "12px"
    errors = list(jsonschema.Draft7Validator(token_schema).iter_errors(tokens))
    assert errors, "the resolved-token schema must reject a numeric string"


def test_every_css_token_path_is_present_in_every_resolved_document() -> None:
    paths = set(css_token_paths())
    for name in ("glass", "flat", "paper"):
        for mode in ("dark", "light"):
            tokens = resolved(name, mode)
            present = set(validate_skins._css_paths(tokens).values())
            assert present == paths, f"{name}:{mode}"


def test_state_role_and_surface_coverage() -> None:
    used: set[str] = set()
    for path in TEMPLATES.glob("*.j2"):
        for raw in PLACEHOLDER.findall(path.read_text()):
            used.add(raw.strip())
    paths = set(css_token_paths())
    used_paths = {path for path in paths if validate_skins._flatten(path) in used}

    for state in ("hover", "selected", "focus", "disabled"):
        assert any(path.startswith(f"state.{state}.") for path in used_paths), state
    for role in ("panel", "card", "cell", "control", "pill"):
        assert any(path.startswith(f"surface.{role}.") for path in used_paths), role
    for token in ("ink", "ink-dim", "accent", "accent-muted", "ink-over"):
        assert f"ink.{token}" in used_paths, token
    for token in (
        "font-family",
        "font-weight",
        "letter-spacing",
        "size-caption",
        "size-meta",
        "size-body",
        "size-title",
        "size-display",
    ):
        assert f"type.{token}" in used_paths, token


@pytest.mark.parametrize("name", ["glass", "flat", "paper"])
def test_no_literal_hex_or_transition_in_manifest(name: str) -> None:
    text = (MANIFESTS / f"{name}.toml").read_text()
    assert not HEX.search(text)
    assert "transition" not in text
    assert "animation" not in text


# --------------------------------------------------------------------------- #
# Frozen v2 values and mode resolution
# --------------------------------------------------------------------------- #


def test_frozen_glass_values() -> None:
    glass = load_manifest("glass")
    assert glass["schemaVersion"] == 2
    assert glass["name"] == "glass"
    assert glass["groups"]["surface"]["panel"] == {
        "bg": "alpha(@surface, 0.94)",
        "border": "@primary",
        "border-width": 1.5,
        "radius": 12,
        "padding": 11,
        "shadow": "none",
        "blur": "none",
    }
    assert glass["groups"]["surface"]["card"] == {
        "bg": "alpha(@surface_container_high, 0.18)",
        "border": "alpha(@on_surface, 0.10)",
        "border-width": 1,
        "radius": 9,
        "padding": 10,
    }
    assert glass["groups"]["surface"]["cell"] == {
        "bg": "transparent",
        "border": "transparent",
        "border-width": 0,
        "radius": 7,
        "padding": 8,
        "hover-bg": "alpha(@on_surface, 0.08)",
    }
    assert glass["groups"]["surface"]["control"]["border-width"] == 1
    assert glass["groups"]["surface"]["control"]["padding"] == 4
    assert glass["groups"]["surface"]["control"]["font-size"] == 11
    assert glass["groups"]["surface"]["pill"]["radius"] == 20
    assert glass["groups"]["surface"]["pill"]["font-size"] == 9.5
    assert glass["groups"]["surface"]["pill"]["letter-spacing"] == 0.05
    assert glass["groups"]["state"]["hover"] == {
        "fill": "alpha(@on_surface, 0.08)",
        "ink": "@on_surface",
        "ring": "@primary",
    }
    assert glass["groups"]["state"]["selected"] == {
        "fill": "@primary_container",
        "ink": "@on_primary_container",
        "ring": "@primary",
    }
    assert glass["groups"]["type"] == {
        "font-family": "inherit",
        "font-weight": 400,
        "letter-spacing": 0,
        "size-caption": 10.5,
        "size-meta": 11,
        "size-body": 13,
        "size-title": 12.5,
        "size-display": 16,
    }
    assert glass["groups"]["ink"] == {
        "ink": "@on_surface",
        "ink-dim": "alpha(@on_surface, 0.62)",
        "accent": "@primary",
        "accent-muted": "alpha(@primary, 0.18)",
        "ink-over": "auto",
    }
    assert glass["groups"]["layout"]["ags"] == {
        "panel-width": 312,
        "bt-list-spacing": 4,
    }
    assert glass["groups"]["layout"]["ags-icme"] == {
        "root-width": 1280,
        "root-height": 800,
    }
    assert glass["groups"]["layout"]["ags-wallpaper-selector"] == {
        "root-width": 960,
        "root-height": 640,
    }
    assert "mode" not in glass


def test_frozen_flat_and_paper_values() -> None:
    flat = load_manifest("flat")
    paper = load_manifest("paper")

    assert flat["groups"]["surface"]["panel"]["radius"] == 0
    assert flat["groups"]["surface"]["panel"]["border-width"] == 0
    assert flat["groups"]["surface"]["panel"]["bg"] == "transparent"
    assert flat["groups"]["surface"]["pill"]["radius"] == 999
    assert flat["groups"]["type"]["size-title"] == 15

    assert paper["groups"]["surface"]["panel"]["bg"] == "@surface_container_lowest"
    assert paper["groups"]["surface"]["panel"]["border"] == "alpha(@on_surface, 0.22)"
    assert paper["groups"]["surface"]["card"]["bg"] == "@surface_container_low"
    assert paper["groups"]["surface"]["panel"]["radius"] == 6
    assert paper["groups"]["surface"]["card"]["radius"] == 4
    assert paper["groups"]["surface"]["cell"]["radius"] == 3
    assert paper["groups"]["surface"]["panel"]["shadow"] == (
        "0 10px 28px rgba(0,0,0,0.22)"
    )
    assert paper["groups"]["layout"]["ags"] == {
        "panel-width": 312,
        "bt-list-spacing": 6,
    }


def test_layout_defaults_preserve_the_apps_pre_v2_window_sizes() -> None:
    """Every skin keeps the app defaults; only paint/rhythm differs per skin."""
    for name in ("glass", "flat", "paper"):
        layout = load_manifest(name)["groups"]["layout"]
        assert layout["ags-icme"] == {"root-width": 1280, "root-height": 800}, name
        assert layout["ags-wallpaper-selector"] == {
            "root-width": 960,
            "root-height": 640,
        }, name
        # Retired v1 knobs: no app source reads them.
        assert "bar-row-height" not in layout["ags"], name
        assert "chip-min" not in layout["ags"], name
        # Real TSX literals and the CSS-derived cleanup candidates stay put.
        assert layout["ags"] == {
            "panel-width": 312,
            "bt-list-spacing": 4 if name != "paper" else 6,
        }, name
        assert layout["ags-clipboard"] == {"card-width": 260}, name
        assert layout["ags-notifications"] == {"card-width": 380}, name
        assert layout["ags-capture"] == {"panel-width": 560}, name
        assert layout["ags-btop-studio"] == {
            "left-width": 280,
            "right-width": 320,
        }, name


def test_paper_declares_explicit_light_mode_overrides() -> None:
    paper = load_manifest("paper")
    assert "light" in paper["mode"]
    assert set(paper["mode"]["light"]) == {"surface", "state", "ink"}
    light = paper["mode"]["light"]

    # A complete same-shape surface group, not a partial merge.
    assert set(light["surface"]) == {"panel", "card", "cell", "control", "pill"}
    assert light["surface"]["panel"]["border"] == "alpha(@on_surface, 0.16)"
    assert light["surface"]["card"]["border"] == "alpha(@on_surface, 0.10)"
    assert light["surface"]["cell"]["hover-bg"] == "alpha(@on_surface, 0.06)"
    assert light["state"]["hover"]["fill"] == "alpha(@on_surface, 0.06)"
    assert light["ink"]["ink"] == "@on_surface"

    dark = resolved("paper", "dark")
    light_tokens = resolved("paper", "light")
    assert dark["surface"]["panel"]["border"] == "alpha(@on_surface, 0.22)"
    assert light_tokens["surface"]["panel"]["border"] == "alpha(@on_surface, 0.16)"
    assert dark["state"]["hover"]["fill"] == "alpha(@on_surface, 0.08)"
    assert light_tokens["state"]["hover"]["fill"] == "alpha(@on_surface, 0.06)"
    # The base dark branch stays the v1-equivalent paper look.
    assert dark["surface"]["panel"]["bg"] == "@surface_container_lowest"
    assert light_tokens["surface"]["panel"]["shadow"] == (
        "0 8px 22px alpha(@shadow, 0.16)"
    )


def test_glass_expands_to_the_tokenized_values() -> None:
    css = render(TEMPLATE.read_text(), "glass")
    assert "background-color: alpha(@surface, 0.94);" in css
    assert "background-color: alpha(@surface_container_high, 0.18);" in css
    assert "border: 1.5px solid @primary;" in css
    assert "border: 1px solid alpha(@on_surface, 0.10);" in css
    assert "border: 1px solid alpha(@on_surface, 0.26);" in css
    assert "border: 1px solid alpha(@on_surface, 0.14);" in css
    assert "box-shadow: none;" in css
    assert "backdrop-filter: none;" in css
    assert "border-radius: 12px;" in css
    assert "border-radius: 9px;" in css
    assert "border-radius: 7px;" in css
    assert "border-radius: 20px;" in css
    assert "padding: 11px;" in css
    assert "padding: 10px 11px;" in css
    assert "padding: 8px 9px;" in css
    assert "padding: 4px 8px;" in css
    assert "padding: 2px 6px;" in css
    assert "font-size: 10.5px;" in css
    assert "font-size: 11px;" in css
    assert "font-size: 12.5px;" in css
    assert "font-size: 13px;" in css
    assert "font-size: 16px;" in css
    assert "letter-spacing: 0.05em;" in css
    assert "min-width: 312px;" not in css


def test_flat_and_paper_expand_with_their_own_surfaces() -> None:
    flat = render(TEMPLATE.read_text(), "flat")
    assert "background-color: transparent;" in flat
    assert "border: 0px solid transparent;" in flat
    assert "box-shadow: none;" in flat
    assert "padding: 7px 9px;" in flat
    assert "border-radius: 0px;" in flat

    paper_dark = render(TEMPLATE.read_text(), "paper", "dark")
    assert "background-color: @surface_container_lowest;" in paper_dark
    assert "background-color: @surface_container_low;" in paper_dark
    assert "border: 1px solid alpha(@on_surface, 0.22);" in paper_dark
    assert "box-shadow: 0 10px 28px rgba(0,0,0,0.22);" in paper_dark

    paper_light = render(TEMPLATE.read_text(), "paper", "light")
    assert "border: 1px solid alpha(@on_surface, 0.16);" in paper_light
    assert "box-shadow: 0 8px 22px alpha(@shadow, 0.16);" in paper_light
    assert "background-color: alpha(@on_surface, 0.06);" in paper_light


# --------------------------------------------------------------------------- #
# Negative fixtures
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("fixture", "needle"),
    [
        ("literal-hex.toml", "literal hex colour"),
        ("unknown-role.toml", "not in palette.v1"),
        ("structure.toml", "structure/variant keys are forbidden"),
        ("missing-token.toml", "missing required property"),
        ("numeric-string.toml", "must be a number"),
        ("unknown-surface-role.toml", "unexpected property"),
        ("incomplete-mode.toml", "missing required property"),
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
        ("transition.gtk.css.j2", "CSS transition"),
        ("unknown-placeholder.gtk.css.j2", "is not a token"),
        ("layout-placeholder.gtk.css.j2", "layout token"),
        ("ags-bar.css.j2", "template name"),
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
    target = root / "skins" / "contracts" / "appearance-manifest.schema.json"
    target.write_text(target.read_text() + "\n")
    errors = errors_for(root)
    assert any("does not match" in error for error in errors), errors


def test_pinned_tag_disagreement_fails(tmp_path: Path) -> None:
    data = schema()
    data["canonical"]["tag"] = "v0.6.0"
    bad_schema = tmp_path / "schema-tag.json"
    bad_schema.write_text(json.dumps(data))
    root = make_root(tmp_path, schema_override=bad_schema)
    errors = errors_for(root)
    assert any("disagrees with canonical.tag" in error for error in errors), errors
