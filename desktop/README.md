# desktop — application entries and the helper scripts a keybind runs

This class holds the per-user desktop integration the consumer deploys for you: six
application entries (rofi's `drun` mode lists them) and `toggle-touchpad`, the helper the
touchpad Fn key calls.

```text
applications/  6 *.desktop entries
scripts/       toggle-touchpad   (0755)
desktop.yaml   one record per entry: {file, requires, optional}
```

Every entry is an **override or an addition**, never a duplicate of a packaged launcher for
its own sake:

| Entry | What it is | Why it is authored here |
| --- | --- | --- |
| `antigravity-ide.desktop` | override of the packaged Antigravity entry | adds the Ozone/Wayland flags so it runs Wayland-native on Hyprland (the packaged `%F` is preserved) |
| `code.desktop` | override of the packaged VS Code entry | same: the AUR package's own launcher, plus the Wayland flags |
| `devin-desktop.desktop` | override of the packaged Devin entry | same (Windsurf was rebranded upstream; the provisioning key stays `windsurf`) |
| `tidal-hifi.desktop` | override of the packaged TIDAL entry | keeps the packaged Wayland flags **and** adds `--disable-dev-shm-usage`, the workaround Castlabs Electron needs |
| `copilot.desktop` | new entry | GitHub Copilot CLI ships no entry at all, so it is invisible to `drun` |
| `codex.desktop` | new entry | OpenAI Codex CLI ships no entry at all, same reason |

## The three validation layers (spine AD-10)

A dead menu entry is the failure this class exists to prevent: rofi still lists an entry whose
binary is not installed, so the click does nothing. No single repository can answer all of it,
so the checks are split by who can actually observe the fact:

| Layer | Owner | Asserts | Failure mode |
| --- | --- | --- | --- |
| 1. static | **this repository** (`make validate-desktop`) | every entry parses (`[Desktop Entry]`, `Type`, `Name`, `Exec`, `Icon`, `TryExec`), `Exec` argv[0] names a binary in the entry's `requires`, `TryExec` is present and names that same binary, `desktop.yaml` equals the `.desktop` set exactly, scripts are `shellcheck`-clean, executable and have a shebang | the tag cannot be cut |
| 2. deploy-time | the consumer's installer | resolves each entry's `requires[]` on the target; a missing **required** binary fails the run, a missing **optional** one is reported and the entry is skipped | provision fails / degrades loudly |
| 3. deployed | the consumer's `verify` | the deployed set is present, every deployed `Exec` binary resolves, `toggle-touchpad` is executable, and every script/launcher a Hyprland keybind invokes exists | the gate fails |

Layer 1 never asks whether a package is installed: that is a host fact, and a data repository
that asserted it would be guessing.

## `TryExec` — the key the corpus did not carry

A `.desktop` `TryExec` names the binary a launcher probes to decide whether the application is
installed. The corpus carried **zero** `TryExec=` keys before this class landed, which is exactly
why a missing binary produced a silent dead entry. Each entry now declares the binary its `Exec`
launches:

```ini
Exec=/usr/bin/code --enable-features=… %F
TryExec=code
```

For the two kitty-hosted CLIs the launched binary is `kitty` (they run `kitty … codex`), so their
`TryExec` is `kitty`, not the CLI — probing for the CLI would hide the entry even when the
terminal it needs is present.

## `desktop.yaml` — `requires` and `optional`

```yaml
schema_major: 1
entries:
  - file: codex.desktop
    requires:
      - kitty
    optional:
      - codex
```

- **`requires`** is what the entry cannot work without — the launcher itself:
  `basename(Exec argv[0])`, which is also the `TryExec` value. An IDE override requires its own
  binary (`code`, `devin-desktop`, `antigravity-ide`); the TIDAL override requires `tidal-hifi`;
  the two CLI wrappers require `kitty`. A missing required binary means the deploy contract is
  broken, so the consumer's provision fails naming the entry and the binary.
- **`optional`** is what makes an entry pointless but not the host unprovisionable: the CLI the
  kitty wrapper runs (`codex`, `copilot`). The CLI's package belongs to the consumer's packages
  role, not to this corpus, so its absence must **not** fail a provision — the consumer reports
  it and skips that one entry.

The lists are derived from the `Exec` line, and `validate-desktop` enforces that: a name that
does not occur in its entry's own command cannot be declared, so a stale record cannot outlive
the command it described. `desktop.yaml` is the class's schema-bearing contract
(`schema_major: 1`, spine AD-12).

## What is deliberately **not** here

- **Launcher wrappers** (`rofi-ui`, `capture-ui`, `clipboard-ui`, `wallpaper-selector-ui`,
  `icon-color-mapping-editor`, `btop-theme-studio`). They are Jinja-rendered by the consumer's
  `cli_tools` role because they bake in installed-binary paths (`ags`, the unit's CLIs), so they
  are code with host inputs, not static data. `scripts/` holds **repo-authored static scripts
  only** — today exactly `toggle-touchpad`, which reads its device and state at run time.
- **Installed binaries.** This repository declares a binary; it never installs one.
- **Rendered output and mutable state.** No `mimeapps.list`, no cached `desktop-file-validate`
  output, no launcher database: those are produced by the desktop environment and would make
  this repository a second source of truth that drifts (`make validate`, spine AD-11).

## How the class is checked

```bash
make validate-desktop
# validate-desktop: entries=6 with_TryExec=6 contract_records=6 requires=7 optional=2 scripts=1
# validate-desktop: shellcheck -> 1 script(s) clean
# validate-desktop: PASS
```

The gate is not vacuous — break one entry and it names the binary:

```bash
cp desktop/applications/code.desktop /tmp/opencode/code.bak
sed -i 's/^Exec=.*/Exec=definitely-not-installed --flag %F/' desktop/applications/code.desktop
make validate-desktop; echo "rc=$?"
# non-zero: desktop/applications/code.desktop: Exec launches 'definitely-not-installed', which is
# not in its declared requires ['code'] …
cp /tmp/opencode/code.bak desktop/applications/code.desktop
```

`make lint` runs `shellcheck` too (the class-independent sweep). Both targets fail loudly when
`shellcheck` is missing and scripts are present — a silent skip and a pass are indistinguishable
in a green log.

## Byte identity

The six entries and `toggle-touchpad` were imported byte-for-byte from the consumer corpus.
`cmp` returns 0 for the script; each entry differs by exactly **one added line** — its
`TryExec=`, which layer 1 requires and the pre-split corpus never had. Nothing else was edited:
the packaged `Exec` lines, comments, categories, MIME types and startup hints are the bytes the
consumer shipped before the split.
