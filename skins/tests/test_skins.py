"""Fixture tests for the skins class (mirror of ``scripts/validate-skins.py``).

Run with the repository's development dependencies:

    make test-skins

The corpus itself is validated by the stdlib-only ``make validate-skins`` gate;
these tests add the positive frozen-value assertions and the negative fixtures
that prove the gate actually bites. The model is the v2 Appearance token set
from ``contracts`` v0.12.0, not the frozen v1 skin vocabulary. The required
six-role surface includes ``window`` (never aliased from ``panel``); the
optional root ``[host]`` policy is a delegation object, not a token group and
delegates window/panel geometry plus the card/control/cell rectangle radii;
the pill stays explicit. The shared template set has CSS targets
(``<configDir>.gtk.css.j2``) and non-CSS artifacts
(``<consumer>.<format>.j2``); this tag ships the ``gtk3``/``gtk4`` targets and
the ``rofi``/``rasi`` and ``kitty``/``conf`` artifacts.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
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
POSITIVE = Path(__file__).parent / "fixtures" / "positive"
MANIFEST_NAMES = ("glass", "flat", "paper", "terminal", "terminal-host")

VENDORED = {
    "appearance-manifest.schema.json": "skins/contracts/appearance-manifest.schema.json",
    "appearance-json.schema.json": "skins/contracts/appearance-json.schema.json",
    "appearance-artifact.schema.json": "skins/contracts/appearance-artifact.schema.json",
    "generation-manifest.schema.json": "skins/contracts/generation-manifest.schema.json",
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
            ".audio-surface",
            ".tray-surface",
            ".audio-settings",
            ".audio-menu > contents",
            ".audio-playing-page",
            ".audio-mixer-row",
            ".audio-device",
            ".audio-muted-pill",
            ".audio-switch",
            ".audio-strip-main",
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
            "SKIN_STATE_FOCUS_RING",
            "SKIN_STATE_DISABLED_INK",
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
    "wlogout": {
        "selectors": [
            "window",
            "button",
            "button:hover",
            "button:focus",
            "button:active",
            "button span",
        ],
        "tokens": {
            "SKIN_SURFACE_WINDOW_BG",
            "SKIN_SURFACE_PANEL_BORDER_WIDTH",
            "SKIN_SURFACE_PANEL_RADIUS",
            "SKIN_SURFACE_CARD_BG",
            "SKIN_SURFACE_CARD_BORDER",
            "SKIN_SURFACE_CARD_PADDING",
            "SKIN_STATE_HOVER_INK",
            "SKIN_STATE_HOVER_RING",
            "SKIN_STATE_FOCUS_INK",
            "SKIN_STATE_FOCUS_RING",
            "SKIN_STATE_SELECTED_FILL",
            "SKIN_STATE_SELECTED_INK",
            "SKIN_STATE_SELECTED_RING",
            "SKIN_INK_INK",
            "SKIN_TYPE_FONT_FAMILY",
            "SKIN_TYPE_FONT_WEIGHT",
            "SKIN_TYPE_LETTER_SPACING",
            "SKIN_TYPE_SIZE_TITLE",
        },
    },
}

PIN = CONTRACTS / "PIN"
REQUIRED_TARGETS = set(APP_TEMPLATES) | {"gtk3", "gtk4"}
REQUIRED_ARTIFACTS = [
    {"consumer": "rofi", "format": "rasi"},
    {"consumer": "kitty", "format": "conf"},
]
FORMAT_TEMPLATES = {
    "gtk3": ("gtk3.gtk.css.j2", "css"),
    "gtk4": ("gtk4.gtk.css.j2", "css"),
    "rofi": ("rofi.rasi.j2", "rasi"),
    "kitty": ("kitty.conf.j2", "conf"),
}

ROFI_CONFIG = ROOT / "configs" / "rofi" / "launcher" / "config.rasi"
ROFI_PALETTE_IMPORT = '@import "../colors.rasi"'
ROFI_APPEARANCE_IMPORT = '@import "../appearance.rasi"'

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


def render(
    template: str,
    name: str = "glass",
    mode: str = "dark",
    template_format: str = "css",
) -> str:
    rendered = validate_skins.expand_template(
        template, resolved(name, mode), template_format
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


def make_full_root(
    tmp_path: Path,
    *,
    drop_template: str | None = None,
    drop_artifact: str | None = None,
    manifest_override: tuple[str, Path] | None = None,
    schema_override: Path | None = None,
) -> Path:
    """A complete corpus copy for required-target tests.

    ``make_root`` deliberately copies one template so a single negative fixture
    is isolated. Required-target coverage needs the whole set, optionally minus
    one target or artifact to prove the gate bites.
    """
    root = tmp_path / "repo"
    (root / "skins" / "manifests").mkdir(parents=True)
    (root / "skins" / "templates").mkdir(parents=True)
    shutil.copytree(CONTRACTS, root / "skins" / "contracts")
    shutil.copy2(schema_override or SCHEMA, root / "skins" / "schema.json")
    for path in MANIFESTS.glob("*.toml"):
        shutil.copy2(path, root / "skins" / "manifests" / path.name)
    if manifest_override is not None:
        stem, source = manifest_override
        shutil.copy2(source, root / "skins" / "manifests" / f"{stem}.toml")
    for path in TEMPLATES.glob("*.j2"):
        if drop_template is not None and path.name == f"{drop_template}.gtk.css.j2":
            continue
        if drop_artifact is not None and path.name in {
            f"{drop_artifact}.rasi.j2",
            f"{drop_artifact}.conf.j2",
            f"{drop_artifact}.theme.j2",
        }:
            continue
        shutil.copy2(path, root / "skins" / "templates" / path.name)
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
        "manifests": 5,
        "templates": 12,
        "targets": sorted(REQUIRED_TARGETS),
        "artifacts": ["kitty:conf", "rofi:rasi"],
        "tokens": 65,
        "roles": 51,
        "expansions": 10,
        "host_resolutions": 6,
        "host_manifests": ["glass", "paper", "terminal-host"],
    }
    assert any("palette roles ==" in note for note in notes)
    assert any("host policy resolved for glass,paper,terminal-host" in note for note in notes)
    for target in REQUIRED_TARGETS:
        note = next(
            (item for item in notes if f"targets={target} format=css expanded for" in item),
            "",
        )
        assert note, target
        for manifest_name in MANIFEST_NAMES:
            for mode in ("dark", "light"):
                assert f"{manifest_name}:{mode}" in note, f"{target}: {note}"
    rofi_note = next(
        (item for item in notes if "artifacts=rofi format=rasi expanded for" in item),
        "",
    )
    assert rofi_note
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            assert f"{manifest_name}:{mode}" in rofi_note


def test_template_target_is_the_filename_prefix() -> None:
    assert TEMPLATE.name == "ags.gtk.css.j2"
    assert TEMPLATE.name[: -len(".gtk.css.j2")] == "ags"
    assert validate_skins.TEMPLATE_NAME.match(TEMPLATE.name)
    assert not (TEMPLATE.parent / "ags-bar.gtk.css.j2").exists()
    assert sorted(
        path.name[: -len(".gtk.css.j2")]
        for path in TEMPLATES.glob("*.gtk.css.j2")
    ) == sorted(REQUIRED_TARGETS)


@pytest.mark.parametrize("target", sorted(APP_TEMPLATES))
def test_app_template_expands_for_every_manifest_and_mode(target: str) -> None:
    path = TEMPLATES / f"{target}.gtk.css.j2"
    text = path.read_text()
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            css = render(text, manifest_name, mode)
            assert "{{" not in css, f"{path.name}: {manifest_name}:{mode}"
    for selector in APP_TEMPLATES[target]["selectors"]:
        assert re.search(
            rf"(?m)^\s*{re.escape(selector)}\s*(?:,|\{{)", text
        ), f"{path.name}: missing selector {selector}"


def _rule(css: str, selector: str) -> str:
    """Declarations for a selector, including grouped selectors."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selectors = [item.strip() for item in match.group(1).split(",")]
        if selector in selectors:
            return match.group(2)
    raise AssertionError(f"missing {selector} rule")


def test_ags_template_paints_the_sound_panel_from_the_panel_role() -> None:
    """REQ-005: the AGS sound overlay is `surface.panel`, never `window`."""
    text = TEMPLATE.read_text()
    assert ".audio-surface" in text
    assert ".tray-surface" in text
    assert ".audio-settings" in text
    # No sound selector may consume the toplevel window role (doc 113 W-10).
    code = validate_skins._strip_comments(text)
    for match in re.finditer(r"(?m)^\s*([^{}]+)\s*\{", code):
        selector = match.group(1)
        if ".audio-" in selector or ".tray-" in selector:
            assert "surface.window" not in selector
    sound = text[text.index("/* ── Sound — REQ-005"):]
    assert "SKIN_SURFACE_WINDOW" not in sound
    # The panel radius/paint are the manifest's panel values in every skin.
    expected = {
        "glass": ("alpha(@surface, 0.94)", "12px"),
        "paper": ("@surface_container_lowest", "6px"),
        "flat": ("transparent", "0px"),
        "terminal": ("@surface", "0px"),
        "terminal-host": ("@surface", "0px"),
    }
    for name, (paint, radius) in expected.items():
        css = render(text, name, "dark")
        surface = _rule(css, ".audio-surface")
        settings = _rule(css, ".audio-settings")
        assert f"background-color: {paint}" in surface, (name, surface)
        assert f"border-radius: {radius}" in surface, (name, surface)
        assert f"border-radius: {radius}" in settings, (name, settings)
        assert "padding:" in surface and "box-shadow:" in surface
        assert "backdrop-filter:" in surface


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
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            css = render(text, manifest_name, mode)
            assert not LAYOUT_PLACEHOLDER.search(css), f"{target}: {manifest_name}:{mode}"


