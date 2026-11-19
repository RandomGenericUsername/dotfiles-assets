#!/usr/bin/env bash
# Headless verification for the Neovim appearance loader (dotfiles-v3 REQ-124 §6.2).
#
# Proves, without a UI:
#   * the same palette role map yields different chrome for glass/flat/terminal;
#   * resolve() reports token provenance and winborder per skin;
#   * a missing/malformed document returns false instead of raising;
#   * a single bad token only degrades that group;
#   * apply() reads stdpath('config')/lua/dotfiles-appearance.json and sets the
#     chrome highlight groups in Neovim's real highlight table.
#
# Requires `nvim` (>= 0.11 for 'winborder'). Not a member of `make gates`: the
# asset corpus gate set must run on a stock runner with no editor installed.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
assets="$root/configs/nvim"
fixtures="$root/tests/fixtures/nvim-appearance"
tests="$root/tests/nvim-appearance"

command -v nvim >/dev/null 2>&1 || {
  echo "verify: FAIL -- nvim is not installed" >&2
  exit 1
}

run_nvim() {
  nvim --headless --clean -u NONE \
    --cmd "set rtp+=$assets" \
    --cmd "let \$NVIM_APPEARANCE_FIXTURES='$fixtures'" \
    "$@"
}

echo "verify: resolver fixtures (glass/flat/terminal + fallbacks)"
run_nvim -c "luafile $tests/verify.lua" -c "qa!"
echo

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT INT TERM
mkdir -p "$tmp/xdg/nvim/lua" "$tmp/empty/nvim/lua"
cp "$fixtures/glass.tokens.json" "$tmp/xdg/nvim/lua/dotfiles-appearance.json"

# A stand-in for the generated palette module: the same fixed role map the
# fixtures resolve against, so require("dotfiles-palette") survives the reload
# handler dropping package.loaded.
python3 - "$fixtures/palette.roles.json" "$tmp/xdg/nvim/lua/dotfiles-palette.lua" <<'PY'
import json
import sys

roles = json.load(open(sys.argv[1], encoding="utf-8"))
lines = ["return {", "  palette = {"]
for name in sorted(roles):
    lines.append(f'    ["{name}"] = "{roles[name]}",')
lines.extend(["  },", "}", ""])
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
PY

echo "verify: apply through stdpath('config') with an isolated XDG tree"
( export XDG_CONFIG_HOME="$tmp/xdg"; run_nvim --cmd "set rtp+=$tmp/xdg/nvim" \
  -c "luafile $tests/apply.lua" -c "qa!" )
echo

echo "verify: SIGUSR1 and :DotfilesColorsReload re-read the pointer"
( export XDG_CONFIG_HOME="$tmp/xdg"; export NVIM_APPEARANCE_ASSETS="$assets"; run_nvim \
  --cmd "set rtp+=$tmp/xdg/nvim" -c "luafile $tests/reload.lua" -c "qa!" )
echo

echo "verify: absent JSON pointer is a safe no-op"
( export XDG_CONFIG_HOME="$tmp/empty"; run_nvim \
  -c "lua assert(require('dotfiles-appearance').load() == false, 'expected false without a pointer')" \
  -c "qa!" )
echo "MISSING POINTER PASSED"

echo "NVIM APPEARANCE VERIFICATION PASSED"
