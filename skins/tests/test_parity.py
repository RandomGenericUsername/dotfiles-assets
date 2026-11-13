"""Parity tests: the glass expansion is today's ags-bar settings/Bluetooth look.

The v2 Appearance token set replaces the v1 flat knobs without changing the
glass declarations that the tokenized set covers. This suite proves the parity
contract from RFC 105 R-11: converting the template to flattened v2
placeholders (`surface.panel.bg`, `state.hover.fill`, ...) must expand to the
same measured declarations as today's `../ags-bar/style.css`.

The expansion reuses ``scripts/validate-skins.py``'s own v2 resolver and
placeholder expander, so the rendered CSS is the same substitution the gate
validates. Expected declarations carry the source line references.
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


def render(name: str = "glass", mode: str = "dark") -> str:
    """Expand a manifest through validate-skins' own v2 expander."""
    tokens = validate_skins._resolve_manifest(load_manifest(name), mode)
    template = validate_skins.expand_template(TEMPLATE.read_text(), tokens)
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


PARITY: dict[str, tuple[str, list[str]]] = {'window.settings-panel': ('style.css:147-151 + policy: font-family only, no font-size',
                           ['background-color: transparent',
                            'color: @on_surface',
                            'font-family: inherit']),
 'window.settings-catcher': ('style.css:147-151 + policy: font-family only, no font-size',
                             ['background-color: transparent',
                              'color: @on_surface',
                              'font-family: inherit']),
 '.settings-catcher-fill': ('style.css:157-159', ['background-color: alpha(@surface, 0.01)']),
 '.settings-surface': ('style.css:161-166 + token extras (shadow/blur none)',
                       ['background-color: alpha(@surface, 0.94)',
                        'border: 1.5px solid @primary',
                        'border-radius: 12px',
                        'padding: 11px',
                        'box-shadow: none',
                        'backdrop-filter: none']),
 '.settings-card': ('style.css:181-186 (hairline-w = 1px)',
                    ['background-color: alpha(@surface_container_high, 0.18)',
                     'border: 1px solid alpha(@on_surface, 0.10)',
                     'border-radius: 9px']),
 '.settings-password': ('style.css:556-561 (same paint as the card, hairline-w = 1px)',
                        ['background-color: alpha(@surface_container_high, 0.18)',
                         'border: 1px solid alpha(@on_surface, 0.10)',
                         'border-radius: 9px']),
 '.settings-card-title': ('style.css:188-191 (title-size = 12.5px)', ['font-size: 12.5px']),
 '.settings-tile': ('style.css:194-199 (asymmetric tile padding preserved)',
                    ['background-color: alpha(@surface_container_high, 0.18)',
                     'border: 1px solid alpha(@on_surface, 0.10)',
                     'border-radius: 9px']),
 '.settings-tile-title': ('style.css:201-204 (text-size = 13px)', ['font-size: 13px']),
 '.settings-tile-sub': ('style.css:206-209 (11px literal)',
                        ['font-size: 11px', 'color: alpha(@on_surface, 0.62)']),
 '.settings-chevron': ('style.css:211-214 (16px literal)',
                       ['font-size: 16px', 'color: alpha(@on_surface, 0.5)']),
 '.settings-mini': ('style.css:260-268',
                    ['padding: 10px',
                     'background-color: alpha(@surface_container_high, 0.18)',
                     'background-image: none',
                     'border: 1px solid alpha(@on_surface, 0.10)',
                     'border-radius: 9px',
                     'color: @on_surface',
                     'box-shadow: none']),
 '.settings-mini:hover': ('style.css:270-272', ['border-color: @primary']),
 '.settings-net': ('style.css:378-387 + cell-pad/radius-cell (row height/spacing are '
                   'TSX-owned)',
                   ['background-color: transparent',
                    'background-image: none',
                    'border: none',
                    'border-radius: 7px',
                    'box-shadow: none',
                    'color: @on_surface']),
 '.settings-net:hover': ('style.css:389-391', ['background-color: alpha(@on_surface, 0.08)']),
 '.settings-net.sel': ('style.css:393-396',
                       ['background-color: @primary_container',
                        'color: @on_primary_container']),
 '.settings-net.out-of-range': ('style.css:400-402', ['opacity: 0.45']),
 '.settings-net-name': ('style.css:407-411 (title-size = 12.5px)', ['font-size: 12.5px']),
 '.settings-net-sub': ('style.css:413-416 (10.5px literal)',
                       ['font-size: 10.5px', 'color: alpha(@on_surface, 0.62)']),
 '.settings-badge': ('style.css:422-429 (hairline-w = 1px)',
                     ['font-size: 9.5px',
                      'letter-spacing: 0.05em',
                      'border-radius: 20px',
                      'background-color: alpha(@on_surface, 0.12)',
                      'border: 1px solid alpha(@on_surface, 0.14)']),
 '.settings-badge.conn': ('style.css:431-435 (hairline-w = 1px)',
                          ['background-color: alpha(@primary, 0.18)',
                           'border: 1px solid alpha(@primary, 0.45)',
                           'color: @on_surface']),
 '.settings-rowact': ('style.css:437-448 (hairline-w = 1px; width/height are TSX-owned)',
                      ['font-size: 11px',
                       'font-weight: 600',
                       'border: 1px solid alpha(@on_surface, 0.26)',
                       'border-radius: 7px',
                       'background-color: transparent',
                       'background-image: none',
                       'box-shadow: none',
                       'color: @on_surface']),
 '.settings-rowact:hover': ('style.css:450-452', ['border-color: @primary']),
 '.settings-rowact.disabled': ('style.css:456-458', ['opacity: 0.5']),
 '.settings-rowact.subtle': ('style.css:461-463', ['opacity: 0.68']),
 '.settings-rowact.subtle:hover': ('style.css:465-468',
                                   ['opacity: 1', 'border-color: alpha(@on_surface, 0.4)']),
 '.settings-rowact.danger': ('style.css:473-476',
                             ['border-color: @tertiary', 'color: @tertiary']),
 '.settings-rowact.danger:hover': ('style.css:478-481',
                                   ['border-color: @secondary', 'color: @secondary']),
 '.settings-net.confirming': ('style.css:488-490', ['background: alpha(@on_surface, 0.06)']),
 '.settings-detail': ('style.css:705-709 (11px literal)',
                      ['font-size: 11px', 'color: alpha(@on_surface, 0.5)']),
 '.settings-empty': ('style.css:637-641 (12px + 18px 10px literals)',
                     ['color: alpha(@on_surface, 0.6)']),
 '.settings-wifi-settings-row:hover': ('style.css:763-765',
                                       ['background-color: alpha(@on_surface, 0.05)']),
 '.settings-wifi-settings-label': ('style.css:783-786 (text-size = 13px)',
                                   ['font-size: 13px', 'color: alpha(@on_surface, 0.7)']),
 '.settings-wifi-settings-note': ('style.css:787-790 (10px literal)',
                                  ['color: alpha(@on_surface, 0.3)']),
 '.settings-wifi-settings-arrow': ('style.css:791-795 (14px literal)',
                                   ['color: alpha(@on_surface, 0.3)']),
 '.settings-back': ('style.css:301-312',
                    ['border-radius: 8px',
                     'background-color: alpha(@on_surface, 0.12)',
                     'background-image: none',
                     'border: none',
                     'box-shadow: none',
                     'color: @on_surface']),
 '.settings-back:hover': ('style.css:313-315', ['background-color: alpha(@on_surface, 0.2)']),
 '.settings-section-label': ('style.css:732-739 (11px literal)',
                             ['font-size: 11px',
                              'font-weight: 600',
                              'color: alpha(@on_surface, 0.4)']),
 '.settings-chevron-row:hover': ('style.css:745-747',
                                 ['background-color: alpha(@on_surface, 0.05)']),
 '.settings-chevron-label': ('style.css:748-751 (text-size = 13px)',
                             ['font-size: 13px', 'color: alpha(@on_surface, 0.7)'])}