@pytest.mark.parametrize("name", sorted(FORMAT_TEMPLATES))
def test_format_template_expands_for_every_manifest_and_mode(name: str) -> None:
    filename, template_format = FORMAT_TEMPLATES[name]
    text = (TEMPLATES / filename).read_text()
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            expanded = render(text, manifest_name, mode, template_format)
            assert "{{" not in expanded, f"{filename}: {manifest_name}:{mode}"
            assert not validate_skins.PLACEHOLDER.findall(expanded)


@pytest.mark.parametrize("name", sorted(FORMAT_TEMPLATES))
def test_format_template_has_no_literal_hex_structure_or_layout(name: str) -> None:
    filename, _template_format = FORMAT_TEMPLATES[name]
    text = (TEMPLATES / filename).read_text()
    assert not HEX.search(text), f"{filename}: literal hex colour"
    assert not re.search(r"\btransition\s*:", text), f"{filename}: transition"
    assert not re.search(r"\banimation\s*:", text), f"{filename}: animation"
    assert not LAYOUT_PLACEHOLDER.search(text), f"{filename}: layout placeholder"
    for key in ("structure", "variant"):
        assert not re.search(rf"\b{key}\s*:", text), f"{filename}: {key} property"
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            expanded = render(text, manifest_name, mode, _template_format)
            assert not HEX.search(expanded), f"{filename}: rendered hex"
            assert not LAYOUT_PLACEHOLDER.search(expanded), f"{filename}: rendered layout"
            assert not re.search(r"\btransition\s*:", expanded), filename
            assert not re.search(r"\banimation\s*:", expanded), filename
            assert not re.search(r"\b(?:structure|variant)\s*:", expanded), filename


def test_gtk3_template_is_gtk3_dialect_and_conservative() -> None:
    text = (TEMPLATES / "gtk3.gtk.css.j2").read_text()
    code = validate_skins._strip_comments(text)
    assert not re.search(r"\bvar\s*\(", code)
    assert not re.search(r"\bcolor-mix\s*\(", code)
    assert validate_skins._selectors(text)
    assert set(validate_skins._selectors(text)) <= validate_skins.GTK_SELECTORS
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            css = render(text, manifest_name, mode)
            assert not re.search(r"\bvar\s*\(", css)
            assert not re.search(r"\bcolor-mix\s*\(", css)
            assert set(validate_skins._selectors(css)) <= validate_skins.GTK_SELECTORS
            for line in css.splitlines():
                assert not validate_skins.GTK_LAYOUT_PROPERTY.match(line), line


def test_gtk4_template_is_conservative_and_uses_named_colours() -> None:
    text = (TEMPLATES / "gtk4.gtk.css.j2").read_text()
    assert "@define-color window_bg_color" in text
    assert "@define-color accent_bg_color" in text
    assert set(validate_skins._selectors(text)) <= validate_skins.GTK_SELECTORS
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            css = render(text, manifest_name, mode)
            assert set(validate_skins._selectors(css)) <= validate_skins.GTK_SELECTORS
            for line in css.splitlines():
                assert not validate_skins.GTK_LAYOUT_PROPERTY.match(line), line


def test_rofi_template_is_solid_roles_and_geometry_only() -> None:
    text = (TEMPLATES / "rofi.rasi.j2").read_text()
    code = validate_skins._strip_comments(text)
    assert not validate_skins.RASI_ALPHA.search(code)
    assert not validate_skins.RASI_UNDERSCORE_ROLE.search(code)
    assert "SKIN_TYPE_" not in text, "typography is deferred in Phase 3A"
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            rasi = render(text, manifest_name, mode, "rasi")
            assert not validate_skins.RASI_ALPHA.search(rasi)
            assert not validate_skins.RASI_UNDERSCORE_ROLE.search(rasi)
            assert not HEX.search(rasi)
            assert "SKIN_TYPE_" not in rasi
            roles = set(schema()["palette"]["roles"])
            hyphenated = {role.replace("_", "-") for role in roles}
            assert set(validate_skins.RASI_ROLE.findall(rasi)) <= hyphenated


@pytest.mark.parametrize(
    (
        "name",
        "window_radius",
        "window_border",
        "panel_radius",
        "panel_border",
        "card_radius",
        "control_radius",
        "cell_radius",
    ),
    [
        ("terminal-host", 17, 3, 13, 2, 14, 15, 16),
        ("glass", 17, 3, 13, 2, 14, 15, 16),
        ("paper", 17, 3, 13, 2, 14, 15, 16),
        ("terminal", 0, 1, 0, 1, 0, 2, 0),
        ("flat", 0, 0, 0, 0, 0, 0, 0),
    ],
)
def test_rofi_host_probe_delegates_rectangle_radii_for_opt_in_skins(
    name: str,
    window_radius: int,
    window_border: int,
    panel_radius: int,
    panel_border: int,
    card_radius: int,
    control_radius: int,
    cell_radius: int,
) -> None:
    """Window owns rofi's outer slot; mainbox/inputbar/element stay card/control/cell."""
    text = (TEMPLATES / "rofi.rasi.j2").read_text()
    host = dict(validate_skins.HOST_PROBE)
    tokens = validate_skins._resolve_manifest(load_manifest(name), "dark", host)
    rasi = validate_skins.expand_template(text, tokens, "rasi")
    assert "{{" not in rasi

    window = _wlogout_block(rasi, "window")
    mainbox = _wlogout_block(rasi, "mainbox")
    inputbar = _wlogout_block(rasi, "inputbar")
    element = _wlogout_block(rasi, "element")
    assert f"border-radius: {window_radius}px;" in window
    assert f"border: {window_border}px;" in window
    assert f"border-radius: {card_radius}px;" in mainbox
    assert f"border-radius: {control_radius}px;" in inputbar
    assert f"border-radius: {cell_radius}px;" in element


@pytest.mark.parametrize(
    "template_name",
    ["gtk3.gtk.css.j2", "gtk4.gtk.css.j2"],
)
@pytest.mark.parametrize(
    ("name", "card_radius", "control_radius"),
    [
        ("terminal-host", 14, 15),
        ("glass", 14, 15),
        ("paper", 14, 15),
        ("terminal", 0, 2),
        ("flat", 0, 0),
    ],
)
def test_gtk_host_probe_delegates_card_and_control_radii(
    template_name: str, name: str, card_radius: int, control_radius: int
) -> None:
    """GTK's control/card roles follow the host probe only for opt-in skins."""
    text = (TEMPLATES / template_name).read_text()
    tokens = validate_skins._resolve_manifest(
        load_manifest(name), "dark", dict(validate_skins.HOST_PROBE)
    )
    css = validate_skins.expand_template(text, tokens, "css")
    assert "{{" not in css
    for selector in ("button", "entry"):
        assert f"border-radius: {control_radius}px;" in _wlogout_block(css, selector)
    assert f"border-radius: {card_radius}px;" in _wlogout_block(css, ".card")


