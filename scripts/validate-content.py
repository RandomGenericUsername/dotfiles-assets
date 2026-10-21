#!/usr/bin/env python3
"""validate-content -- the content class: the tarball is the contract, themes are real.

WHAT THIS GATE PROVES:

  1. THE WALLPAPERS TARBALL CONTAINS A TOP-LEVEL `default.png`. The installer
     already asserts this at deploy time (`roles/assets/tasks/main.yml`), but by
     then the tag is already published and a machine is already mid-provision.
     The assets repository asserts it at RELEASE time, so a bad tarball cannot be
     tagged. "Top-level" is exact: the member name must be `default.png`, not
     `wallpapers/default.png` -- the deploy unpacks the archive's contents into
     the spine's `wallpapers/` directory.

  2. EVERY `*.theme` IS NON-EMPTY. An authored btop theme of zero bytes renders
     as an empty theme, which reads as "no theme" on a provisioned machine. The
     class holds authored themes only (the active-theme preference is a mutable
     host fact and never an asset, spine AD-11).

  3. THE TARBALL IS UNPACKED BYTE-FOR-BYTE, NOT REPACKED. The check reads the
     archive's member list with the standard library; it never writes a copy.
     The bytes are the contract (the runtime derives a hash from them), so a
     re-pack would change the hash for no user-visible gain.

WHAT IT REPORTS WITHOUT FAILING: how many authored themes exist (zero today is a
deliberate state, not a gap -- the `.gitkeep` says so). A vacuous pass is printed
as vacuous; a silent skip and a pass must not be indistinguishable in a green log.

Usage: ``python3 scripts/validate-content.py [--root REPO_ROOT]``
Exit 0 = the content corpus is shippable. Exit 1 = at least one violation, by path.
"""

from __future__ import annotations

import argparse
import sys
import tarfile
from pathlib import Path

WALLPAPERS = "content/wallpapers/wallpapers.tar.gz"
THEMES_DIR = "content/btop-themes"
DEFAULT_IMAGE = "default.png"


def check_wallpapers(root: Path, errors: list[str]) -> tuple[int, bool]:
    """Check the tarball's top-level default.png; return (member count, has default)."""
    path = root / WALLPAPERS
    if not path.is_file():
        errors.append(f"{WALLPAPERS}: missing -- the wallpaper corpus is a required member")
        return 0, False
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getnames()
    except (tarfile.TarError, OSError) as exc:
        errors.append(f"{WALLPAPERS}: not a readable gzip tarball ({exc})")
        return 0, False
    has_default = DEFAULT_IMAGE in members
    if not has_default:
        errors.append(
            f"{WALLPAPERS}: no top-level {DEFAULT_IMAGE!r} member -- the deploy unpacks "
            f"the archive's CONTENTS into the spine, so the image must be at the root"
        )
    unsafe = [name for name in members if name.startswith("/") or ".." in Path(name).parts]
    if unsafe:
        errors.append(
            f"{WALLPAPERS}: member path(s) escape the archive root: "
            + ", ".join(unsafe[:5])
        )
    return len(members), has_default


def check_themes(root: Path, errors: list[str]) -> tuple[int, int]:
    """Check every authored theme is non-empty; return (count, bytes)."""
    directory = root / THEMES_DIR
    if not directory.is_dir():
        errors.append(f"{THEMES_DIR}/: missing -- the authored-theme class dir is required")
        return 0, 0
    themes = sorted(directory.rglob("*.theme"))
    total = 0
    for theme in themes:
        rel = theme.relative_to(root).as_posix()
        size = theme.stat().st_size
        total += size
        if size == 0:
            errors.append(f"{rel}: empty theme -- it would render as 'no theme' on a host")
    return len(themes), total


def main() -> int:
    parser = argparse.ArgumentParser(description="validate the content corpus")
    parser.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = parser.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent

    errors: list[str] = []
    members, has_default = check_wallpapers(root, errors)
    theme_count, theme_bytes = check_themes(root, errors)

    print(
        f"validate-content: root={root} wallpapers={WALLPAPERS} "
        f"tar_members={members} top_level_{DEFAULT_IMAGE}={has_default}"
    )
    print(
        f"validate-content: authored themes: {theme_count} "
        f"({theme_bytes} bytes)"
        + (" -- vacuous until the themes land" if theme_count == 0 else "")
    )
    if errors:
        print(f"validate-content: FAIL -- {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        f"validate-content: PASS -- {WALLPAPERS} holds a top-level {DEFAULT_IMAGE} and "
        f"every *.theme is non-empty"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