def source_style() -> Path | None:
    """Find the read-only ags-bar source next to this repo or its worktree."""
    for base in (ROOT, *ROOT.parents):
        candidate = base / "ags-bar" / "style.css"
        if candidate.is_file():
            return candidate
    return None


def test_glass_expansion_keeps_unit_suffixed_lengths() -> None:
    glass = load_manifest("glass")
    panel = glass["groups"]["surface"]["panel"]
    card = glass["groups"]["surface"]["card"]
    css = render("glass")
    assert panel["radius"] == 12
    assert panel["border-width"] == 1.5
    assert card["border-width"] == 1
    assert "border-radius: 12px;" in css
    assert "border: 1.5px solid @primary;" in css
    assert "border: 1px solid alpha(@on_surface, 0.10);" in css
    # Inner component padding is app-owned (AUDIT-001 decision 1); the skin
    # only expands its one role padding per declared surface.
    assert "padding: 11px;" in css
    assert not __import__("re").search(r"padding: \d+px \d+px;", css)
    assert "border-radius: 20px;" in css
    assert "font-size: 12.5px;" in css
    assert "letter-spacing: 0.05em;" in css
    assert "min-width: 312px;" not in css


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


def test_border_ownership_is_documented_and_split() -> None:
    template = TEMPLATE.read_text()
    assert "FIDELITY POLICY" in template
    assert "BORDER OWNERSHIP" in template
    assert "LAYOUT IS TSX-OWNED" in template
    assert "1.5px" in template and "1px" in template
    assert "gap` is not consumed" in template

    data = json.loads(DEVIATIONS.read_text())
    assert data["deviations"] == []
    assert data["policy"]
    assert any("per-role" in item for item in data["nonvisual"])


