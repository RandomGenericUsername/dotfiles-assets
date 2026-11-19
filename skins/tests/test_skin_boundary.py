"""Skin-boundary gate: skin = role tokens/paint for app-declared surfaces.

WHY THIS FILE EXISTS
--------------------
`REQ-005` / `REQ-018` moved the sound panel into the appearance skin plane.
The panel is an app surface, but the skin target (`ags.gtk.css.j2`) grew
component geometry (min-width/min-height/margin), component type sizes and
weights, structural separators and selectors for toolkit sub-nodes (slider
trough, menu `contents`, switch `slider`, art placeholders). Two owners then
described the same widget tree, and the owner's review found layout and
components in the skin plane.

THE LAW (frozen for this slice)
-------------------------------
A skin template may declare, for an app-declared surface:

* paint/state/type/ink from the v2 role vocabulary (or a palette role);
* the surface's own `padding` role, as exactly one `SKIN_SURFACE_*_PADDING`
  token;
* a simple selector for that surface plus `:hover` / `:focus` /
  `:focus-visible` / `:disabled` / `.selected` / `.active` / `.checked`
  state variants.

It may not declare:

* layout/geometry (`min-width`, `min-height`, `margin`, directional padding,
  flex/grid/order/position, ...);
* component type sizes/weights/letter-spacing or text casing;
* structural borders or dividers (`border-top/bottom/...`);
* descendant/child/sibling selectors (they encode the widget tree);
* a component/content subject (art tile, spinner, divider, scrollbar, slider
  trough, `contents`);
* a semantic signal dot (`live`/`playing`/`mode`/`status`). The app owns the
  dot and its behaviour and uses one semantic green; the skin may supply only
  the colour role, never the node.

Owner decisions recorded (2026-11-13):

1. **Spacing** — the app owns inner component spacing; the skin may declare
   only the surface's single padding token. The strict padding gate stays.
2. **Scope** — enforce `ags` now; the other seven app targets are staged and
   migration-documented, not corpus-wide red today.
6. **Live dot** — app-owned node/behaviour, one semantic green, skin supplies
   only the colour role; the skin's `.audio-mode-dot` ownership is removed.

The bar target (`ags`) is enforced now; the other app targets carry the same
long-standing defect and are measured, not failed, in this slice
(`validate_skins.BOUNDARY_TARGETS` is the migration switch).

Run with `make test-skins`. The corpus test is expected to FAIL until the
templates are split; the unit tests prove each law actually bites.
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "skins" / "templates"

_SPEC = importlib.util.spec_from_file_location(
    "validate_skins_boundary", ROOT / "scripts" / "validate-skins.py"
)
assert _SPEC and _SPEC.loader
validate_skins = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_skins_boundary"] = validate_skins
_SPEC.loader.exec_module(validate_skins)


def _violations(css: str) -> list[tuple[str, int, str]]:
    return validate_skins.skin_boundary_violations(css)


def _categories(css: str) -> list[str]:
    return [category for category, _line, _detail in _violations(css)]


# --------------------------------------------------------------------------- #
# The gate itself: the checked-in corpus must be paint-only for the bar.
# --------------------------------------------------------------------------- #


def test_validate_skins_gate_reports_no_skin_boundary_violation() -> None:
    """`make validate-skins` must be green; every boundary error is named."""
    errors, _notes, _stats = validate_skins.validate(ROOT)
    boundary = [error for error in errors if "skin boundary (" in error]
    summary = Counter(
        error.split("skin boundary (", 1)[1].split(")", 1)[0] for error in boundary
    )
    assert boundary == [], (
        f"{len(boundary)} skin-boundary violation(s) in the enforced target(s) "
        f"{validate_skins.BOUNDARY_TARGETS}: {dict(summary)}\n"
        + "\n".join(boundary)
    )


def test_ags_template_has_no_boundary_violation() -> None:
    """The focused audit view: every offending rule in the bar target."""
    text = (TEMPLATES / "ags.gtk.css.j2").read_text()
    violations = _violations(text)
    assert violations == [], "\n".join(
        f"ags.gtk.css.j2:{line}: {category}: {detail}"
        for category, line, detail in violations
    )


def test_the_enforced_targets_are_registered() -> None:
    """The bar + the wallpaper overlay are the reviewed, enforced surfaces."""
    assert validate_skins.BOUNDARY_TARGETS == ("ags", "ags-wallpaper-selector")
    for target in validate_skins.BOUNDARY_TARGETS:
        assert (TEMPLATES / f"{target}.gtk.css.j2").is_file(), target


#: Owner decision 2026-11-13: the remaining app targets are migration-staged,
#: not failed. The list is frozen here so a future change that silently widens
#: enforcement (or drops a target) fails this test.
STAGED_TARGETS = (
    "ags-btop-studio",
    "ags-capture",
    "ags-clipboard",
    "ags-icme",
    "ags-notifications",
    "wlogout",
)


def test_staged_targets_are_named_and_not_enforced() -> None:
    assert set(STAGED_TARGETS).isdisjoint(validate_skins.BOUNDARY_TARGETS)
    for target in STAGED_TARGETS:
        assert (TEMPLATES / f"{target}.gtk.css.j2").is_file(), target


def test_only_the_enforced_targets_fail_the_gate() -> None:
    """Staged migration: an unenforced target may not contribute errors yet."""
    errors, _notes, _stats = validate_skins.validate(ROOT)
    boundary = [error for error in errors if "skin boundary (" in error]
    offenders = {error.split(":", 1)[0] for error in boundary}
    assert offenders <= {
        f"skins/templates/{target}.gtk.css.j2"
        for target in validate_skins.BOUNDARY_TARGETS
    }, offenders


# --------------------------------------------------------------------------- #
# The laws, proved on minimal snippets (these pass even while the corpus fails).
# --------------------------------------------------------------------------- #


def test_layout_geometry_is_rejected() -> None:
    css = """
    .app-surface {
      min-width: 48px;
      min-height: 26px;
      margin: 4px 0;
      padding-left: 9px;
      position: absolute;
      gap: 4px;
    }
    """
    categories = _categories(css)
    assert categories.count("layout property") == 6, categories


def test_role_padding_must_be_one_surface_token() -> None:
    allowed = ".app-surface { padding: {{SKIN_SURFACE_PANEL_PADDING}}; }"
    assert _categories(allowed) == []

    literal = ".app-surface { padding: 8px 11px 8px 10px; }"
    assert "component padding" in _categories(literal)

    half_token = ".app-surface { padding: {{SKIN_SURFACE_CARD_PADDING}} 11px; }"
    assert "component padding" in _categories(half_token)


def test_component_type_must_use_type_tokens() -> None:
    allowed = (
        ".app-title { font-size: {{SKIN_TYPE_SIZE_TITLE}}; "
        "font-weight: {{SKIN_TYPE_FONT_WEIGHT}}; "
        "letter-spacing: {{SKIN_TYPE_LETTER_SPACING}}; }"
    )
    assert _categories(allowed) == []

    literal = ".app-title { font-size: 28px; font-weight: 650; letter-spacing: -0.02em; }"
    assert _categories(literal).count("component type") == 3


def test_text_casing_is_component_content() -> None:
    assert "component content" in _categories(
        ".app-section-label { text-transform: uppercase; }"
    )


def test_structural_borders_are_app_owned() -> None:
    for prop in ("border-top", "border-right", "border-bottom", "border-left"):
        assert "structural border" in _categories(
            f".app-row {{ {prop}: 1px solid alpha(@on_surface, 0.07); }}"
        ), prop


def test_widget_tree_combinators_are_app_owned() -> None:
    for selector in (
        ".app-menu > contents",
        ".app-scroll viewport",
        ".app-row + .app-row",
        ".app-strip .app-glyph-button.active .app-glyph",
    ):
        assert "structural selector" in _categories(
            f"{selector} {{ color: @on_surface; }}"
        ), selector


def test_component_content_subjects_are_app_owned() -> None:
    for selector in (
        ".app-empty-art",
        ".app-spinner",
        ".app-divider",
        ".app-level-slider",
        ".app-scroll",
        ".app-track-art",
        ".app-app-tile",
    ):
        assert "component/content selector" in _categories(
            f"{selector} {{ color: @on_surface; }}"
        ), selector


def test_semantic_signal_dots_are_app_owned() -> None:
    """Decision 6: the app owns the dot/behaviour and one green; the skin does not."""
    for selector in (".app-live-dot", ".app-playing-dot", ".app-mode-dot", ".app-status-dot"):
        categories = _categories(
            f"{selector} {{ background-color: @primary; }}"
        )
        assert "semantic signal dot" in categories, (selector, categories)


def test_wallpaper_selector_template_has_no_boundary_violation() -> None:
    """The REQ-005 overlay surface is paint-only: layout/components are app-owned."""
    text = (TEMPLATES / "ags-wallpaper-selector.gtk.css.j2").read_text()
    violations = _violations(text)
    assert violations == [], "\n".join(
        f"ags-wallpaper-selector.gtk.css.j2:{line}: {category}: {detail}"
        for category, line, detail in violations
    )


def test_wallpaper_selector_template_paints_the_panel_role() -> None:
    """A layer-shell overlay uses surface.panel, never surface.window."""
    text = (TEMPLATES / "ags-wallpaper-selector.gtk.css.j2").read_text()
    assert "SKIN_SURFACE_PANEL_BG" in text
    assert "SKIN_SURFACE_WINDOW_BG" not in text
    assert ".ws-control-bar" in text
    # No dot node: the app owns the live marker and its behaviour.
    assert "ws-look-live-dot" not in text
    assert "ws-state-dot" not in text


def test_ags_template_owns_no_semantic_signal_dot() -> None:
    """The bar target must not paint a dot; this is RED until the fix lands."""
    text = (TEMPLATES / "ags.gtk.css.j2").read_text()
    dots = [item for item in _violations(text) if item[0] == "semantic signal dot"]
    assert dots == [], "\n".join(
        f"ags.gtk.css.j2:{line}: {category}: {detail}"
        for category, line, detail in dots
    )


def test_focus_ring_state_on_a_control_stays_skin_owned() -> None:
    """`state.focus.ring` is a role the app cannot read; only the ring is skin."""
    css = ".app-level-slider:focus-visible { outline: 2px solid {{SKIN_STATE_FOCUS_RING}}; }"
    assert _violations(css) == []


def test_a_declared_surface_paint_and_state_is_allowed() -> None:
    css = """
    .app-surface {
      background-color: {{SKIN_SURFACE_PANEL_BG}};
      border: {{SKIN_SURFACE_PANEL_BORDER_WIDTH}} solid {{SKIN_SURFACE_PANEL_BORDER}};
      border-radius: {{SKIN_SURFACE_PANEL_RADIUS}};
      padding: {{SKIN_SURFACE_PANEL_PADDING}};
      color: {{SKIN_INK_INK}};
      font-family: {{SKIN_TYPE_FONT_FAMILY}};
    }
    .app-surface:hover { background-color: {{SKIN_STATE_HOVER_FILL}}; }
    .app-surface.selected { background-color: {{SKIN_STATE_SELECTED_FILL}}; }
    """
    assert _violations(css) == []
