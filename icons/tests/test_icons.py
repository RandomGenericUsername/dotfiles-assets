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
    assert 'fill-opacity="0.5"' in (TEMPLATES / variants["shuffle"]["template"]).read_text()
    assert 'fill-opacity' not in (TEMPLATES / variants["shuffle-active"]["template"]).read_text()


def test_settings_gear_is_one_template_for_bar_and_panel() -> None:
    settings = _variants("settings")["default"]
    panel = _variants("settings-panel")["settings"]
    assert settings["template"] == "status-bar/settings/default/icon.svg"
    # schema_major 2 single-sources the byte-identical panel copy: both rows name
    # the one drawing, so bar and panel can never drift apart.
    assert panel["template"] == settings["template"]
    for variant in (settings, panel):
        path = TEMPLATES / variant["template"]
        assert path.is_file(), path
        text = path.read_text()
        assert 'viewBox="0 0 1024 1024"' in text
        assert "{{COLOR_FOREGROUND}}" in text
    assert _group("settings")["surface"] == "wallpaper"
    assert _group("settings-panel")["surface"] == "dark-glass"
    assert "color_mappings" not in panel
    assert _group("settings-panel")["color_mappings"]["COLOR_FOREGROUND"] == "on_surface"


def test_schema_major_2_retires_system_rows_and_collapses_ladders() -> None:
    names = {
        variant["name"]
        for group in MANIFEST.values()
        for variant in group["variants"]
    }
    assert not [name for name in names if name.startswith("system-")]
    assert sum(len(group["variants"]) for group in MANIFEST.values()) == 130
    assert len(list(TEMPLATES.rglob("*.svg"))) == 106

    ladder = [
        "signal-low",
        "signal-medium",
        "signal-good",
        "signal-high",
        "wifi-signal-full",
        "wifi-signal-good",
        "wifi-signal-medium",
        "wifi-signal-low",
        "bluetooth-signal-full",
        "bluetooth-signal-good",
        "bluetooth-signal-medium",
        "bluetooth-signal-low",
    ]
    variants = _variants("settings-panel")
    templates = {
        variants[name]["template"]
        for name in ladder
        if not name.startswith("signal-")
    }
    assert templates == {
        "settings-panel/wifi-signal/default/icon.svg",
        "settings-panel/bluetooth-signal/default/icon.svg",
    }
    assert {variants[name]["template"] for name in ladder if name.startswith("signal-")} == {
        "settings-panel/signal/default/icon.svg"
    }
    for name in ladder:
        if name.endswith(("-low", "-medium", "-good")):
            assert any(
                token.startswith("OPACITY_")
                for token in (variants[name].get("color_mappings") or {})
            ), name

    medium = _variants("volume")["medium"]
    assert medium["template"] == _variants("volume")["max"]["template"]
    assert medium["color_mappings"]["OPACITY_ARC_1"] == "0.5"

    network = _variants("network")
    for state in ("wifi-high", "wifi-medium", "wifi-low"):
        assert (
            network[f"{state}-default"]["template"]
            == "status-bar/network/wifi/default/icon.svg"
        )
        assert (
            network[f"{state}-rounded"]["template"]
            == "status-bar/network/wifi/rounded/icon.svg"
        )
    assert network["ethernet-connected-rounded"]["template"] == (
        network["ethernet-connected-bold"]["template"]
    )
    assert _group("network")["styles"] == ["default", "bold", "rounded"]