def test_rofi_dump_theme_has_no_parse_warning(tmp_path: Path) -> None:
    rofi = shutil.which("rofi")
    if rofi is None:
        pytest.skip("rofi is not installed")
    text = (TEMPLATES / "rofi.rasi.j2").read_text()
    for manifest_name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            path = tmp_path / f"{manifest_name}-{mode}.rasi"
            path.write_text(render(text, manifest_name, mode, "rasi"))
            result = subprocess.run(
                [rofi, "-dump-theme", "-theme", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, (manifest_name, mode, result.stderr)
            assert "Failed to parse theme" not in result.stderr, (
                manifest_name,
                mode,
                result.stderr,
            )
            assert result.stdout.strip(), (manifest_name, mode)


@pytest.mark.parametrize(
    ("fixture", "needle"),
    [
        ("rofi-alpha", "Failed to parse theme"),
        ("rofi-underscore", "Failed to parse theme"),
    ],
)
def test_rofi_negative_fixture_warns_while_exiting_zero(
    tmp_path: Path, fixture: str, needle: str
) -> None:
    rofi = shutil.which("rofi")
    if rofi is None:
        pytest.skip("rofi is not installed")
    source = FIXTURES / "format" / fixture / "rofi.rasi.j2"
    path = tmp_path / "bad.rasi"
    path.write_text(source.read_text())
    result = subprocess.run(
        [rofi, "-dump-theme", "-theme", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert needle in result.stderr, result.stderr


def _rofi_layout(
    tmp_path: Path,
    skin: str,
    *,
    host: dict[str, object] | None = None,
    include_appearance: bool = True,
) -> Path:
    """Materialise the deployed rofi layout and return its launcher theme.

    The static config imports ``../colors.rasi`` first and
    ``../appearance.rasi`` last, exactly as the consumer deploys it. The
    appearance sheet is rendered from the rofi artifact so this probe exercises
    the real static/generated import order rather than the template in
    isolation.
    """
    layout = tmp_path / "rofi"
    launcher = layout / "launcher"
    launcher.mkdir(parents=True)
    roles = schema()["palette"]["roles"]
    (layout / "colors.rasi").write_text(
        "* {\n"
        + "\n".join(f"    {role.replace('_', '-')}: #123456;" for role in roles)
        + "\n}\n"
    )
    if include_appearance:
        tokens = validate_skins._resolve_manifest(load_manifest(skin), "dark", host)
        (layout / "appearance.rasi").write_text(
            validate_skins.expand_template(
                (TEMPLATES / "rofi.rasi.j2").read_text(), tokens, "rasi"
            )
        )
    text = ROFI_CONFIG.read_text()
    assert ROFI_PALETTE_IMPORT in text
    assert ROFI_APPEARANCE_IMPORT in text
    (launcher / "config.rasi").write_text(text)
    return launcher / "config.rasi"


def _rofi_dump_theme(theme: Path) -> str:
    rofi = shutil.which("rofi")
    if rofi is None:
        pytest.skip("rofi is not installed")
    result = subprocess.run(
        [rofi, "-no-config", "-theme", str(theme), "-dump-theme"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Failed to parse theme" not in result.stderr, result.stderr
    assert result.stdout.strip(), "rofi -dump-theme produced no theme"
    return result.stdout


def _rofi_radii(dump: str) -> tuple[int, int, int, int]:
    radii = []
    for selector in ("window", "mainbox", "inputbar", "element"):
        match = re.search(
            r"border-radius:\s*(\d+)px", _wlogout_block(dump, selector)
        )
        assert match is not None, f"{selector} has no border-radius in the dump"
        radii.append(int(match.group(1)))
    return tuple(radii)  # type: ignore[return-value]


def test_rofi_static_config_imports_appearance_last() -> None:
    """Regression guard: the static radii must not override the generated skin."""
    lines = [line.strip() for line in ROFI_CONFIG.read_text().splitlines() if line.strip()]
    imports = [line for line in lines if line.startswith("@import")]
    assert imports == [ROFI_PALETTE_IMPORT, ROFI_APPEARANCE_IMPORT]
    assert lines[-1] == ROFI_APPEARANCE_IMPORT


@pytest.mark.parametrize(
    ("skin", "host", "expected"),
    [
        ("terminal", None, (0, 0, 2, 0)),
        (
            "terminal-host",
            {
                "surface.window.radius": 7,
                "surface.window.border-width": 2,
                "surface.panel.radius": 9,
                "surface.panel.border-width": 2,
                "surface.card.radius": 9,
                "surface.control.radius": 9,
                "surface.cell.radius": 9,
            },
            (7, 9, 9, 9),
        ),
        ("flat", None, (0, 0, 0, 0)),
        ("paper", None, (6, 4, 3, 3)),
    ],
)
def test_rofi_config_renders_generated_geometry_last(
    tmp_path: Path,
    skin: str,
    host: dict[str, object] | None,
    expected: tuple[int, int, int, int],
) -> None:
    """The deployed import order yields the generated panel/card/control/cell radii."""
    theme = _rofi_layout(tmp_path, skin, host=host)
    assert _rofi_radii(_rofi_dump_theme(theme)) == expected


def test_rofi_host_probe_leaves_the_pill_radius_explicit() -> None:
    """Delegating the four rectangles must not reach the pill token."""
    pill = load_manifest("terminal-host")["groups"]["surface"]["pill"]["radius"]
    host = {
        "surface.window.radius": 7,
        "surface.window.border-width": 2,
        "surface.panel.radius": 9,
        "surface.panel.border-width": 2,
        "surface.card.radius": 9,
        "surface.control.radius": 9,
        "surface.cell.radius": 9,
    }
    resolved = validate_skins._resolve_manifest(load_manifest("terminal-host"), "dark", host)
    assert resolved["surface"]["pill"]["radius"] == pill


def test_rofi_static_config_falls_back_when_appearance_is_missing(tmp_path: Path) -> None:
    """A host without the generated sheet still parses the palette + static radii."""
    theme = _rofi_layout(tmp_path, "terminal", include_appearance=False)
    assert not (theme.parent.parent / "appearance.rasi").exists()
    assert _rofi_radii(_rofi_dump_theme(theme)) == (16, 8, 5, 5)


def _gtk_parse_probe(template_name: str, gtk_version: str) -> subprocess.CompletedProcess[str]:
    """Parse every skin's rendered sheet with a GTK provider in a child process.

    GTK3 and GTK4 cannot both be loaded in one interpreter, and the pytest
    virtualenv may not have `gi`. Prefer the current interpreter, then the
    system interpreter, and skip only when neither can import `gi`.
    """
    script = f"""
import importlib.util, json, pathlib, sys, tempfile
root = pathlib.Path({str(ROOT)!r})
spec = importlib.util.spec_from_file_location("validate_skins", root / "scripts" / "validate-skins.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
roles = json.loads((root / "skins" / "schema.json").read_text())["palette"]["roles"]
defs = "\\n".join(f"@define-color {{role}} #123456;" for role in roles)
import gi
gi.require_version("Gtk", {gtk_version!r})
from gi.repository import Gtk
template = (root / "skins" / "templates" / {template_name!r}).read_text()
parsed = 0
for name in ("glass", "flat", "paper", "terminal", "terminal-host"):
    manifest = __import__("tomllib").loads((root / "skins" / "manifests" / f"{{name}}.toml").read_text())
    for mode in ("dark", "light"):
        resolved = v._resolve_manifest(manifest, mode)
        css = v.expand_template(template, resolved, "css")
        path = pathlib.Path(tempfile.mkdtemp()) / "gtk.css"
        path.write_text(defs + "\\n" + css)
        provider = Gtk.CssProvider()
        result = provider.load_from_path(str(path))
        if result is False:
            sys.exit(f"{{name}}:{{mode}} GTK parse returned False")
        parsed += 1
print(f"parsed {{parsed}}/10")
"""
    candidates = [sys.executable, Path(sys.base_prefix) / "bin" / "python3", Path("/usr/bin/python3")]
    seen: set[str] = set()
    for candidate in candidates:
        executable = str(candidate)
        if executable in seen or not Path(executable).is_file():
            continue
        seen.add(executable)
        check = subprocess.run(
            [executable, "-c", "import gi"], capture_output=True, text=True, check=False
        )
        if check.returncode == 0:
            return subprocess.run(
                [executable, "-c", script],
                capture_output=True,
                text=True,
                check=False,
            )
    pytest.skip("no interpreter with gi (PyGObject) is available for the GTK probe")


@pytest.mark.parametrize(
    ("template_name", "gtk_version"),
    [("gtk3.gtk.css.j2", "3.0"), ("gtk4.gtk.css.j2", "4.0")],
)
def test_gtk_format_template_parses_every_skin(
    template_name: str, gtk_version: str
) -> None:
    result = _gtk_parse_probe(template_name, gtk_version)
    assert result.returncode == 0, result.stderr
    assert "parsed 10/10" in result.stdout, result.stdout
    assert "parser error" not in result.stderr.lower(), result.stderr


def test_required_targets_and_artifacts_match_the_template_matrix() -> None:
    assert set(schema()["frozen"]["required_targets"]) == REQUIRED_TARGETS
    assert schema()["frozen"]["required_artifacts"] == REQUIRED_ARTIFACTS
    assert sorted(
        path.name for path in TEMPLATES.glob("*.rasi.j2")
    ) == ["rofi.rasi.j2"]
    assert sorted(
        path.name for path in TEMPLATES.glob("*.conf.j2")
    ) == ["kitty.conf.j2"]
    assert not list(TEMPLATES.glob("*.theme.j2"))


def test_wlogout_template_is_paint_and_rhythm_only() -> None:
    text = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    for banned in (
        "#lock",
        "#logout",
        "#suspend",
        "#hibernate",
        "#shutdown",
        "#reboot",
        "url(",
        "wallpaper",
        "background-image",
        "grid",
        "margin",
    ):
        assert banned not in text, f"wlogout template contains structural token {banned!r}"


def test_static_wlogout_stylesheet_does_not_own_skin_paint_or_rhythm() -> None:
    """The generated sheet owns paint/rhythm/type; the static sheet owns structure.

    W-2.6 regression: importing `appearance.css` last is not enough while the
    static sheet still declares the pre-skin colour, background, border,
    radius, padding, font, shadow and opacity. Comments are stripped first so
    prose naming a property does not count as a declaration.
    """
    static = (ROOT / "templates" / "wlogout" / "style.css.tpl").read_text()
    body = re.sub(r"/\*.*?\*/", "", static, flags=re.DOTALL)

    forbidden = re.compile(
        r"(?mi)^\s*(?:"
        r"border(?:-[a-z-]+)?|"
        r"padding(?:-[a-z-]+)?|"
        r"color|"
        r"background-color|"
        r"box-shadow|"
        r"opacity|"
        r"font(?:-(?:family|size|weight))?"
        r")\s*:"
    )
    offenders = [match.group(0).strip() for match in forbidden.finditer(body)]
    assert offenders == [], f"static wlogout sheet still owns paint/rhythm: {offenders}"

    for name in ("SYSTEM_FONT_FAMILY", "FONT_SIZE_PX"):
        assert name not in static, f"static wlogout sheet still reads {name}"

    # App-owned structure must survive the paint removal.
    for needle in (
        '@import url("{{COLORS_FILE_PATH}}");',
        'background-image: url("{{CURRENT_WALLPAPER_SYMLINK}}");',
        "background-size: cover;",
        "background-position: center;",
        "background-repeat: no-repeat;",
        "background-size: 20%;",
        "background-size: 30%;",
        "-gtk-icon-effect: none;",
        "animation: gradient_f",
        "transition:",
        "background-image: image(url(\"{{STATE_ROOT}}/dotfiles/current/icons/lock.svg\"));",
        "background-image: image(url(\"{{STATE_ROOT}}/dotfiles/current/icons/reboot.svg\"));",
    ):
        assert needle in static, f"static wlogout sheet dropped app-owned structure: {needle}"

    # The palette fallback stays first; the generated skin stays last.
    assert body.lstrip().startswith('@import url("{{COLORS_FILE_PATH}}");')
    assert body.rstrip().endswith('@import url("appearance.css");')


def _gtk3_parsing_errors(css_path: Path) -> list[str]:
    gi = pytest.importorskip("gi")
    try:
        gi.require_version("Gtk", "3.0")
    except ValueError:  # Gtk 4 already loaded in this interpreter
        pytest.skip("GTK3 namespace unavailable")
    from gi.repository import Gtk

    provider = Gtk.CssProvider()
    problems: list[str] = []
    provider.connect(
        "parsing-error",
        lambda _provider, _section, error: problems.append(error.message),
    )
    assert provider.load_from_path(str(css_path)) is True
    return problems


def _write_wlogout_render_tree(tmp_path: Path) -> tuple[Path, Path]:
    """Write the static sheet with real palette/wallpaper/icon paths."""
    colors = tmp_path / "colors.gtk.css"
    roles = (
        "surface",
        "surface_container",
        "surface_container_high",
        "surface_container_low",
        "surface_container_lowest",
        "on_surface",
        "primary",
        "primary_container",
        "on_primary_container",
        "shadow",
    )
    colors.write_text(
        "\n".join(f"@define-color {role} #202830;" for role in roles) + "\n"
    )

    icons = tmp_path / "state" / "dotfiles" / "current" / "icons"
    icons.mkdir(parents=True)
    for tile in ("lock", "logout", "suspend", "hibernate", "shutdown", "reboot"):
        shutil.copy2(
            ROOT / "icons" / "templates" / "wlogout" / tile / "default" / "icon.svg",
            icons / f"{tile}.svg",
        )

    static = (ROOT / "templates" / "wlogout" / "style.css.tpl").read_text()
    static_css = (
        static.replace("{{COLORS_FILE_PATH}}", str(colors))
        .replace("{{CURRENT_WALLPAPER_SYMLINK}}", str(icons / "lock.svg"))
        .replace("{{STATE_ROOT}}", str(tmp_path / "state"))
    )
    assert "{{" not in static_css, "unexpanded static wlogout variable"
    sheet = tmp_path / "style.css"
    sheet.write_text(static_css)
    return sheet, tmp_path / "appearance.css"


def test_wlogout_static_and_combined_parse_with_gtk3(tmp_path: Path) -> None:
    sheet, appearance = _write_wlogout_render_tree(tmp_path)
    appearance.write_text("")
    assert _gtk3_parsing_errors(sheet) == []

    template = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    for name in MANIFEST_NAMES:
        appearance.write_text(render(template, name, "dark"))
        assert _gtk3_parsing_errors(sheet) == [], name


def _wlogout_block(css: str, selector: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(selector)}\s*\{{(.*?)^\}}", css)
    assert match is not None, f"missing {selector} block"
    return match.group(1)


def test_wlogout_template_maps_card_fill_and_panel_geometry() -> None:
    text = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    body = _wlogout_block(text, "button")
    for placeholder in (
        "{{SKIN_SURFACE_CARD_BG}}",
        "{{SKIN_SURFACE_CARD_BORDER}}",
        "{{SKIN_SURFACE_PANEL_BORDER_WIDTH}}",
        "{{SKIN_SURFACE_PANEL_RADIUS}}",
        "{{SKIN_SURFACE_CARD_PADDING}}",
    ):
        assert placeholder in body, f"button missing {placeholder}"
    assert "SKIN_SURFACE_CONTROL" not in text, "buttons are cards, not controls"
    for selector in ("button:hover", "button:focus"):
        state = _wlogout_block(text, selector)
        assert "{{SKIN_SURFACE_CARD_BG}}" in state, f"{selector} drops the card background"
    for state in ("HOVER", "FOCUS"):
        assert f"{{{{SKIN_STATE_{state}_FILL}}}}" not in text, (
            f"{state.lower()} fill must not replace a card surface"
        )
        assert f"{{{{SKIN_STATE_{state}_INK}}}}" in text
        assert f"{{{{SKIN_STATE_{state}_RING}}}}" in text
    for token in ("FILL", "INK", "RING"):
        assert f"{{{{SKIN_STATE_SELECTED_{token}}}}}" in text
    for token in ("FONT_FAMILY", "SIZE_TITLE", "FONT_WEIGHT", "LETTER_SPACING"):
        assert f"{{{{SKIN_TYPE_{token}}}}}" in text


@pytest.mark.parametrize(
    (
        "name",
        "fill",
        "border",
        "radius",
        "padding",
        "selected_fill",
        "selected_ink",
    ),
    [
        (
            "glass",
            "alpha(@surface_container_high, 0.18)",
            "1.5px solid alpha(@on_surface, 0.10)",
            "12px",
            "10px",
            "@primary_container",
            "@on_primary_container",
        ),
        (
            "flat",
            "transparent",
            "0px solid transparent",
            "0px",
            "10px",
            "@primary",
            "@on_primary",
        ),
        (
            "paper",
            "@surface_container_low",
            "1px solid alpha(@on_surface, 0.10)",
            "6px",
            "10px",
            "@primary_container",
            "@on_primary_container",
        ),
        (
            "terminal",
            "@surface_container",
            "1px solid alpha(@on_surface, 0.18)",
            "0px",
            "8px",
            "@primary_container",
            "@on_primary_container",
        ),
        (
            "terminal-host",
            "@surface_container",
            "1px solid alpha(@on_surface, 0.18)",
            "0px",
            "8px",
            "@primary_container",
            "@on_primary_container",
        ),
    ],
)
def test_wlogout_button_uses_each_skins_card_fill_and_panel_geometry(
    name: str,
    fill: str,
    border: str,
    radius: str,
    padding: str,
    selected_fill: str,
    selected_ink: str,
) -> None:
    css = render((TEMPLATES / "wlogout.gtk.css.j2").read_text(), name, "dark")
    assert f"background-color: {fill};" in _wlogout_block(css, "button"), name
    assert f"border: {border};" in _wlogout_block(css, "button"), name
    assert f"border-radius: {radius};" in _wlogout_block(css, "button"), name
    assert f"padding: {padding};" in _wlogout_block(css, "button"), name

    for selector in ("button:hover", "button:focus"):
        state = _wlogout_block(css, selector)
        assert f"background-color: {fill};" in state, (
            f"{name}: {selector} lost the card background"
        )
        assert "color: @on_surface;" in state, f"{name}: {selector} ink"
        assert "border-color: @primary;" in state, f"{name}: {selector} ring"

    active = _wlogout_block(css, "button:active")
    assert f"background-color: {selected_fill};" in active, name
    assert f"color: {selected_ink};" in active, name
    assert "border-color: @primary;" in active, name


@pytest.mark.parametrize(
    ("name", "radius", "border"),
    [
        ("terminal-host", 13, 2),
        ("glass", 13, 2),
        ("paper", 13, 2),
        ("terminal", 0, 1),
        ("flat", 0, 0),
    ],
)
def test_wlogout_host_probe_keeps_action_cards_on_panel_geometry(
    name: str, radius: int, border: int
) -> None:
    """wlogout maps action cards to the panel, never to the inner card radius."""
    text = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    tokens = validate_skins._resolve_manifest(
        load_manifest(name), "dark", dict(validate_skins.HOST_PROBE)
    )
    css = validate_skins.expand_template(text, tokens, "css")
    assert "{{" not in css
    button = _wlogout_block(css, "button")
    assert f"border-radius: {radius}px;" in button
    assert f"border: {border}px solid" in button
    assert f"border-radius: {validate_skins.HOST_PROBE['surface.card.radius']}px;" not in button


def test_wlogout_template_expands_card_panel_state_and_type() -> None:
    text = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    glass = render(text, "glass", "dark")
    assert "background-color: alpha(@surface, 0.94);" in glass
    assert "background-color: alpha(@surface_container_high, 0.18);" in _wlogout_block(
        glass, "button:focus"
    )
    assert "border: 1.5px solid alpha(@on_surface, 0.10);" in glass
    assert "border-radius: 12px;" in glass
    assert "padding: 10px;" in glass
    assert "font-size: 12.5px;" in glass
    assert "font-family: inherit;" in glass
    assert "letter-spacing: 0em;" in glass

    terminal = render(text, "terminal", "dark")
    assert "background-color: @surface_container;" in _wlogout_block(
        terminal, "button:focus"
    )
    assert "border: 1px solid alpha(@on_surface, 0.18);" in terminal
    assert "border-radius: 0px;" in terminal
    assert "padding: 8px;" in terminal
    assert "font-family: JetBrainsMono Nerd Font, monospace;" in terminal
    assert "font-size: 13px;" in terminal
    assert "background-color: @primary_container;" in _wlogout_block(
        terminal, "button:active"
    )
    assert "color: @on_primary_container;" in _wlogout_block(terminal, "button:active")


def test_wlogout_focused_card_keeps_card_background_with_gtk3(
    tmp_path: Path,
) -> None:
    """W-2.19: a focused card keeps the card background; only ring/ink move."""
    gi = pytest.importorskip("gi")
    try:
        gi.require_version("Gtk", "3.0")
    except ValueError:  # Gtk 4 already loaded in this interpreter
        pytest.skip("GTK3 namespace unavailable")
    from gi.repository import Gtk

    initialised, _argv = Gtk.init_check()
    if not initialised:
        pytest.skip("no GDK display for the GTK3 style probe")

    template = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    appearance = render(template, "terminal", "dark")
    probe = tmp_path / "probe.css"
    probe.write_text(
        "\n".join(
            (
                "@define-color surface #101820;",
                "@define-color surface_container #202830;",
                "@define-color on_surface #d0d8e0;",
                "@define-color primary #88aaff;",
                "@define-color primary_container #304860;",
                "@define-color on_primary_container #d8e8f8;",
            )
        )
        + "\n"
        + appearance
    )
    provider = Gtk.CssProvider()
    assert provider.load_from_path(str(probe)) is True

    window = Gtk.Window()
    button = Gtk.Button(label="probe")
    window.add(button)
    context = button.get_style_context()
    context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    normal = context.get_background_color(Gtk.StateFlags.NORMAL)
    focused = context.get_background_color(Gtk.StateFlags.FOCUSED)
    assert (normal.red, normal.green, normal.blue, normal.alpha) == pytest.approx(
        (focused.red, focused.green, focused.blue, focused.alpha)
    ), "focused card lost the card background"
    assert (normal.red, normal.green, normal.blue, normal.alpha) == pytest.approx(
        (0x20 / 255, 0x28 / 255, 0x30 / 255, 1.0)
    ), "focused card background is not the terminal card fill"
    ring = context.get_border_color(Gtk.StateFlags.FOCUSED)
    assert (ring.red, ring.green, ring.blue) == pytest.approx(
        (0x88 / 255, 0xAA / 255, 0xFF / 255)
    ), "focused card ring did not move to the focus ring"


def test_terminal_host_applies_host_radius_and_keeps_terminal_card_fill_with_gtk3(
    tmp_path: Path,
) -> None:
    """Host geometry is applied for terminal-host; card paint stays terminal's."""
    gi = pytest.importorskip("gi")
    try:
        gi.require_version("Gtk", "3.0")
    except ValueError:  # Gtk 4 already loaded in this interpreter
        pytest.skip("GTK3 namespace unavailable")
    from gi.repository import Gtk

    initialised, _argv = Gtk.init_check()
    if not initialised:
        pytest.skip("no GDK display for the GTK3 style probe")

    template = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    terminal_css = render(template, "terminal", "dark")
    host = dict(validate_skins.HOST_PROBE)
    host_tokens = validate_skins._resolve_manifest(
        load_manifest("terminal-host"), "dark", host
    )
    terminal_host_css = validate_skins.expand_template(template, host_tokens)
    assert "{{" not in terminal_host_css

    # The host values reach the action cards only through panel geometry; the
    # delegated card/control/cell radii do not replace the panel mapping.
    button = _wlogout_block(terminal_host_css, "button")
    assert "border-radius: 13px;" in button
    assert "border-radius: 14px;" not in button
    assert "border-radius: 15px;" not in button
    assert "border-radius: 16px;" not in button
    assert "border: 2px solid alpha(@on_surface, 0.18);" in button
    assert "background-color: @surface_container;" in button
    assert "padding: 8px;" in button

    palette = "\n".join(
        (
            "@define-color surface #101820;",
            "@define-color surface_container #202830;",
            "@define-color on_surface #d0d8e0;",
            "@define-color primary #88aaff;",
            "@define-color primary_container #304860;",
            "@define-color on_primary_container #d8e8f8;",
        )
    ) + "\n"
    providers = []
    for name, css in (("terminal", terminal_css), ("terminal-host", terminal_host_css)):
        probe = tmp_path / f"{name}.css"
        probe.write_text(palette + css)
        provider = Gtk.CssProvider()
        assert provider.load_from_path(str(probe)) is True, name
        providers.append(provider)

    window = Gtk.Window()
    card = Gtk.Button(label="probe")
    window.add(card)
    context = card.get_style_context()
    computed = []
    for provider in providers:
        context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        colour = context.get_background_color(Gtk.StateFlags.NORMAL)
        computed.append((colour.red, colour.green, colour.blue, colour.alpha))
    assert computed[0] == pytest.approx(computed[1]), (
        "terminal-host changed the terminal card fill"
    )
    assert computed[0] == pytest.approx((0x20 / 255, 0x28 / 255, 0x30 / 255, 1.0))



def test_missing_wlogout_template_fails_the_required_target_gate(tmp_path: Path) -> None:
    root = make_full_root(tmp_path, drop_template="wlogout")
    errors = errors_for(root)
    assert any("missing required target(s) ['wlogout']" in error for error in errors), errors


def test_missing_gtk_target_fails_the_required_target_gate(tmp_path: Path) -> None:
    root = make_full_root(tmp_path, drop_template="gtk3")
    errors = errors_for(root)
    assert any("missing required target(s) ['gtk3']" in error for error in errors), errors


def test_missing_rofi_artifact_fails_the_required_artifact_gate(tmp_path: Path) -> None:
    root = make_full_root(tmp_path, drop_artifact="rofi")
    errors = errors_for(root)
    assert any(
        "missing required artifact(s) ['rofi:rasi']" in error for error in errors
    ), errors


def test_schema_without_required_artifacts_fails(tmp_path: Path) -> None:
    data = schema()
    del data["frozen"]["required_artifacts"]
    bad_schema = tmp_path / "schema-no-artifacts.json"
    bad_schema.write_text(json.dumps(data))
    root = make_full_root(tmp_path, schema_override=bad_schema)
    errors = errors_for(root)
    assert any("frozen.required_artifacts" in error for error in errors), errors


def test_unregistered_extra_artifact_fails(tmp_path: Path) -> None:
    root = make_full_root(tmp_path)
    (root / "skins" / "templates" / "btop.conf.j2").write_text(
        "font_family {{SKIN_TYPE_FONT_FAMILY}}\n"
    )
    errors = errors_for(root)
    assert any(
        "unregistered artifact(s) ['btop:conf']" in error for error in errors
    ), errors


def test_schema_without_required_targets_fails(tmp_path: Path) -> None:
    data = schema()
    del data["frozen"]["required_targets"]
    bad_schema = tmp_path / "schema-no-targets.json"
    bad_schema.write_text(json.dumps(data))
    root = make_full_root(tmp_path, schema_override=bad_schema)
    errors = errors_for(root)
    assert any("frozen.required_targets" in error for error in errors), errors


def test_unregistered_extra_target_fails(tmp_path: Path) -> None:
    data = schema()
    data["frozen"]["required_targets"].remove("wlogout")
    bad_schema = tmp_path / "schema-no-wlogout.json"
    bad_schema.write_text(json.dumps(data))
    root = make_full_root(tmp_path, schema_override=bad_schema)
    errors = errors_for(root)
    assert any("unregistered target(s) ['wlogout']" in error for error in errors), errors


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
    assert data["frozen"]["required_files"] == [
        "glass",
        "flat",
        "paper",
        "terminal",
        "terminal-host",
    ]
    canonical = data["canonical"]
    assert canonical["repository"] == "contracts"
    assert set(canonical["paths"]) == {
        "schemas/appearance-manifest.schema.json",
        "schemas/appearance-json.schema.json",
        "schemas/appearance-artifact.schema.json",
        "schemas/generation-manifest.schema.json",
        "schemas/skin-token.schema.json",
        "schemas/skin-manifest.schema.json",
        "schemas/skin-json.schema.json",
    }
    assert canonical["vendored"] is True
    assert canonical["tag"] == "v0.12.0"
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
    assert metadata["source-commit"] == "a03b5632828df8012c02a6117c3be438eca4264b"
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


HOST_PATHS = [
    "surface.window.radius",
    "surface.window.border-width",
    "surface.panel.radius",
    "surface.panel.border-width",
    "surface.card.radius",
    "surface.control.radius",
    "surface.cell.radius",
]


def test_host_policy_is_a_policy_object_not_a_token_group() -> None:
    glass = load_manifest("glass")
    paper = load_manifest("paper")
    terminal_host = load_manifest("terminal-host")
    expected = {"inherit": HOST_PATHS, "fallback": "skin"}
    assert glass["host"] == expected
    assert paper["host"] == expected
    assert terminal_host["host"] == expected

    for name in MANIFEST_NAMES:
        manifest = load_manifest(name)
        assert "host" not in manifest["groups"], name
        assert "host" not in resolved(name, "dark"), name

    for name in ("flat", "terminal"):
        assert "host" not in load_manifest(name), name

    manifest_schema = json.loads(
        (CONTRACTS / "appearance-manifest.schema.json").read_text()
    )
    assert "host" in manifest_schema["properties"]
    ref = manifest_schema["properties"]["host"]["$ref"].split("/")[-1]
    policy = manifest_schema["definitions"][ref]
    assert policy["required"] == ["inherit"]
    assert policy["additionalProperties"] is False
    assert policy["properties"]["inherit"]["minItems"] == 1
    assert policy["properties"]["inherit"]["uniqueItems"] is True
    assert policy["properties"]["inherit"]["items"]["enum"] == HOST_PATHS
    assert policy["properties"]["fallback"]["enum"] == ["skin", "error"]
    assert validate_skins.HOST_INHERITABLE == tuple(HOST_PATHS)
    assert "surface.pill.radius" not in validate_skins.HOST_INHERITABLE


def test_terminal_host_is_terminal_plus_only_the_host_policy() -> None:
    terminal = load_manifest("terminal")
    terminal_host = load_manifest("terminal-host")
    assert terminal_host["name"] == "terminal-host"
    assert terminal_host["groups"] == terminal["groups"]
    assert "host" not in terminal
    assert terminal_host["host"] == {
        "inherit": HOST_PATHS,
        "fallback": "skin",
    }
    assert "mode" not in terminal_host


def test_host_values_resolve_only_into_inherited_rectangle_geometry() -> None:
    host = dict(validate_skins.HOST_PROBE)
    for name in MANIFEST_NAMES:
        manifest = load_manifest(name)
        for mode in ("dark", "light"):
            base = validate_skins._resolve_manifest(manifest, mode)
            with_host = validate_skins._resolve_manifest(manifest, mode, host)
            if "host" not in manifest:
                assert with_host == base, f"{name}:{mode} must ignore host values"
                continue

            base_leaves = dict(validate_skins._leaves(base))
            host_leaves = dict(validate_skins._leaves(with_host))
            changed = {
                path
                for path, value in base_leaves.items()
                if host_leaves.get(path) != value
            }
            mode_groups = manifest.get("mode", {}).get(mode, {})
            if "surface" in mode_groups:
                assert changed == set(), f"{name}:{mode} mode override must win"
            else:
                assert changed == set(host), f"{name}:{mode}: {changed}"

    terminal_host = validate_skins._resolve_manifest(
        load_manifest("terminal-host"), "dark", host
    )
    assert terminal_host["surface"]["window"]["radius"] == 17
    assert terminal_host["surface"]["window"]["border-width"] == 3
    assert terminal_host["surface"]["panel"]["radius"] == 13
    assert terminal_host["surface"]["panel"]["border-width"] == 2
    assert terminal_host["surface"]["card"]["radius"] == 14
    assert terminal_host["surface"]["control"]["radius"] == 15
    assert terminal_host["surface"]["cell"]["radius"] == 16
    assert terminal_host["surface"]["pill"]["radius"] == 2

    # The original terminal is explicit: even with host values supplied it
    # keeps its square/hairline geometry.
    terminal = validate_skins._resolve_manifest(load_manifest("terminal"), "dark", host)
    assert terminal["surface"]["window"]["radius"] == 0
    assert terminal["surface"]["window"]["border-width"] == 1
    assert terminal["surface"]["panel"]["radius"] == 0
    assert terminal["surface"]["panel"]["border-width"] == 1
    assert terminal["surface"]["card"]["radius"] == 0
    assert terminal["surface"]["control"]["radius"] == 2
    assert terminal["surface"]["cell"]["radius"] == 0

    # paper's light surface override wins over the host policy for every
    # delegated rectangle path.
    paper_light = validate_skins._resolve_manifest(
        load_manifest("paper"), "light", host
    )
    assert paper_light["surface"]["window"]["radius"] == 6
    assert paper_light["surface"]["window"]["border-width"] == 1
    assert paper_light["surface"]["panel"]["radius"] == 6
    assert paper_light["surface"]["panel"]["border-width"] == 1
    assert paper_light["surface"]["card"]["radius"] == 4
    assert paper_light["surface"]["control"]["radius"] == 3
    assert paper_light["surface"]["cell"]["radius"] == 3


def test_host_fallback_skin_keeps_skin_values_when_the_host_is_silent() -> None:
    manifest = load_manifest("terminal-host")
    base = validate_skins._resolve_manifest(manifest, "dark")
    silent = validate_skins._resolve_manifest(manifest, "dark", {})
    partial = validate_skins._resolve_manifest(
        manifest,
        "dark",
        {"surface.panel.radius": 9, "surface.card.radius": 10},
    )
    assert silent == base
    assert partial["surface"]["window"]["radius"] == 0
    assert partial["surface"]["window"]["border-width"] == 1
    assert partial["surface"]["panel"]["radius"] == 9
    assert partial["surface"]["panel"]["border-width"] == 1
    assert partial["surface"]["card"]["radius"] == 10
    assert partial["surface"]["control"]["radius"] == 2
    assert partial["surface"]["cell"]["radius"] == 0

    error_policy = dict(manifest)
    error_policy["host"] = {
        "inherit": HOST_PATHS,
        "fallback": "error",
    }
    with pytest.raises(ValueError, match="fallback = \"error\""):
        validate_skins._resolve_manifest(error_policy, "dark", {})


def test_positive_host_fixture_is_accepted(tmp_path: Path) -> None:
    fixture = POSITIVE / "host.toml"
    with fixture.open("rb") as handle:
        fixture_data = tomllib.load(handle)
    assert fixture_data == load_manifest("glass")

    root = make_full_root(tmp_path, manifest_override=("glass", fixture))
    errors, _notes, stats = validate_skins.validate(root)
    assert errors == []
    assert stats["manifests"] == 5


def test_positive_host_rectangles_fixture_is_accepted(tmp_path: Path) -> None:
    fixture = POSITIVE / "host-rectangles.toml"
    with fixture.open("rb") as handle:
        fixture_data = tomllib.load(handle)
    assert fixture_data == load_manifest("glass")
    assert fixture_data["host"]["inherit"] == HOST_PATHS

    root = make_full_root(tmp_path, manifest_override=("glass", fixture))
    errors, _notes, stats = validate_skins.validate(root)
    assert errors == []
    assert stats["manifests"] == 5


def test_resolved_tokens_validate_for_every_manifest_and_mode() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    token_schema = json.loads((CONTRACTS / "appearance-json.schema.json").read_text())
    jsonschema.Draft7Validator.check_schema(token_schema)
    validator = jsonschema.Draft7Validator(token_schema)
    for name in MANIFEST_NAMES:
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
    for name in MANIFEST_NAMES:
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
    for role in ("window", "panel", "card", "cell", "control", "pill"):
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


@pytest.mark.parametrize("name", MANIFEST_NAMES)
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
    assert glass["groups"]["surface"]["window"] == {
        "bg": "alpha(@surface, 0.94)",
        "border": "@primary",
        "border-width": 1.5,
        "radius": 12,
        "padding": 11,
        "shadow": "none",
        "blur": "none",
        "opacity": 0.94,
    }
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


def test_frozen_terminal_values() -> None:
    terminal = load_manifest("terminal")
    assert terminal["schemaVersion"] == 2
    assert terminal["name"] == "terminal"
    assert terminal["groups"]["surface"]["panel"] == {
        "bg": "@surface",
        "border": "alpha(@on_surface, 0.22)",
        "border-width": 1,
        "radius": 0,
        "padding": 9,
        "shadow": "none",
        "blur": "none",
    }
    assert terminal["groups"]["surface"]["card"] == {
        "bg": "@surface_container",
        "border": "alpha(@on_surface, 0.18)",
        "border-width": 1,
        "radius": 0,
        "padding": 8,
    }
    assert terminal["groups"]["surface"]["cell"] == {
        "bg": "transparent",
        "border": "transparent",
        "border-width": 0,
        "radius": 0,
        "padding": 5,
        "hover-bg": "alpha(@on_surface, 0.10)",
    }
    assert terminal["groups"]["surface"]["control"] == {
        "bg": "transparent",
        "border": "alpha(@on_surface, 0.30)",
        "border-width": 1,
        "radius": 2,
        "padding": 3,
        "font-size": 10,
        "font-weight": 600,
    }
    assert terminal["groups"]["surface"]["pill"] == {
        "bg": "alpha(@on_surface, 0.12)",
        "border": "alpha(@on_surface, 0.18)",
        "border-width": 1,
        "radius": 2,
        "padding": 1,
        "font-size": 9,
        "letter-spacing": 0.04,
    }
    assert terminal["groups"]["state"]["hover"] == {
        "fill": "alpha(@on_surface, 0.10)",
        "ink": "@on_surface",
        "ring": "@primary",
    }
    assert terminal["groups"]["state"]["selected"] == {
        "fill": "@primary_container",
        "ink": "@on_primary_container",
        "ring": "@primary",
    }
    assert terminal["groups"]["state"]["focus"] == {
        "fill": "transparent",
        "ink": "@on_surface",
        "ring": "@primary",
    }
    assert terminal["groups"]["state"]["disabled"] == {
        "fill": "alpha(@on_surface, 0.06)",
        "ink": "alpha(@on_surface, 0.38)",
        "ring": "transparent",
    }
    assert terminal["groups"]["type"] == {
        "font-family": "JetBrainsMono Nerd Font, monospace",
        "font-weight": 500,
        "letter-spacing": 0,
        "size-caption": 9,
        "size-meta": 10,
        "size-body": 12,
        "size-title": 13,
        "size-display": 14,
    }
    assert terminal["groups"]["ink"] == {
        "ink": "@on_surface",
        "ink-dim": "alpha(@on_surface, 0.62)",
        "accent": "@primary",
        "accent-muted": "alpha(@primary, 0.5)",
        "ink-over": "auto",
    }
    assert terminal["groups"]["layout"] == {
        "ags": {"panel-width": 312, "bt-list-spacing": 4},
        "ags-clipboard": {"card-width": 260},
        "ags-notifications": {"card-width": 380},
        "ags-wallpaper-selector": {"root-width": 960, "root-height": 640},
        "ags-icme": {"root-width": 1280, "root-height": 800},
    }
    assert "mode" not in terminal


def test_terminal_expands_with_its_dense_monospace_shape() -> None:
    css = render(TEMPLATE.read_text(), "terminal")
    assert "background-color: @surface;" in css
    assert "background-color: @surface_container;" in css
    assert "border: 1px solid alpha(@on_surface, 0.22);" in css
    assert "border: 1px solid alpha(@on_surface, 0.30);" in css
    assert "border-radius: 0px;" in css
    assert "border-radius: 2px;" in css
    assert "padding: 9px;" in css
    assert "font-family: JetBrainsMono Nerd Font, monospace;" in css
    assert "font-size: 9px;" in css
    assert "font-size: 10px;" in css
    assert "font-size: 12px;" in css
    assert "font-size: 13px;" in css
    assert "font-size: 14px;" in css
    assert "letter-spacing: 0.04em;" in css
    # Mode-agnostic: both modes expand from the same base groups.
    assert render(TEMPLATE.read_text(), "terminal", "light") == css


def test_positive_terminal_host_fixture_is_accepted(tmp_path: Path) -> None:
    fixture = POSITIVE / "terminal-host.toml"
    with fixture.open("rb") as handle:
        fixture_data = tomllib.load(handle)
    assert fixture_data == load_manifest("terminal-host")

    root = make_full_root(tmp_path, manifest_override=("terminal-host", fixture))
    errors, _notes, stats = validate_skins.validate(root)
    assert errors == []
    assert stats["manifests"] == 5


def test_terminal_host_expands_like_terminal_until_the_host_supplies_geometry() -> None:
    template = TEMPLATE.read_text()
    terminal = render(template, "terminal")
    terminal_host_fallback = render(template, "terminal-host")
    assert terminal_host_fallback == terminal

    host = dict(validate_skins.HOST_PROBE)
    tokens = validate_skins._resolve_manifest(
        load_manifest("terminal-host"), "dark", host
    )
    terminal_host = validate_skins.expand_template(template, tokens)
    assert "{{" not in terminal_host
    assert "border-radius: 13px;" in terminal_host
    assert "border: 2px solid alpha(@on_surface, 0.22);" in terminal_host
    # The host moves every rectangle radius; paint, type and the pill stay put.
    assert "background-color: @surface_container;" in terminal_host
    assert "border-radius: 14px;" in terminal_host
    assert "border-radius: 15px;" in terminal_host
    assert "border-radius: 16px;" in terminal_host
    assert "border-radius: 2px;" in terminal_host
    assert "font-family: JetBrainsMono Nerd Font, monospace;" in terminal_host
    # The host radius reaches every panel-role surface: the settings panel plus
    # the REQ-005 sound popover/tray/settings and their menu (doc 113 W-10).
    for selector in (".settings-surface", ".audio-surface", ".tray-surface",
                     ".audio-settings", ".audio-menu > contents"):
        assert "border-radius: 13px;" in _rule(terminal_host, selector), selector


def test_positive_terminal_fixture_is_accepted(tmp_path: Path) -> None:
    fixture = POSITIVE / "terminal.toml"
    with fixture.open("rb") as handle:
        fixture_data = tomllib.load(handle)
    assert fixture_data == load_manifest("terminal")

    root = make_full_root(tmp_path, manifest_override=("terminal", fixture))
    errors, _notes, stats = validate_skins.validate(root)
    assert errors == []
    assert stats["manifests"] == 5


def test_positive_wlogout_fixture_matches_and_expands() -> None:
    fixture = POSITIVE / "wlogout.gtk.css.j2"
    shipped = TEMPLATES / "wlogout.gtk.css.j2"
    assert fixture.read_text() == shipped.read_text()
    for name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            css = render(fixture.read_text(), name, mode)
            assert "{{" not in css, f"wlogout fixture: {name}:{mode}"


def test_layout_defaults_preserve_the_apps_pre_v2_window_sizes() -> None:
    """Every skin keeps the app defaults; only paint/rhythm differs per skin."""
    for name in MANIFEST_NAMES:
        layout = load_manifest(name)["groups"]["layout"]
        assert layout["ags-icme"] == {"root-width": 1280, "root-height": 800}, name
        assert layout["ags-wallpaper-selector"] == {
            "root-width": 960,
            "root-height": 640,
        }, name
        # Retired v1 knobs: no app source reads them.
        assert "bar-row-height" not in layout["ags"], name
        assert "chip-min" not in layout["ags"], name
        # Real TSX literals stay; the CSS-derived cleanup candidates are gone
        # in v0.13.0 (the apps are corrected to their pre-v2 natural layout).
        assert layout["ags"] == {
            "panel-width": 312,
            "bt-list-spacing": 4 if name != "paper" else 6,
        }, name
        assert layout["ags-clipboard"] == {"card-width": 260}, name
        assert layout["ags-notifications"] == {"card-width": 380}, name
        assert "ags-capture" not in layout, name
        assert "ags-btop-studio" not in layout, name


def test_paper_declares_explicit_light_mode_overrides() -> None:
    paper = load_manifest("paper")
    assert "light" in paper["mode"]
    assert set(paper["mode"]["light"]) == {"surface", "state", "ink"}
    light = paper["mode"]["light"]

    # A complete same-shape surface group, not a partial merge.
    assert set(light["surface"]) == {"window", "panel", "card", "cell", "control", "pill"}
    assert light["surface"]["window"]["border"] == "alpha(@on_surface, 0.16)"
    assert light["surface"]["window"]["opacity"] == 1.0
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
# Window role and the kitty conf projection
# --------------------------------------------------------------------------- #


WINDOW_TOKENS = {
    "bg",
    "border",
    "border-width",
    "radius",
    "padding",
    "shadow",
    "blur",
    "opacity",
}


def test_every_manifest_has_the_required_window_group() -> None:
    for name in MANIFEST_NAMES:
        surface = load_manifest(name)["groups"]["surface"]
        assert set(surface["window"]) == WINDOW_TOKENS, name
        assert 0 <= surface["window"]["opacity"] <= 1, name

    paper_light = load_manifest("paper")["mode"]["light"]["surface"]
    assert set(paper_light["window"]) == WINDOW_TOKENS
    assert paper_light["window"]["opacity"] == 1.0


def test_missing_window_group_or_token_fails(tmp_path: Path) -> None:
    glass = (MANIFESTS / "glass.toml").read_text()
    missing_group = re.sub(
        r"\[groups\.surface\.window\][\s\S]*?(?=\[groups\.surface\.card\])",
        "",
        glass,
        count=1,
    )
    assert "[groups.surface.window]" not in missing_group
    fixture = tmp_path / "missing-window.toml"
    fixture.write_text(missing_group)
    root = make_root(tmp_path, manifest_override=("glass", fixture))
    errors = errors_for(root)
    assert any("missing required property 'window'" in error for error in errors), errors

    window = re.search(
        r"\[groups\.surface\.window\][\s\S]*?(?=\[groups\.surface\.card\])",
        glass,
    )
    assert window is not None
    missing_token = glass.replace(
        window.group(0), window.group(0).replace("opacity = 0.94\n", "")
    )
    fixture.write_text(missing_token)
    root = make_root(tmp_path / "second", manifest_override=("glass", fixture))
    errors = errors_for(root)
    assert any("missing required property 'opacity'" in error for error in errors), errors


def test_window_opacity_is_a_unitless_bounded_number() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    manifest_schema = json.loads(
        (CONTRACTS / "appearance-manifest.schema.json").read_text()
    )
    validator = jsonschema.Draft7Validator(manifest_schema)
    for bad in ("0.94", -0.1, 1.1):
        manifest = load_manifest("glass")
        manifest["groups"]["surface"]["window"]["opacity"] = bad
        errors = list(validator.iter_errors(manifest))
        assert errors, f"window opacity {bad!r} must be rejected"


def test_outer_consumers_use_the_window_role() -> None:
    rofi = (TEMPLATES / "rofi.rasi.j2").read_text()
    window = _wlogout_block(rofi, "window")
    for token in (
        "SKIN_SURFACE_WINDOW_BG",
        "SKIN_SURFACE_WINDOW_BORDER",
        "SKIN_SURFACE_WINDOW_BORDER_WIDTH",
        "SKIN_SURFACE_WINDOW_RADIUS",
        "SKIN_SURFACE_WINDOW_PADDING",
    ):
        assert "{{" + token + "}}" in window, token
    assert "SKIN_SURFACE_PANEL" not in window

    wlogout = (TEMPLATES / "wlogout.gtk.css.j2").read_text()
    assert "{{SKIN_SURFACE_WINDOW_BG}}" in _wlogout_block(wlogout, "window")
    assert "{{SKIN_SURFACE_PANEL_BG}}" not in _wlogout_block(wlogout, "window")

    for name in ("gtk3.gtk.css.j2", "gtk4.gtk.css.j2"):
        text = (TEMPLATES / name).read_text()
        assert "@define-color skin_window_bg {{SKIN_SURFACE_WINDOW_BG}}" in text, name
        window = _wlogout_block(text, "window")
        assert "@skin_window_bg" in window or "@window_bg_color" in window, name
        headerbar = _wlogout_block(text, "headerbar")
        assert "@skin_window_bg" in headerbar or "@headerbar_bg_color" in headerbar, name
        assert "{{SKIN_SURFACE_WINDOW_BORDER_WIDTH}}" in headerbar, name
        assert "@skin_window_border" in headerbar, name


def test_kitty_conf_template_is_paint_free_and_projects_four_options() -> None:
    text = (TEMPLATES / "kitty.conf.j2").read_text()
    assert not HEX.search(text)
    for token in ("SKIN_TYPE_FONT_FAMILY", "SKIN_TYPE_SIZE_BODY",
                  "SKIN_SURFACE_WINDOW_PADDING", "SKIN_SURFACE_WINDOW_OPACITY"):
        assert "{{" + token + "}}" in text, token
    assert "SKIN_SURFACE_WINDOW_BG" not in text
    assert "SKIN_SURFACE_PANEL" not in text


@pytest.mark.parametrize(
    ("name", "mode", "family", "size", "padding", "opacity"),
    [
        ("glass", "dark", "monospace", "9.75", "8.25", "0.94"),
        ("flat", "dark", "Cantarell", "9.75", "8.25", "1"),
        ("paper", "dark", "Cantarell", "9.75", "8.25", "1"),
        ("paper", "light", "Cantarell", "9.75", "8.25", "1"),
        ("terminal", "dark", "JetBrainsMono Nerd Font", "9", "6.75", "1"),
        ("terminal-host", "dark", "JetBrainsMono Nerd Font", "9", "6.75", "1"),
    ],
)
def test_kitty_projection_values(
    name: str, mode: str, family: str, size: str, padding: str, opacity: str
) -> None:
    text = (TEMPLATES / "kitty.conf.j2").read_text()
    rendered = render(text, name, mode, "conf")
    assert rendered.splitlines()[-4:] == [
        f"font_family {family}",
        f"font_size {size}",
        f"window_padding_width {padding}",
        f"background_opacity {opacity}",
    ], rendered


def test_kitty_font_family_and_point_rules() -> None:
    family = validate_skins._conf_font_family
    assert family("inherit") == "monospace"
    assert family('system-ui, "Cantarell", "Noto Sans", sans-serif') == "Cantarell"
    assert family("JetBrainsMono Nerd Font, monospace") == "JetBrainsMono Nerd Font"
    assert family('"Noto Sans", sans-serif') == "Noto Sans"
    assert family("monospace, serif") == "monospace"

    value = validate_skins._conf_token_value
    assert value("type.size-body", 12) == "9"
    assert value("type.size-body", 12.5) == "9.38"
    assert value("type.size-body", 13) == "9.75"
    assert value("surface.window.padding", 11) == "8.25"
    assert value("type.size-body", 1) == "6"
    assert value("type.size-body", 100) == "36"
    assert value("surface.window.padding", 100) == "32"
    assert value("surface.window.opacity", 0.94) == "0.94"
    assert value("surface.window.opacity", 1.0) == "1"


def test_kitty_artifact_parses_with_kitty_runpy(tmp_path: Path) -> None:
    kitty = shutil.which("kitty")
    if kitty is None:
        pytest.skip("kitty is not installed")
    text = (TEMPLATES / "kitty.conf.j2").read_text()
    for name in MANIFEST_NAMES:
        for mode in ("dark", "light"):
            path = tmp_path / f"{name}-{mode}.conf"
            path.write_text(render(text, name, mode, "conf"))
            script = (
                "from kitty.config import load_config\n"
                f"b = []\nload_config({str(path)!r}, accumulate_bad_lines=b)\n"
                "print(len(b))\n"
            )
            result = subprocess.run(
                [kitty, "+runpy", script],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stderr
            assert result.stdout.strip() == "0", result.stdout
            assert "Ignoring unknown config key" not in result.stderr, result.stderr


def test_kitty_runpy_reports_an_unknown_key(tmp_path: Path) -> None:
    kitty = shutil.which("kitty")
    if kitty is None:
        pytest.skip("kitty is not installed")
    path = tmp_path / "bad.conf"
    path.write_text("font_family monospace\nnot_a_kitty_key 1\n")
    script = (
        "from kitty.config import load_config\n"
        f"b = []\nload_config({str(path)!r}, accumulate_bad_lines=b)\n"
        "print(len(b))\n"
    )
    result = subprocess.run(
        [kitty, "+runpy", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "Ignoring unknown config key: not_a_kitty_key" in result.stderr, result.stderr


def test_missing_kitty_artifact_fails_the_required_artifact_gate(tmp_path: Path) -> None:
    root = make_full_root(tmp_path, drop_artifact="kitty")
    errors = errors_for(root)
    assert any(
        "missing required artifact(s) ['kitty:conf']" in error for error in errors
    ), errors


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
        ("host-empty-inherit.toml", "at least 1 item"),
        ("host-duplicate-inherit.toml", "duplicate items"),
        ("host-unknown-inherit.toml", "surface.card.border-width"),
        ("host-pill-radius.toml", "surface.pill.radius"),
        ("host-bad-fallback.toml", "must be one of"),
        ("host-extra-key.toml", "unexpected property"),
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
        ("literal-hex.gtk.css.j2", "literal hex colour"),
        ("structure.gtk.css.j2", "structure/variant property"),
        ("unknown-placeholder.gtk.css.j2", "is not a token"),
        ("layout-placeholder.gtk.css.j2", "layout token"),
        ("ags-bar.css.j2", "template name"),
        ("format/gtk3-var/gtk3.gtk.css.j2", "GTK3 var()"),
        ("format/gtk3-mix/gtk3.gtk.css.j2", "GTK3 color-mix()"),
        ("format/gtk4-selector/gtk4.gtk.css.j2", "outside the conservative GTK allowlist"),
        ("format/gtk4-size/gtk4.gtk.css.j2", "layout/size property"),
        ("format/rofi-alpha/rofi.rasi.j2", "must not contain alpha()"),
        ("format/rofi-underscore/rofi.rasi.j2", "hyphenated role names"),
        ("format/rofi-hex/rofi.rasi.j2", "literal hex colour"),
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
