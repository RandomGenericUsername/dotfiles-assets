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

WHY STDLIB ONLY. A fresh clone must pass `make gates` with no virtualenv and no
network. This is the same rule as the other class validators.

Usage: ``python3 scripts/validate-configs.py [--root REPO_ROOT]``
Exit 0 = the class is deployment-fixed and carries the one documented token.
Exit 1 = at least one violation, each naming the file and the reason.
"""

from __future__ import annotations

import argparse
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


def validate(root: Path) -> tuple[str, int]:
    files = _files(root)
    _check_names(files, root)
    token_at = _check_tokens(files, root)
    _check_nonempty(files, root)
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
        f"render token at {token_file}:{token_line}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