def test_per_role_border_widths_match_source() -> None:
    rules = parse_rules(render("glass"))
    # The panel keeps the source's 1.5px frame; every source 1px hairline is 1px.
    assert "border: 1.5px solid @primary" in rules[".settings-surface"]
    for selector in (
        ".settings-card",
        ".settings-password",
        ".settings-tile",
        ".settings-mini",
        ".settings-rowact",
        ".settings-badge",
    ):
        assert any(
            declaration.startswith("border: 1px solid alpha(")
            for declaration in rules[selector]
        ), selector
    assert "border: 1px solid alpha(@primary, 0.45)" in rules[".settings-badge.conn"]
    # Structural separators are app-owned; the skin must not emit them.
    assert ".settings-wifi-settings-row" not in rules
    assert not any(
        declaration.startswith("border: 1.5px solid alpha(")
        for selector, declarations in rules.items()
        if selector != ".settings-surface"
        for declaration in declarations
    ), "only the panel/frame may use the 1.5px border-width"


def test_layout_tokens_are_not_emitted_as_css() -> None:
    template = TEMPLATE.read_text()
    for token in (
        "SKIN_LAYOUT_AGS_PANEL_WIDTH",
        "SKIN_LAYOUT_AGS_BT_LIST_SPACING",
        "SKIN_LAYOUT_AGS_BAR_ROW_HEIGHT",
        "SKIN_LAYOUT_AGS_CHIP_MIN",
    ):
        assert "{{" + token + "}}" not in template, token

    rules = parse_rules(render("glass"))
    assert "min-width: 312px" not in rules[".settings-surface"]
    for selector in (".settings-net", ".settings-rowact"):
        assert not any(
            declaration.startswith(("min-width:", "min-height:"))
            for declaration in rules[selector]
        ), selector
    assert not any(
        declaration.startswith("margin-bottom:") for declaration in rules[".settings-net"]
    )


def test_settings_net_height_matches_source_no_border() -> None:
    rules = parse_rules(render("glass"))
    source = source_style()
    net = rules[".settings-net"]

    assert "border: none" in net
    assert not any(
        declaration.startswith("border:") and "transparent" in declaration
        for declaration in net
    )
    assert not any(declaration.startswith("margin-bottom:") for declaration in net)
    assert not any(declaration.startswith("min-height:") for declaration in net)

    if source is not None:
        block = re.search(
            r"\.settings-net\s*\{(.*?)\}", source.read_text(), re.DOTALL
        )
        assert block is not None
        declarations = {
            line.strip()
            for line in block.group(1).splitlines()
            if line.strip()
        }
        assert "border: none;" in declarations
        assert "min-height: 0;" in declarations
        assert not any(line.startswith("margin") for line in declarations)


def test_gap_is_metadata_not_a_rewritten_padding() -> None:
    css = render("glass")
    assert "padding: 11px;" in css
    # App-owned component spacing never appears as a literal asymmetric value.
    assert "padding: 10px 11px;" not in css
    assert "margin-bottom: 4px;" not in css


def test_window_root_has_no_font_size() -> None:
    rules = parse_rules(render("glass"))
    for selector in ("window.settings-panel", "window.settings-catcher"):
        assert not any(
            declaration.startswith("font-size:") for declaration in rules[selector]
        )
        assert "font-family: inherit" in rules[selector]


def test_paper_dark_and_light_expansions_differ_only_by_mode() -> None:
    dark = render("paper", "dark")
    light = render("paper", "light")
    assert "border: 1px solid alpha(@on_surface, 0.22);" in dark
    assert "border: 1px solid alpha(@on_surface, 0.16);" in light
    assert "box-shadow: 0 10px 28px rgba(0,0,0,0.22);" in dark
    assert "box-shadow: 0 8px 22px alpha(@shadow, 0.16);" in light
