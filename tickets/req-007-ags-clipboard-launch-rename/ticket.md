---
id: REQ-007
title: "Rename the clipboard launcher/autostart/keybind from hypr-pano to clipboard"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-007/
branch: ticket/REQ-007-ags-clipboard-launch-rename
---

# Rename the clipboard launcher/autostart/keybind from hypr-pano to clipboard

## Requirement

Cut the static config corpus over to the clipboard pilot (`ags-apps` REQ-009,
AD-35) and put every AGS cold start under the shared per-user launch lock
(`dotfiles-provision` REQ-008, AD-28):

- `configs/hypr/autostart.lua` starts `~/.config/ags-clipboard` with the
  `clipboard` instance/log name, not `ags-hypr-pano`;
- `configs/hypr/keybindings.lua` invokes `clipboard-ui`, not `hypr-pano-ui`;
- every AGS autostart line (§ bar, capture, notifications, clipboard) goes
  through the provisioned `ags-run-locked` wrapper with `--expect-instance`,
  because four concurrent `ags run` invocations race on the single
  `$XDG_RUNTIME_DIR/ags.js` bundle;
- the existing 2/3/4 s stagger sleeps stay — the wrapper holds the shared lock
  only until the instance registers on the AGS bus, not for the process
  lifetime;
- any desktop entry, comment or config reference to the app's old name is
  updated or removed;
- the provisioned launcher template and the app itself belong to
  `dotfiles-provision` REQ-008 and `ags-apps` REQ-009, not this repo.

The runtime clipboard daemon keeps `dotfiles-runtime clipboard`; its data-path
migration is in the runtime ticket.

## Tasks

- [x] **Bar under the lock** — `configs/hypr/autostart.lua:28` runs
      `bash -lc '$HOME/.local/bin/ags-run-locked --expect-instance ags'`
      (no `-d`: the bar uses the AGS default `~/.config/ags`).
- [x] **Capture under the lock** — `autostart.lua:36`, `sleep 2`, `-d
      $HOME/.config/ags-capture`, `--log-file …/capture.log`,
      `--expect-instance capture`.
- [x] **Notifications under the lock** — `autostart.lua:44`, `sleep 4`, `-d
      $HOME/.config/ags-notifications`, `--log-file …/notifications.log`,
      `--expect-instance notifications`.
- [x] **Clipboard rename + lock** — `autostart.lua:62`, `sleep 3`, `-d
      $HOME/.config/ags-clipboard`, `--log-file …/clipboard.log`,
      `--expect-instance clipboard`; the comment above it names the
      standalone `clipboard` instance and the runtime job that owns capture.
- [x] **Keybind rename** — `configs/hypr/keybindings.lua:61` invokes
      `clipboard-ui`; the description stays “Open clipboard history”; the
      launcher list comment at `keybindings.lua:31` and
      `configs/hypr/env-variables.lua:5` name `clipboard-ui`.
- [x] **Docs** — `configs/README.md` gained the AGS launch-discipline section
      (lock lifecycle, per-surface identity table, rename note);
      `desktop/README.md` no longer lists the retired launcher name.
- [x] **Assets gates green** — `make gates`, `make gates-ci`,
      `make validate-configs` and `make ci-gates-parity` exit 0 (Evidence).
