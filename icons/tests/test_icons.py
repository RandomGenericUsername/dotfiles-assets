"""Icon corpus tests for the sound-panel controls and settings gear."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ICONS = ROOT / "icons"
MANIFEST = yaml.safe_load((ICONS / "mappings/icons.yaml").read_text())
TEMPLATES = ICONS / "templates"


def _group(name: str) -> dict:
    return MANIFEST[name]


def _variants(name: str) -> dict[str, dict]:
    return {variant["name"]: variant for variant in _group(name)["variants"]}


def test_media_controls_carry_active_and_shape_states() -> None:
    group = _group("media-controls")
    assert group["surface"] == "dark-glass"
    assert group["color_mappings"]["COLOR_FOREGROUND"] == "on_surface"
    variants = _variants("media-controls")
    assert set(variants) == {"shuffle", "shuffle-active", "repeat", "repeat-once", "repeat-off"}
    assert "color_mappings" not in variants["shuffle"]
    assert variants["shuffle-active"]["color_mappings"]["COLOR_FOREGROUND"] == "primary"
    assert variants["repeat"]["color_mappings"]["COLOR_FOREGROUND"] == "primary"
    assert variants["repeat-once"]["color_mappings"]["COLOR_FOREGROUND"] == "primary"
    assert "color_mappings" not in variants["repeat-off"]
    for variant in variants.values():
        template = TEMPLATES / variant["template"]
        assert template.is_file(), template
        assert "{{COLOR_FOREGROUND}}" in template.read_text(), template


def test_settings_gear_is_one_template_for_bar_and_panel() -> None:
    settings = _variants("settings")["default"]
    panel = _variants("settings-panel")["settings"]
    assert settings["template"] == "status-bar/settings/default/icon.svg"
    assert panel["template"] == "settings-panel/settings/default/icon.svg"
    for variant in (settings, panel):
        path = TEMPLATES / variant["template"]
        assert path.is_file(), path
        text = path.read_text()
        assert 'viewBox="0 0 1024 1024"' in text
        assert "{{COLOR_FOREGROUND}}" in text
    assert _group("settings")["surface"] == "wallpaper"
    assert _group("settings-panel")["surface"] == "dark-glass"
    assert _variants("settings-panel")["settings"]["color_mappings"]["COLOR_FOREGROUND"] == "on_surface"
