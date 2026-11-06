"""Parity tests: the glass expansion is today's ags-bar settings/Bluetooth look.

The frozen v1 token set is not changed here. This suite proves the correction
that `v0.7.0` missed: the GTK template is a *literal extraction* of
``../ags-bar/style.css`` for the settings and Bluetooth surfaces, with
``{{SKIN_*}}`` used only where the token is a genuine global knob.

The expansion reuses ``scripts/validate-skins.py``'s own placeholder map, so the
rendered CSS is the same substitution the gate validates. Expected declarations
carry the source line references; the only visual deviations are the documented
1px → 1.5px hairlines encoded in
``fixtures/parity/deviations.json`` (the single frozen ``border-w`` token cannot
split the 1.5px panel from the 1px controls).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "skins" / "schema.json"
MANIFESTS = ROOT / "skins" / "manifests"
TEMPLATE = ROOT / "skins" / "templates" / "ags.gtk.css.j2"
DEVIATIONS = Path(__file__).parent / "fixtures" / "parity" / "deviations.json"
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")

_SPEC = importlib.util.spec_from_file_location(
    "validate_skins", ROOT / "scripts" / "validate-skins.py"
)
assert _SPEC and _SPEC.loader
validate_skins = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_skins"] = validate_skins
_SPEC.loader.exec_module(validate_skins)


def schema() -> dict:
    return json.loads(SCHEMA.read_text())


def load_manifest(name: str) -> dict:
    with (MANIFESTS / f"{name}.toml").open("rb") as handle:
        return tomllib.load(handle)


def render(name: str) -> str:
    """Expand a manifest through validate-skins' own unit-rule expander."""
    manifest = load_manifest(name)
    template = validate_skins.expand_template(
        TEMPLATE.read_text(), manifest, schema()["frozen"]["token_groups"]
    )
    assert "{{" not in template, "unexpanded placeholder in template"
    return template


