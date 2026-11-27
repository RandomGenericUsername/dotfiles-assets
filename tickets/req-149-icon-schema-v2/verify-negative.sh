#!/usr/bin/env bash
# verify-negative.sh — prove the schema_major 2 gate bites.
#
# Each case copies the live `icons/` class into a throwaway tree, makes ONE
# contract-breaking edit, and runs the real validator against it. The case passes
# only when the validator exits non-zero AND names the expected rule. Nothing in
# the repository is modified.
#
#   bash tickets/req-149-icon-schema-v2/verify-negative.sh
set -eu

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VALIDATOR="$REPO/scripts/validate-icons.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM

fail=0
case_no=0

run_case() {
  local title="$1" expect="$2" mutate="$3"
  case_no=$((case_no + 1))
  local root="$TMP/case$case_no"
  mkdir -p "$root"
  cp -a "$REPO/icons" "$root/icons"
  ( cd "$root" && eval "$mutate" )
  local out rc=0
  out="$(python3 "$VALIDATOR" --root "$root" 2>&1)" || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "FAIL case $case_no ($title): validator exited 0"
    fail=1
    return
  fi
  if ! printf '%s\n' "$out" | grep -q "$expect"; then
    echo "FAIL case $case_no ($title): exit $rc but the output does not name: $expect"
    printf '%s\n' "$out" | sed 's/^/    /' | head -6
    fail=1
    return
  fi
  echo "PASS case $case_no ($title): exit $rc, $(printf '%s\n' "$out" | grep -m1 "$expect" | sed 's/^ *- //' | cut -c1-150)"
}

run_case "opacity above 1" "must be a numeric literal in \[0, 1\]" \
  "sed -i 's/OPACITY_ARC_1: \"0.5\"/OPACITY_ARC_1: \"1.5\"/' icons/mappings/icons.yaml"

run_case "a number as a colour role" "a colour is not a number" \
  "sed -i '0,/COLOR_CROSS: error/s//COLOR_CROSS: \"0.5\"/' icons/mappings/icons.yaml"

run_case "a role as an opacity" "an opacity is not a role" \
  "sed -i 's/OPACITY_ARC_1: \"0.5\"/OPACITY_ARC_1: primary/' icons/mappings/icons.yaml"

run_case "wallpaper ink is not on_backdrop" "a wallpaper glyph's ink must be" \
  "sed -i '0,/COLOR_FOREGROUND: on_backdrop/s//COLOR_FOREGROUND: on_surface/' icons/mappings/icons.yaml"

run_case "unknown token family in art" "malformed placeholder" \
  "sed -i 's/{{OPACITY_BAR_1}}/{{VISIBILITY_BAR_1}}/' icons/templates/settings-panel/signal/default/icon.svg"

run_case "schema and checker disagree" "this validator implements 2" \
  "sed -i 's/\"schema_major\": 2/\"schema_major\": 1/' icons/schema.json"

run_case "styled row without a style" "must declare its \`style\`" \
  "python3 - <<'PY'
from pathlib import Path
p = Path('icons/mappings/icons.yaml')
text = p.read_text()
text = text.replace('''      state: wifi-full
      style: default
''', '''      state: wifi-full
''', 1)
p.write_text(text)
PY"

run_case "style not declared by the group" "is not declared in the group's styles" \
  "sed -i '0,/style: default/s//style: fat/' icons/mappings/icons.yaml"

run_case "redundant variant pin" "already inherits" \
  "python3 - <<'PY'
from pathlib import Path
p = Path('icons/mappings/icons.yaml')
text = p.read_text()
text = text.replace('''    - name: signal-high
      template: settings-panel/signal/default/icon.svg
      output: settings-panel-signal-high.svg
''', '''    - name: signal-high
      template: settings-panel/signal/default/icon.svg
      output: settings-panel-signal-high.svg
      color_mappings:
        OPACITY_BAR_4: \"1\"
''', 1)
p.write_text(text)
PY"

run_case "state table names no variant" "names no variant in this group" \
  "sed -i 's/wifi-full: wifi-full-default/wifi-full: wifi-full-missing/' icons/mappings/icons.yaml"

if [ "$fail" -ne 0 ]; then
  echo "verify-negative: FAIL -- at least one case did not bite"
  exit 1
fi
echo "verify-negative: PASS -- $case_no/$case_no contract violations fail the gate by name"