- [x] **Release** — annotated `v0.6.2` tagged locally on `master`; no push,
      no publish, no provision (this agent's scope).
- [x] **No duplicate surface** — one autostart line and one `SUPER + V` bind
      per app; the old clipboard line is replaced, not duplicated.

Explicitly **not** in this repo (left to their owners):

- the provisioned `clipboard-ui` launcher template, the `ags-clipboard`
  config link, and installing `~/.local/bin/ags-run-locked` — provision
  REQ-008 (see Provision follow-up);
- the `clipboard` app source, `app.manifest.json`, `palette-refresh` handler
  and repository release — `ags-apps` REQ-009;
- the `hypr-pano` → `clipboard` data-path migration in the runtime daemon —
  `dotfiles-runtime` REQ-002;
- the v3 `apps.yaml` entry rename and the assets pin bump — `dotfiles-v3`.

## Acceptance

- [x] `rg -n 'hypr-pano|ags-hypr-pano' configs desktop` returns no live app
      reference: **exit 1, zero matches**. The only remaining occurrences in
      the repository are historical — `CHANGELOG.md` (0.5.0/0.6.2 notes) and
      this ticket/`tickets/INDEX.md` record.
- [x] Autostart launches `ags-clipboard` with the `clipboard` instance/log
      (`configs/hypr/autostart.lua:62`).
- [x] The keybind invokes `clipboard-ui` with the “Open clipboard history”
      description (`configs/hypr/keybindings.lua:59-63`).
- [x] `make validate-configs`/`make gates` is green; the asset schema/catalog
      remains valid (catalog still reports `tag=v0.6.0`, the inventory tag;
      the release tag is `v0.6.2`).
- [x] The cutover leaves no duplicate autostart/keybind entry.
- [x] Every AGS autostart line uses `ags-run-locked --expect-instance` exactly
      once per identity (`ags`, `capture`, `notifications`, `clipboard`).

## Evidence

- Implementation commit **`16a43b8`** — `feat(configs): start every AGS app
  under the shared launch lock`. Diff: `configs/hypr/autostart.lua` (four
  `ags run` lines → four wrapper lines, clipboard rename),
  `configs/hypr/keybindings.lua` (`hypr-pano-ui` → `clipboard-ui` and the
  instance comment), `configs/hypr/env-variables.lua` (launcher list comment).
- Docs commit **`e11b545`** — `docs(configs): document the AGS launch lock and
  the clipboard rename` (`configs/README.md`, `desktop/README.md`,
  `CHANGELOG.md` 0.6.2, `README.md` release tag).
- `rg -n 'hypr-pano|ags-hypr-pano' configs desktop` → **exit 1, no output**.
- `grep -n 'ags-run-locked\|clipboard-ui' configs/hypr/autostart.lua
  configs/hypr/keybindings.lua` → four `--expect-instance` lines
  (`ags:28`, `capture:36`, `notifications:44`, `clipboard:62`) and the
  `clipboard-ui` bind at `keybindings.lua:61`.
- `luac -p configs/hypr/autostart.lua configs/hypr/keybindings.lua
  configs/hypr/env-variables.lua` → exit 0 (syntax parses).
- Wrapper interface check against `dotfiles-provision` engine **v0.1.19**
  (`ansible/roles/cli_tools/files/ags-run-locked`): the header states
  `ags-run-locked [--expect-instance NAME] [--lock-timeout SEC]
  [--register-timeout SEC] [--] <ags run args...>` and the body calls
  `ags run "$@"`; `diff` of that file against the v0.1.19 engine checkout
  (`dotfiles-v3/.worktrees/OPS-0114/.dev/dotfiles-provision-v0.1.19/…`) →
  **identical** (diff rc=0).
- Prototype proof of both call shapes, using the v0.1.19 wrapper plus a fake
  `ags` that records argv and publishes a name on `ags list`:
  - `ags-run-locked --expect-instance capture -d "$HOME/.config/ags-capture"
    --log-file "$HOME/.local/state/ags/capture.log"` → rc 0, instance
    `capture` registered, `ags run` argv
    `-d …/ags-capture --log-file …/capture.log`;
  - `ags-run-locked --expect-instance ags` → rc 0, instance `ags` registered,
    `ags run` invoked with no arguments (bar default config dir).
  So the wrapper strips its own options and does not require a literal `run`
  token.
- Gates (with the host's shellcheck on `PATH`; the `~/.local/bin/shellcheck`
  symlink is broken on this host, see Provision follow-up 5):
  `make gates` → **rc 0**, `make gates-ci` → **rc 0**,
  `make ci-gates-parity` → **rc 0** (8 GATES / 9 workflow jobs),
  `make validate-configs` → **rc 0**
  (`PASS -- … wlogout Logout action is 'uwsm stop'`).
- `make validate` reports `tag=v0.6.0` while the release tag is `v0.6.2`: the
  inventory did not change, so `catalog.yaml` stays at the inventory tag (the
  `v0.6.1` precedent).

## Provision follow-up (outside this repo — do not edit here)

The assets corpus now names surfaces the host does not yet have. Exact items,
in cutover order:

1. **Install the wrapper.** `dotfiles-provision` `cli_tools` copies
   `ansible/roles/cli_tools/files/ags-run-locked` to
   `{{ cli_tools_bin_dir }}/ags-run-locked` (`cli_tools/tasks/main.yml:44-48`),
   i.e. `~/.local/bin/ags-run-locked`. The host at `v0.6.2` time has **no**
   `~/.local/bin/ags-run-locked` (`command -v ags-run-locked` → not found), so
   the engine that ships it (v0.1.19) must be applied before the autostart
   lines can run. Until then each AGS autostart line exits 127.
2. **Render `clipboard-ui`.** Add/rename the `cli_tools` launcher template
   (`hypr-pano-ui.j2` → `clipboard-ui.j2`) with `INSTANCE="clipboard"`,
   `WINDOW="clipboard-window"`, `DIR="${HOME}/.config/ags-clipboard"`,
   `LOG="${HOME}/.local/state/ags/clipboard.log"`, cold start
   `ags-run-locked --expect-instance "$INSTANCE" -d "$DIR" --log-file "$LOG"`
   and the warm `ags request toggle -i "$INSTANCE"` path; install it to
   `~/.local/bin/clipboard-ui`.
3. **Link the config dir.** `config_links` must expose
   `~/.config/ags-clipboard` (replacing `ags-hypr-pano`) and the v3
   `dotfiles/provisioning/apps.yaml` entry must rename
   `app: hypr-pano` → `clipboard` with `instance: clipboard`,
   `configDir/configLink/spineLink/xdgLink: ags-clipboard`,
   `launcher: clipboard-ui`, `autostart: clipboard`.
4. **Pin and provision.** After that, bump the v3 `dotfiles-assets` pin to
   `v0.6.2`, apply the composition, and verify the four surfaces
   (`ags list` shows `ags/capture/notifications/clipboard`, the bind opens the
   overlay, `~/.local/state/ags/clipboard.log` is written).
5. **Host hygiene, not a repo defect:** the `~/.local/bin/shellcheck` symlink
   points at a deleted `/tmp/opencode/uvtools/shellcheck-py/bin/shellcheck`.
   The gates were run with a working shellcheck 0.11.0 from the uv cache; the
   host symlink should be repaired on the next provision.

Until 1–3 land, the new lines are inert (the wrapper/launcher binaries are
missing) but the corpus is internally consistent: every AGS launch takes the
lock, and no live reference to the retired clipboard name remains.

## Release

- Assets **`v0.6.2`**, annotated PATCH tag on `master` at `4fa35c4`
  (tag object `e94165b`), created locally; **not pushed, not published, not
  provisioned** — the orchestrator owns CI and the GitHub Release. The tag
  object is recorded here in the follow-up commit (the `v0.6.1`/BUG-001
  precedent).
- PATCH because no path, file count, catalog entry or `schema_major` changed:
  new launch lines in two existing config files plus a comment/doc rename.
- `catalog.yaml` stays at `v0.6.0` (inventory tag).
