#!/usr/bin/env python3
"""validate-configs -- the `configs` class boundary, asserted against the corpus.

WHAT THIS GATE PROVES (spine AD-11, R-05/R-06):

  1. NO JINJA SOURCE. A `*.j2` or `*.tpl` file under `configs/` is a template whose
     variables the consumer was supposed to render; copying it here makes the tool
     read `{{ … }}` literally.

  2. NO MUTABLE PREFERENCE OR RENDERED OUTPUT. `active-theme`, `.zshrc`, `kitty.conf`,
     `btop.conf`, `settings.toml`, `icons.json` and `style.css` are host state or
     rendered results, never corpus files. `make validate` also rejects the rendered
     names; this gate is the class-local statement of the same rule.

  3. EXACTLY ONE RENDER TOKEN. `hypr/hyprland.lua` carries the single documented
     host-path token (`{{ compositor_configs_xdg_config_home }}`); every other file
     is literal. A second `{{` or any `{%` is an unreviewed template escaping the
     `templates/` class. The failure names the file and line, e.g.
     `configs/hypr/hyprland.lua:7`.

  4. EVERY FILE IS REGULAR AND NON-EMPTY. A zero-byte config deploys a broken tool.

  5. THE WLOGOUT LOGOUT ACTION STAYS GRACEFUL. `wlogout/layout` is a sequence of
     JSON tiles; its single `"label": "logout"` tile must run `uwsm stop`. The
     previous action, `loginctl terminate-user`, ended the user's whole session
     scope; logind's SIGHUP killed the SDDM helper, and SDDM 0.21.0 read that
     exit as an auth error and skipped the greeter restart (a black VT). This
     assertion makes a silent revert a gate failure (BUG-001 / SDDM #1908).

WHY STDLIB ONLY. A fresh clone must pass `make gates` with no virtualenv and no
network. This is the same rule as the other class validators.

Usage: ``python3 scripts/validate-configs.py [--root REPO_ROOT]``
Exit 0 = the class is deployment-fixed, carries the one documented token, and the
wlogout Logout tile uses `uwsm stop`.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONFIGS_DIR = "configs"
DOC_README = "README.md"
TEMPLATE_SUFFIXES = (".j2", ".tpl")
MUTABLE_OR_RENDERED = (
    "active-theme",
    "theme-map.yaml",
    ".zshrc",
    "kitty.conf",
    "btop.conf",
    "settings.toml",
    "icons.json",
    "style.css",
)
RENDER_TOKEN = "{{"
STATEMENT_TOKEN = "{%"
#: The one reviewed token and the file that is allowed to carry it (R-06).
EXPECTED_TOKEN_FILE = Path(CONFIGS_DIR) / "hypr" / "hyprland.lua"
EXPECTED_TOKEN = "{{ compositor_configs_xdg_config_home }}"
#: The logout tile's action. `loginctl terminate-user` tears down the session
#: scope that carries the SDDM helper; this is the action that avoids it (BUG-001).
WLOGOUT_LAYOUT = Path(CONFIGS_DIR) / "wlogout" / "layout"
WLOGOUT_LOGOUT_ACTION = "uwsm stop"


class ConfigError(Exception):
    """A violation, with the file and the reason a reader needs to fix it."""


def _files(root: Path) -> list[Path]:
    configs = root / CONFIGS_DIR
    if not configs.is_dir():
        raise ConfigError(f"{CONFIGS_DIR}/ is missing — the static config corpus lives there")
    return sorted(path for path in configs.rglob("*") if path.is_file())


def _check_names(files: list[Path], root: Path) -> None:
    for path in files:
        rel = path.relative_to(root)
        if path.suffix in TEMPLATE_SUFFIXES:
            raise ConfigError(
                f"{rel}: a {path.suffix} source belongs in templates/, not configs/ "
                "(the consumer would read the braces literally)"
            )
        if path.name in MUTABLE_OR_RENDERED:
            raise ConfigError(
                f"{rel}: {path.name!r} is mutable host state or rendered output, "
                "not deployment-fixed corpus content"
            )


def _check_tokens(files: list[Path], root: Path) -> tuple[str, int]:
    hits: list[tuple[str, int, str]] = []
    for path in files:
        if path.name == DOC_README:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if RENDER_TOKEN in line or STATEMENT_TOKEN in line:
                hits.append((str(path.relative_to(root)), lineno, line.strip()))

    if not hits:
        raise ConfigError(
            f"no {RENDER_TOKEN} token found; {EXPECTED_TOKEN_FILE} must carry "
            f"{EXPECTED_TOKEN!r} (R-06)"
        )
    if len(hits) > 1:
        where = ", ".join(f"{path}:{lineno}" for path, lineno, _ in hits)
        raise ConfigError(
            f"{len(hits)} render tokens under {CONFIGS_DIR}/ ({where}); the class "
            f"allows exactly one: {EXPECTED_TOKEN_FILE}:{hits[0][1]} "
            f"({EXPECTED_TOKEN!r})"
        )

    path, lineno, line = hits[0]
    if Path(path) != EXPECTED_TOKEN_FILE:
        raise ConfigError(
            f"{path}:{lineno}: render token is in the wrong file; the only reviewed "
            f"token lives in {EXPECTED_TOKEN_FILE} (R-06)"
        )
    if EXPECTED_TOKEN not in line:
        raise ConfigError(
            f"{path}:{lineno}: unexpected render token {line!r}; expected "
            f"{EXPECTED_TOKEN!r}"
        )
    return path, lineno


def _check_nonempty(files: list[Path], root: Path) -> None:
    for path in files:
        if path.stat().st_size == 0:
            raise ConfigError(f"{path.relative_to(root)}: empty file — a zero-byte config is broken")


def _wlogout_tiles(text: str) -> list[dict[str, object]]:
    decoder = json.JSONDecoder()
    tiles: list[dict[str, object]] = []
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        try:
            tile, index = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{WLOGOUT_LAYOUT}: not a sequence of JSON objects: {exc}") from exc
        if not isinstance(tile, dict):
            raise ConfigError(
                f"{WLOGOUT_LAYOUT}: every tile must be a JSON object, "
                f"got {type(tile).__name__}"
            )
        tiles.append(tile)
    return tiles


def _check_wlogout_logout(root: Path) -> None:
    path = root / WLOGOUT_LAYOUT
    if not path.is_file():
        raise ConfigError(f"{WLOGOUT_LAYOUT}: the wlogout layout is missing")
    logout = [
        tile
        for tile in _wlogout_tiles(path.read_text(encoding="utf-8"))
        if tile.get("label") == "logout"
    ]
    if len(logout) != 1:
        raise ConfigError(
            f"{WLOGOUT_LAYOUT}: expected exactly one \"label\": \"logout\" tile, "
            f"found {len(logout)}"
        )
    action = logout[0].get("action")
    if action != WLOGOUT_LOGOUT_ACTION:
        raise ConfigError(
            f"{WLOGOUT_LAYOUT}: the Logout tile action is {action!r}; expected "
            f"{WLOGOUT_LOGOUT_ACTION!r}. `loginctl terminate-user` ends the user's "
            "session scope, and SDDM 0.21.0 never restarts the greeter after the "
            "SIGHUP-killed helper (BUG-001 / SDDM #1908)"
        )


def validate(root: Path) -> tuple[str, int]:
    files = _files(root)
    _check_names(files, root)
    token_at = _check_tokens(files, root)
    _check_nonempty(files, root)
    _check_wlogout_logout(root)
    return token_at


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        token_file, token_line = validate(args.root)
    except ConfigError as exc:
        print(f"validate-configs: FAIL -- {exc}", file=sys.stderr)
        return 1
    print(
        "validate-configs: PASS -- no template/mutable/rendered files; exactly one "
        f"render token at {token_file}:{token_line}; wlogout Logout action is "
        f"{WLOGOUT_LOGOUT_ACTION!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
