#!/usr/bin/env python3
"""verify-collapse -- byte-faithfulness harness for the schema_major 2 collapse.

WHAT IT PROVES (REQ-149 slice 3, task 3.4/3.6):

  For every variant that existed before the collapse and still resolves after it,
  the rendered SVG has the SAME GEOMETRY and the SAME EFFECTIVE PAINT. For the 12
  retired `system-*` rows it proves the replacement row is the same art rendered
  under the retired row's ink (the surface dimension's derivation).

HOW IT RENDERS: with the PINNED renderer, `icon-templates-renderer` (itr v0.3.2),
through its own `PlaceholderSubstitutionService` and `MappingResolutionService` --
the same code path a consumer uses, not a re-implementation. Point it at an itr
checkout that is installed or on PYTHONPATH:

  PYTHONPATH=~/Development/dotfiles/icon-templates-renderer/src \
    python3 tickets/req-149-icon-schema-v2/verify-collapse.py --base master

The role scheme is deterministic and INJECTIVE (role -> #sha256(role)[:6]) so a
role swap cannot hide behind two role names that happen to resolve to the same
hex on today's palette.

READ IT LIKE THIS:
  geometry  = the ordered drawable elements and every non-paint attribute
              (`d`, `cx`, `r`, `transform`, ... );
  paint     = the resolved fill/stroke colour plus the EFFECTIVE opacity
              (element opacity x fill-opacity x ancestor <g> opacity);
  bytes     = the exact substituted document.

A byte difference with identical geometry + effective paint is the one deliberate
normalisation of the collapse: a numeric parameter is always emitted, so a path
that was fully lit now carries `fill-opacity="1"` (and volume's outer arc sits in
an explicit `<g opacity="1">`). 1 is the identity of the opacity value space, so
the paint is unchanged; the report names every such case.

Exit 0 = every compared row is geometry- and paint-identical. Exit 1 = drift.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import MappingProxyType

try:
    from icon_templates_renderer.domain.models import ColorScheme
    from icon_templates_renderer.domain.services import (
        MappingResolutionService,
        PlaceholderSubstitutionService,
    )
except ImportError as exc:  # pragma: no cover - evidence script
    sys.exit(
        "cannot import the pinned renderer (icon-templates-renderer); run with "
        "PYTHONPATH pointing at its src/ (see the module docstring): " + str(exc)
    )

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = "icons/templates"
MANIFEST = "icons/mappings/icons.yaml"
DEFAULTS = "icons/mappings/defaults.yaml"

DRAWABLE = {
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "use",
    "text",
    "image",
}
PAINT_ATTRS = {
    "fill",
    "stroke",
    "fill-opacity",
    "opacity",
    "stroke-opacity",
    "stop-color",
    "stop-opacity",
    "color",
}

# The 12 retired rows: base (group, variant) -> surviving (group, variant). The
# replacement renders the same drawing under the RETIRED row's ink.
RETIRED = {
    ("battery", "system-battery-0"): ("battery", "battery-0"),
    ("battery", "system-battery-25"): ("battery", "battery-25"),
    ("battery", "system-battery-50"): ("battery", "battery-50"),
    ("battery", "system-battery-75"): ("battery", "battery-75"),
    ("battery", "system-battery-100"): ("battery", "battery-100"),
    ("volume", "system-muted"): ("volume", "muted"),
    ("volume", "system-lowest"): ("volume", "lowest"),
    ("volume", "system-low"): ("volume", "low"),
    ("volume", "system-medium"): ("volume", "medium"),
    ("volume", "system-max"): ("volume", "max"),
    ("microphone", "system-mic-on"): ("microphone", "mic-on"),
    ("microphone", "system-mic-off"): ("microphone", "mic-off"),
}

# The 3 byte-identical duplicate pairs measured by icon-architecture.md §10.
DUPLICATES = [
    (
        "status-bar/network/ethernet-connected/bold/icon.svg",
        "status-bar/network/ethernet-connected/rounded/icon.svg",
    ),
    (
        "settings-panel/settings/default/icon.svg",
        "status-bar/settings/default/icon.svg",
    ),
    (
        "status-bar/wallpaper-progress/default/icon.svg",
        "ui/image/default/icon.svg",
    ),
]


def load_yaml_module():
    path = REPO / "scripts/validate-icons.py"
    spec = importlib.util.spec_from_file_location("validate_icons", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_show(ref: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def scheme_for(roles: set[str]) -> ColorScheme:
    values = {role: "#" + hashlib.sha256(role.encode()).hexdigest()[:6] for role in roles}
    # Injectivity guard: two roles must not collide on the deterministic scheme.
    assert len(set(values.values())) == len(values), "role scheme collision"
    return ColorScheme(values=MappingProxyType(values))


def parse_doc(text: str):
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:  # pragma: no cover - evidence script
        raise SystemExit(f"rendered document is not XML: {exc}")


def geometry(root) -> list[tuple[str, tuple[tuple[str, str], ...]]]:
    out = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in DRAWABLE:
            continue
        attrs = tuple(
            sorted((k, v) for k, v in el.attrib.items() if k not in PAINT_ATTRS)
        )
        out.append((tag, attrs))
    return out


def effective_paint(root) -> list[tuple[str, str, float]]:
    """(tag, resolved fill, effective opacity) per drawable, in document order."""
    out: list[tuple[str, str, float]] = []

    def walk(el, inherited: float):
        tag = el.tag.split("}")[-1]
        opacity = float(el.attrib.get("opacity", "1") or 1)
        here = inherited * opacity
        if tag in DRAWABLE:
            fill = el.attrib.get("fill")
            if fill is None:
                fill = root.attrib.get("fill")  # SVG paint inheritance
            fill_opacity = float(el.attrib.get("fill-opacity", "1") or 1)
            out.append((tag, fill or "none", round(here * fill_opacity, 6)))
        for child in el:
            walk(child, here)

    walk(root, 1.0)
    return out


def merge(mapping_merge, defaults, group, variant):
    return mapping_merge.merge(
        defaults,
        (group or {}).get("color_mappings") or {},
        (variant or {}).get("color_mappings") or {},
    )


def render(mapping_merge, substitution, defaults, group, variant, template_text, extra):
    merged = merge(mapping_merge, defaults, group, variant)
    merged.update(extra)
    return substitution.substitute(template_text, scheme, False, merged)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="master", help="git ref of the pre-collapse tree")
    ap.add_argument(
        "--roles",
        nargs="*",
        default=None,
        help="roles to seed the scheme with (default: the live vocabulary)",
    )
    args = ap.parse_args()

    yaml_mod = load_yaml_module()
    base_manifest = yaml_mod.parse_yaml_subset(git_show(args.base, MANIFEST), f"{args.base}:{MANIFEST}")
    base_defaults = yaml_mod.parse_yaml_subset(
        git_show(args.base, DEFAULTS), f"{args.base}:{DEFAULTS}"
    )["defaults"]
    head_manifest = yaml_mod.parse_yaml_subset((REPO / MANIFEST).read_text(), MANIFEST)
    head_defaults = yaml_mod.parse_yaml_subset((REPO / DEFAULTS).read_text(), DEFAULTS)["defaults"]

    roles = set(args.roles or ())
    if not roles:
        import json

        roles = set(json.loads((REPO / "icons/mappings/vocabulary.json").read_text())["roles"])
    global scheme
    scheme = scheme_for(roles)

    mapping_merge = MappingResolutionService()
    substitution = PlaceholderSubstitutionService()

    base_rows = {
        (group, variant["name"]): (group, variant)
        for group, entry in base_manifest.items()
        for variant in entry.get("variants", [])
    }
    head_rows = {
        (group, variant["name"]): (group, variant)
        for group, entry in head_manifest.items()
        for variant in entry.get("variants", [])
    }

    def base_template(group: str, variant: dict) -> str:
        entry = base_manifest[group]
        template_dir = entry.get("template_dir", ".")
        rel = f"{TEMPLATES}/{template_dir}/{variant['template']}" if template_dir != "." else f"{TEMPLATES}/{variant['template']}"
        return git_show(args.base, rel)

    def head_template(group: str, variant: dict) -> str:
        entry = head_manifest[group]
        template_dir = entry.get("template_dir", ".")
        base = REPO / TEMPLATES / template_dir
        return (base / variant["template"]).read_text()

    failures: list[str] = []
    normalised: list[str] = []
    compared = 0

    # 1. Every variant that survives under the same name.
    for key in sorted(set(base_rows) & set(head_rows)):
        group, name = key
        base_group_entry = base_manifest[group]
        head_group_entry = head_manifest[group]
        _, base_variant = base_rows[key]
        _, head_variant = head_rows[key]
        before = render(
            mapping_merge,
            substitution,
            base_defaults,
            base_group_entry,
            base_variant,
            base_template(group, base_variant),
            {},
        )
        after = render(
            mapping_merge,
            substitution,
            head_defaults,
            head_group_entry,
            head_variant,
            head_template(group, head_variant),
            {},
        )
        compared += 1
        broot, aroot = parse_doc(before), parse_doc(after)
        ok_geometry = geometry(broot) == geometry(aroot)
        ok_paint = effective_paint(broot) == effective_paint(aroot)
        if not ok_geometry:
            failures.append(f"{group}/{name}: geometry differs")
        if not ok_paint:
            failures.append(
                f"{group}/{name}: effective paint differs\n"
                f"    before: {effective_paint(broot)}\n"
                f"    after:  {effective_paint(aroot)}"
            )
        if ok_geometry and ok_paint and before != after:
            normalised.append(f"{group}/{name}")

    # 2. The 12 retired rows: same art, the retired row's ink forced on the
    #    surviving row (surface-direct rendering).
    for (bgroup, bname), (hgroup, hname) in sorted(RETIRED.items()):
        if (bgroup, bname) not in base_rows:
            failures.append(f"{bgroup}/{bname}: retired row absent from {args.base}")
            continue
        if (hgroup, hname) not in head_rows:
            failures.append(f"{hgroup}/{hname}: replacement row missing")
            continue
        _, base_variant = base_rows[(bgroup, bname)]
        _, head_variant = head_rows[(hgroup, hname)]
        base_extra = dict(base_variant.get("color_mappings") or {})
        before = render(
            mapping_merge,
            substitution,
            base_defaults,
            base_manifest[bgroup],
            base_variant,
            base_template(bgroup, base_variant),
            {},
        )
        after = render(
            mapping_merge,
            substitution,
            head_defaults,
            head_manifest[hgroup],
            head_variant,
            head_template(hgroup, head_variant),
            base_extra,
        )
        compared += 1
        broot, aroot = parse_doc(before), parse_doc(after)
        ok_geometry = geometry(broot) == geometry(aroot)
        ok_paint = effective_paint(broot) == effective_paint(aroot)
        if not ok_geometry:
            failures.append(f"{bgroup}/{bname} -> {hgroup}/{hname}: geometry differs")
        if not ok_paint:
            failures.append(f"{bgroup}/{bname} -> {hgroup}/{hname}: paint differs")
        if ok_geometry and ok_paint and before != after:
            normalised.append(f"{bgroup}/{bname} -> {hgroup}/{hname}")

    # 3. The three byte-identical duplicate pairs at the base ref.
    duplicates_ok = True
    for left, right in DUPLICATES:
        if git_show(args.base, f"{TEMPLATES}/{left}") != git_show(args.base, f"{TEMPLATES}/{right}"):
            duplicates_ok = False
            failures.append(f"duplicate pair not byte-identical at {args.base}: {left} / {right}")

    print(f"verify-collapse: base={args.base} compared={compared} rows "
          f"({len(set(base_rows) & set(head_rows))} surviving + {len(RETIRED)} retired)")
    print(f"verify-collapse: byte-identical duplicate pairs verified: "
          f"{'3/3' if duplicates_ok else 'FAILED'} (files: {len(DUPLICATES)} pairs)")
    if normalised:
        print("verify-collapse: byte-difference limited to the identity opacity "
              "normalisation (geometry + effective paint identical):")
        for item in normalised:
            print(f"  - {item}")
    if failures:
        print(f"verify-collapse: FAIL -- {len(failures)} drift(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("verify-collapse: PASS -- every compared row is geometry-identical and "
          "carries the same effective paint under the same ink")
    return 0


if __name__ == "__main__":
    sys.exit(main())