def parse_rules(css: str) -> dict[str, list[str]]:
    """Return selector → declarations for the flat CSS this template emits."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    rules: dict[str, list[str]] = {}
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        declarations = [
            declaration.strip()
            for declaration in match.group(2).split(";")
            if declaration.strip()
        ]
        for selector in match.group(1).split(","):
            rules.setdefault(selector.strip(), []).extend(declarations)
    return rules


# selector → (source lines, expected declarations in the glass expansion)
PARITY: dict[str, tuple[str, list[str]]] = {
    "window.settings-panel": (
        "style.css:147-151 + policy: font-family only, no font-size",
        [
            "background-color: transparent",
            "color: @on_surface",
            "font-family: inherit",
        ],
    ),
    "window.settings-catcher": (
        "style.css:147-151 + policy: font-family only, no font-size",
        [
            "background-color: transparent",
            "color: @on_surface",
            "font-family: inherit",
        ],
    ),
    ".settings-catcher-fill": (
        "style.css:157-159",
        ["background-color: alpha(@surface, 0.01)"],
    ),
    ".settings-surface": (
        "style.css:161-166 + token extras (panel width, shadow/blur none)",
        [
            "min-width: 312px",
            "background-color: alpha(@surface, 0.94)",
            "border: 1.5px solid @primary",
            "border-radius: 12px",
            "padding: 11px",
            "box-shadow: none",
            "backdrop-filter: none",
        ],
    ),
    ".settings-scroll": (
        "style.css:168-172",
        ["background-color: transparent", "border: none"],
    ),
    ".settings-scroll viewport": (
        "style.css:168-172",
        ["background-color: transparent", "border: none"],
    ),
    ".settings-scroll scrollbar slider": (
        "style.css:174-178",
        [
            "min-width: 5px",
            "border-radius: 5px",
            "background-color: alpha(@on_surface, 0.25)",
        ],
    ),
    ".settings-card": (
        "style.css:181-186 (border width deviation: 1px → 1.5px)",
        [
            "background-color: alpha(@surface_container_high, 0.18)",
            "border: 1.5px solid alpha(@on_surface, 0.10)",
            "border-radius: 9px",
            "padding: 10px 11px",
        ],
    ),
    ".settings-password": (
        "style.css:556-561 (same paint as the card)",
        [
            "background-color: alpha(@surface_container_high, 0.18)",
            "border: 1.5px solid alpha(@on_surface, 0.10)",
            "border-radius: 9px",
            "padding: 10px 11px",
        ],
    ),
    ".settings-card-title": (
        "style.css:188-191 (title-size = 12.5px)",
        ["font-size: 12.5px", "font-weight: 650"],
    ),
    ".settings-tile": (
        "style.css:194-199 (asymmetric tile padding preserved)",
        [
            "background-color: alpha(@surface_container_high, 0.18)",
            "border: 1.5px solid alpha(@on_surface, 0.10)",
            "border-radius: 9px",
            "padding: 8px 11px 8px 10px",
        ],
    ),
    ".settings-tile-title": (
        "style.css:201-204 (text-size = 13px)",
        ["font-size: 13px", "font-weight: 600"],
    ),
    ".settings-tile-sub": (
        "style.css:206-209 (11px literal)",
        ["font-size: 11px", "color: alpha(@on_surface, 0.62)"],
    ),
    ".settings-chevron": (
        "style.css:211-214 (16px literal)",
        ["font-size: 16px", "color: alpha(@on_surface, 0.5)"],
    ),
    ".settings-mini": (
        "style.css:260-268",
        [
            "min-height: 0",
            "padding: 10px",
            "background-color: alpha(@surface_container_high, 0.18)",
            "background-image: none",
            "border: 1.5px solid alpha(@on_surface, 0.10)",
            "border-radius: 9px",
            "color: @on_surface",
            "box-shadow: none",
        ],
    ),
    ".settings-mini:hover": ("style.css:270-272", ["border-color: @primary"]),
    ".settings-mini-title": (
        "style.css:281-284 (12px literal)",
        ["font-size: 12px", "font-weight: 600"],
    ),
    ".settings-net": (
        "style.css:378-387 + cell-pad/radius-cell + bt-list-spacing margin",
        [
            "min-height: 0px",
            "padding: 8px 9px",
            "margin-bottom: 4px",
            "background-color: transparent",
            "background-image: none",
            "border: none",
            "border-radius: 7px",
            "box-shadow: none",
            "color: @on_surface",
        ],
    ),
    ".settings-net:hover": (
        "style.css:389-391",
        ["background-color: alpha(@on_surface, 0.08)"],
    ),
    ".settings-net.sel": (
        "style.css:393-396",
        ["background-color: @primary_container", "color: @on_primary_container"],
    ),
    ".settings-net.out-of-range": ("style.css:400-402", ["opacity: 0.45"]),
    ".settings-net-name": (
        "style.css:407-411 (title-size = 12.5px)",
        ["font-size: 12.5px", "font-weight: 600", "min-width: 48px"],
    ),
    ".settings-net-sub": (
        "style.css:413-416 (10.5px literal)",
        ["font-size: 10.5px", "color: alpha(@on_surface, 0.62)"],
    ),
    ".settings-net.sel .settings-net-sub": (
        "style.css:418-420",
        ["color: alpha(@on_primary_container, 0.85)"],
    ),
    ".settings-badge": (
        "style.css:422-429 (border width deviation: 1px → 1.5px)",
        [
            "font-size: 9.5px",
            "letter-spacing: 0.05em",
            "padding: 2px 6px",
            "border-radius: 20px",
            "background-color: alpha(@on_surface, 0.12)",
            "border: 1.5px solid alpha(@on_surface, 0.14)",
        ],
    ),
    ".settings-badge.conn": (
        "style.css:431-435 (border width deviation: 1px → 1.5px)",
        [
            "background-color: alpha(@primary, 0.18)",
            "border: 1.5px solid alpha(@primary, 0.45)",
            "color: @on_surface",
        ],
    ),
    ".settings-rowact": (
        "style.css:437-448 (border width deviation: 1px → 1.5px)",
        [
            "min-width: 0px",
            "min-height: 0px",
            "padding: 4px 8px",
            "font-size: 11px",
            "font-weight: 600",
            "border: 1.5px solid alpha(@on_surface, 0.26)",
            "border-radius: 7px",
            "background-color: transparent",
            "background-image: none",
            "box-shadow: none",
            "color: @on_surface",
        ],
    ),
    ".settings-rowact:hover": ("style.css:450-452", ["border-color: @primary"]),
    ".settings-rowact.disabled": ("style.css:456-458", ["opacity: 0.5"]),
    ".settings-rowact.subtle": ("style.css:461-463", ["opacity: 0.68"]),
    ".settings-rowact.subtle:hover": (
        "style.css:465-468",
        ["opacity: 1", "border-color: alpha(@on_surface, 0.4)"],
    ),
    ".settings-rowact.danger": (
        "style.css:473-476",
        ["border-color: @tertiary", "color: @tertiary"],
    ),
    ".settings-rowact.danger:hover": (
        "style.css:478-481",
        ["border-color: @secondary", "color: @secondary"],
    ),
    ".settings-net.confirming": (
        "style.css:488-490",
        ["background: alpha(@on_surface, 0.06)"],
    ),
    ".settings-spinner": (
        "style.css:493-497 (14px literal)",
        ["min-width: 14px", "min-height: 14px", "color: @primary"],
    ),
    ".settings-divider": (
        "style.css:694-698",
        [
            "min-height: 1px",
            "background-color: alpha(@on_surface, 0.06)",
            "margin: 4px 0",
        ],
    ),
    ".settings-conn-details": ("style.css:699-700", ["padding: 6px 16px"]),
    ".settings-detail-row": ("style.css:702-703", ["min-height: 18px"]),
    ".settings-detail": (
        "style.css:705-709 (11px literal)",
        ["font-size: 11px", "color: alpha(@on_surface, 0.5)"],
    ),
    ".settings-empty": (
        "style.css:637-641 (12px + 18px 10px literals)",
        [
            "padding: 18px 10px",
            "font-size: 12px",
            "color: alpha(@on_surface, 0.6)",
        ],
    ),
    ".settings-other-networks": ("style.css:754-756", ["padding: 4px 0"]),
    ".settings-level-slider trough": (
        "style.css:350-357 (99px literal)",
        [
            "min-height: 10px",
            "min-width: 10px",
            "border-radius: 99px",
            "background-color: alpha(@on_surface, 0.16)",
            "border: none",
        ],
    ),
    ".settings-level-slider trough highlight": (
        "style.css:358-361 (99px literal)",
        ["border-radius: 99px", "background-color: @primary"],
    ),
    ".settings-level-slider trough slider": (
        "style.css:363-371",
        [
            "min-width: 15px",
            "min-height: 15px",
            "margin: -3px 0",
            "border: none",
            "border-radius: 50%",
            "background-color: @on_surface",
            "box-shadow: none",
        ],
    ),
    ".settings-wifi-settings-row": (
        "style.css:759-762 (border width deviation: 1px → 1.5px)",
        [
            "padding: 10px 16px",
            "border-top: 1.5px solid alpha(@on_surface, 0.06)",
        ],
    ),
    ".settings-wifi-settings-row:hover": (
        "style.css:763-765",
        ["background-color: alpha(@on_surface, 0.05)"],
    ),
    ".settings-wifi-settings-label": (
        "style.css:783-786 (text-size = 13px)",
        ["font-size: 13px", "color: alpha(@on_surface, 0.7)"],
    ),
    ".settings-wifi-settings-note": (
        "style.css:787-790 (10px literal)",
        ["font-size: 10px", "color: alpha(@on_surface, 0.3)"],
    ),
    ".settings-wifi-settings-arrow": (
        "style.css:791-795 (14px literal)",
        ["font-size: 14px", "color: alpha(@on_surface, 0.3)"],
    ),
    ".settings-nav-header": (
        "style.css:287-300",
        ["min-height: 26px", "padding-bottom: 7px"],
    ),
    ".settings-back": (
        "style.css:301-312",
        [
            "min-width: 26px",
            "min-height: 26px",
            "padding: 0",
            "border-radius: 8px",
            "background-color: alpha(@on_surface, 0.12)",
            "background-image: none",
            "border: none",
            "box-shadow: none",
            "color: @on_surface",
        ],
    ),
    ".settings-back:hover": (
        "style.css:313-315",
        ["background-color: alpha(@on_surface, 0.2)"],
    ),
    ".settings-back-glyph": ("style.css:317-319", ["font-size: 18px"]),
    ".settings-nav-title": (
        "style.css:321-325 (13.5px literal)",
        ["font-size: 13.5px", "font-weight: 650"],
    ),
    ".settings-net-signal": (
        "style.css:711-715 (30px literal)",
        ["min-width: 30px", "min-height: 30px"],
    ),
    ".settings-section-label": (
        "style.css:732-739 (11px literal)",
        [
            "font-size: 11px",
            "font-weight: 600",
            "text-transform: uppercase",
            "letter-spacing: 0.05em",
            "color: alpha(@on_surface, 0.4)",
            "padding: 4px 16px",
        ],
    ),
    ".settings-chevron-row": ("style.css:742-744", ["padding: 8px 16px"]),
    ".settings-chevron-row:hover": (
        "style.css:745-747",
        ["background-color: alpha(@on_surface, 0.05)"],
    ),
    ".settings-chevron-label": (
        "style.css:748-751 (text-size = 13px)",
        ["font-size: 13px", "color: alpha(@on_surface, 0.7)"],
    ),
}


def source_style() -> Path | None:
    """Find the read-only ags-bar source next to this repo or its worktree."""
    for base in (ROOT, *ROOT.parents):
        candidate = base / "ags-bar" / "style.css"
        if candidate.is_file():
            return candidate
    return None


def test_glass_expansion_keeps_unit_suffixed_lengths() -> None:
    glass = load_manifest("glass")
    css = render("glass")
    assert glass["shape"]["radius-panel"] == 12
    assert glass["shape"]["border-w"] == 1.5
    assert glass["rhythm"]["cell-pad"] == "8px 9px"
    assert "border-radius: 12px;" in css
    assert "border: 1.5px solid @primary;" in css
    assert "padding: 8px 9px;" in css
    assert "border-radius: 20px;" in css
    assert "font-size: 12.5px;" in css
    assert "min-width: 312px;" in css


def test_glass_matches_today_source_declarations() -> None:
    rules = parse_rules(render("glass"))
    missing = sorted(set(PARITY) - set(rules))
    assert missing == [], f"selectors missing from the expansion: {missing}"
    wrong = {
        selector: (rules[selector], declarations)
        for selector, (_source, declarations) in PARITY.items()
        if rules[selector] != declarations
    }
    assert wrong == {}, f"glass declarations differ from today: {wrong}"


def test_no_shadow_transition_animation_or_hex() -> None:
    css = render("glass")
    assert not HEX.search(css), "literal hex colour in the expansion"
    assert not re.search(r"\btransition\s*:", css), "transition in the expansion"
    assert not re.search(r"\banimation\s*:", css), "animation in the expansion"
    assert "rgba(" not in css, "glass must not ship a literal rgba shadow"
    for selector, declarations in parse_rules(css).items():
        for declaration in declarations:
            if declaration.startswith("box-shadow:"):
                assert declaration == "box-shadow: none", (
                    f"{selector} ships a shadow: {declaration}"
                )
            if declaration.startswith("backdrop-filter:"):
                assert declaration == "backdrop-filter: none", (
                    f"{selector} ships a blur: {declaration}"
                )


def test_documented_deviations_are_explicit() -> None:
    template = TEMPLATE.read_text()
    assert "FIDELITY POLICY" in template
    assert "DOCUMENTED DEVIATIONS" in template
    assert "1.5px" in template and "1px" in template
    assert "gap` is not consumed" in template

    data = json.loads(DEVIATIONS.read_text())
    assert data["deviations"], "the deviation fixture must not be empty"
    rules = parse_rules(render("glass"))
    source = source_style()
    for deviation in data["deviations"]:
        assert deviation["template"] in rules[deviation["selector"]], deviation
        assert "1.5px" in deviation["template"]
        assert "1px" in deviation["source"]
        if source is not None:
            ref = deviation["source_ref"]
            path, lineno = ref.rsplit(":", 1)
            assert path.endswith("ags-bar/style.css")
            line = source.read_text().splitlines()[int(lineno) - 1].strip()
            assert line == deviation["source"], (
                f"{ref}: expected {deviation['source']!r}, got {line!r}"
            )


def test_card_border_deviation_is_the_only_visual_border_delta() -> None:
    data = json.loads(DEVIATIONS.read_text())
    by_selector = {item["selector"]: item for item in data["deviations"]}
    card = by_selector[".settings-card"]
    assert card["template"] == "border: 1.5px solid alpha(@on_surface, 0.10)"
    assert card["source"] == "border: 1px solid alpha(@on_surface, 0.10);"
    assert card["source_ref"].endswith("style.css:183")
    assert "border-w" in card["reason"]
    assert all(item["delta"] == "+0.5px (1.5px vs 1px)" for item in data["deviations"])

    rules = parse_rules(render("glass"))
    # The panel keeps the source's 1.5px; every source 1px hairline is 1.5px here.
    assert "border: 1.5px solid @primary" in rules[".settings-surface"]
    for selector in (".settings-card", ".settings-rowact", ".settings-badge"):
        assert any(
            declaration.startswith("border: 1.5px solid alpha(")
            for declaration in rules[selector]
        )


def test_gap_is_metadata_not_a_rewritten_padding() -> None:
    css = render("glass")
    # glass gap is 8px, but the template keeps the source's 11px panel padding,
    # 10px 11px card padding and 4px list spacing instead of substituting gap.
    assert "padding: 11px;" in css
    assert "padding: 10px 11px;" in css
    assert "margin-bottom: 4px;" in css
    assert "padding: 8px;" not in css


def test_window_root_has_no_font_size() -> None:
    rules = parse_rules(render("glass"))
    for selector in ("window.settings-panel", "window.settings-catcher"):
        assert not any(
            declaration.startswith("font-size:") for declaration in rules[selector]
        )
        assert "font-family: inherit" in rules[selector]
