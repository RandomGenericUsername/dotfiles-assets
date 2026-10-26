---
id: BUG-001
title: "wlogout Logout runs terminate-user and leaves SDDM on a black VT"
kind: bug
status: in-progress
lane: 2 — bounded config change (bug lane; no OpenSpec change)
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/bug-001/
branch: ticket/bug-001-wlogout-logout-uwsm-stop
repro: "At v0.6.0 or earlier, in the disposable dotfiles VM on the production `hyprland-uwsm.desktop` session, run wlogout -> Logout (key `e`), whose action was `loginctl terminate-user $USER` (`configs/wlogout/layout:15`); the session disappears, the VT stays black with a cursor, and no Pixie greeter returns."
observed: "Boot `ccd99035ee63446bb6493da9a6cfb82b` (2026-10-26, local -05): `Session started true` at 14:31:34, then at 14:35:11 systemd SIGTERMs `sddm-helper` inside `session-2.scope`; SDDM logs `Authentication error: SDDM::Auth::ERROR_INTERNAL \"Process crashed\"`, `sddm-helper ... crashed (exit code 1)` and `sddm-helper exited with 1`, and never logs a second `Greeter starting` or `Display server started`; both session 2 (user) and session 3 (manager) are removed; the power key at 14:36:31 is the only recovery. The same helper exit-1 signature appears on 8 boots from 2026-10-23 to 2026-10-26."
expected: "After the consumer re-provision deploys v0.6.1, Logout returns to the Pixie greeter on seat0 in <30 s with `Auth: sddm-helper exited successfully` and a second `Greeter starting` / `Display server started`; no `Process crashed` / `exited with 1` for the user-session helper; the next login works; repeated 5 times with each session up at least 180 s; `check-session-bounce.py` exits 0."
---

# wlogout Logout runs terminate-user and leaves SDDM on a black VT

## Summary

The **Logout** tile in this repo's wlogout layout was the controllable trigger
of the black-VT logout failure attributed in `dotfiles-provision` BUG-005.
Through `v0.6.0` the tile ran `loginctl terminate-user $USER`, which ended every
session of the user, including the graphical session and the systemd user
manager. The `sddm-helper` process lives in the graphical session's scope;
logind sent it `SIGTERM` **and** `SIGHUP`, the helper caught only `SIGTERM`, and
`SIGHUP` killed it. SDDM 0.21.0 read the resulting exit code 1 as
`Auth::HELPER_AUTH_ERROR` and deliberately skipped the greeter restart, so the
VT was left with no compositor and no greeter: black VT plus cursor.

This is upstream SDDM [#1908](https://github.com/sddm/sddm/issues/1908); the fix
is open as PR [#2103](https://github.com/sddm/sddm/pull/2103) and is not in
0.21.0. weston, Pixie, uwsm and the provision configuration are not the cause.
The assets fix is one line: `configs/wlogout/layout:15` now runs
`"action" : "uwsm stop"`.

**Status: implemented in `v0.6.1`.** The user approved the one-line behavior
change on 2026-10-26 and waived the VM matrix on the same date: the root cause
is proven from the captured boot and upstream sources, and the host logout
after the consumer re-provision is the acceptance. The consumer pin train is a
separate orchestration step; host acceptance is pending until it deploys
`v0.6.1`.

Cross-repo evidence:

- [BUG-005 attribution — logout leaves a black VT](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md)
- [BUG-005 VM-only logout matrix](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md)
- [BUG-005 ticket — repro, captured boot, recurrence](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/ticket.md)

## Repro

**GUI path (production session; the failing action on `v0.6.0` and earlier):**

1. Log in to Hyprland through SDDM using the **Hyprland (uwsm-managed)**
   session (`/usr/share/wayland-sessions/hyprland-uwsm.desktop`,
   `Exec=uwsm start -e -D Hyprland hyprland.desktop`).
2. Open the AGS bar power menu, then the wlogout **Logout** tile (or press `e`).
   The tile action was `loginctl terminate-user $USER`
   (`configs/wlogout/layout:14-17` before `v0.6.1`).
3. Observe: the session stops, the screen drops to a black VT with a blinking
   cursor, and no greeter returns. A short power-button press is the only
   recovery.

**Non-GUI equivalent (disposable VM only — do not run on the host):**

```sh
loginctl terminate-user "$USER"
```

**VM precondition (historical; matrix waived):** the stock `dotfiles-v3` `make vm-fresh`
autologin uses `Session=hyprland.desktop` (plain `/usr/bin/start-hyprland`),
**not** the production `hyprland-uwsm.desktop`. Switching the VM autologin was a
requirement of the VM matrix, which the user waived on 2026-10-26; no VM was
run for this fix.

Evidence: `git show v0.6.0:configs/wlogout/layout` lines 14-17 carry the
historical `terminate-user` action; the current `uwsm stop` line is
`configs/wlogout/layout:14-17`; the GUI path and production session entry are
quoted in the provision BUG-005 ticket.
Verify: `git show v0.6.0:configs/wlogout/layout | sed -n '13,18p'` and
`sed -n '13,18p' configs/wlogout/layout` and
`rg -n '^repro:' tickets/bug-001-wlogout-logout-uwsm-stop/ticket.md`.

## Observed

Boot `ccd99035ee63446bb6493da9a6cfb82b` (2026-10-26, local time -05):

| Time | Event |
| --- | --- |
| 14:31:21.556868 | `Display server started.` |
| 14:31:21.557724 | `Greeter starting...` |
| 14:31:34.354005 | `Greeter stopped. SDDM::Auth::HELPER_SUCCESS` |
| 14:31:34.453131 | `Session started true` |
| 14:35:11.706771 | `session-2.scope: Killing process 1455 (sddm-helper) with signal SIGTERM.` |
| 14:35:11.707201 | `uwsm[1515]: Received SIGHUP, stopping wayland-session-envelope@hyprland.desktop.target...` |
| 14:35:11.707710 | `Authentication error: SDDM::Auth::ERROR_INTERNAL "Process crashed"` |
| 14:35:11.707720 | `Auth: sddm-helper (...) crashed (exit code 1)` |
| 14:35:11.707725 | `Auth: sddm-helper exited with 1` |
| 14:35:14.981900 | `Removed session 2.` |
| 14:35:15.427353 | `Removed session 3.` |
| 14:36:31.991908 | `Signal received: SIGTERM` (short power-button press) |

There is **no** `Adding new display...`, `Removing display...`, second
`Display server started.`, second `Greeter starting...`, or weston start after
14:35:11. `sddm` stays active; the VT is black with a cursor. Both session 2
(`Class=user`) and session 3 (`Class=manager`) are removed, and the user
manager's PAM session is closed — the signature of a user-wide teardown, not a
single-session logout.

The same `Auth: sddm-helper ... crashed (exit code 1)` signature for the
user-session helper appears on **8 boots** from 2026-10-23 to 2026-10-26 (table
in the provision BUG-005 ticket), so this is deterministic, not a one-off race.
`coredumpctl list sddm-helper` finds no coredump: exit 1 is a signal-driven
termination path, not a segfault.

Evidence: the boot log excerpts above and the full mechanism in
[attribution.md](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md);
recurrence table in the provision BUG-005 ticket.
Verify: `journalctl -b -1 -u sddm --no-pager | grep -nE 'Display server started|Greeter starting|Process crashed|exited with|Adding new display|Removing display'`.

## Expected

After the consumer re-provision deploys `v0.6.1`:

- After **Logout**, SDDM tears the user session down cleanly and restarts the
  Pixie/Wayland greeter on seat0 within **< 30 s**.
- SDDM logs `Auth: sddm-helper exited successfully` and a second
  `Greeter starting...` / `Display server started.`; no
  `ERROR_INTERNAL "Process crashed"` / `exited with 1` for the user-session
  helper.
- A subsequent login works. The cycle works **5 times in a row**, each session
  up at least 180 s (the session checker treats a shorter logout as an early
  logout).
- `python3 scripts/check-session-bounce.py --since "<start>"` (from
  `dotfiles-v3`) exits 0.
- No power-button recovery is needed.

## Root cause (attributed; full proof in provision BUG-005)

1. **Trigger — the pre-`v0.6.1` Logout tile.** `configs/wlogout/layout:15` ran
   `loginctl terminate-user $USER`. That ended every session of the user — the
   graphical session and the systemd user manager — not the session's normal
   logout.
2. **Failure mode — SDDM 0.21.0 misclassifies the SIGHUP-killed helper.**
   logind stops `session-2.scope` with `KillSignal=15` and `SendSIGHUP=yes`.
   `sddm-helper` catches SIGTERM but not SIGHUP, so SIGHUP kills it before Qt
   can dispatch the SIGTERM notifier. Qt reports `CrashExit` with exit code 1
   (the signal number).
3. **No greeter restart.** SDDM's `Auth.cpp` casts exit code 1 to
   `Auth::HELPER_AUTH_ERROR`; `Display::slotHelperFinished()` calls `stop()`
   only when the status is **not** `HELPER_AUTH_ERROR`. The greeter was already
   stopped after login, so the VT is left with no compositor and no greeter.
4. **Not weston/Pixie/uwsm.** The greeter's weston finished normally at login
   (14:31:34.351617); no second weston is ever requested. The Pixie timeout
   patch is inert because no greeter process exists. uwsm stops cleanly on
   HUP/TERM; the wrong verb is chosen by wlogout.

The systemic defect is upstream SDDM #1908; PR #2103 (restart the greeter when
the helper is signal-killed) is open and not in 0.21.0. The assets-side fix
below does not patch SDDM; it avoids the user-wide teardown that provokes it.

Evidence: [attribution.md](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md)
§1–§5; SDDM v0.21.0 `src/auth/Auth.cpp:220-233`,
`src/auth/Auth.h:84-89`, `src/daemon/Display.cpp:524-532`.
Verify: `curl -fsSL https://raw.githubusercontent.com/sddm/sddm/v0.21.0/src/daemon/Display.cpp | sed -n '524,532p'`
and
`curl -fsSL https://raw.githubusercontent.com/sddm/sddm/v0.21.0/src/auth/Auth.cpp | sed -n '220,233p'`.

## Fix (implemented in `v0.6.1`)

**One line, one file** — `configs/wlogout/layout:15`:

```diff
-    "action" : "loginctl terminate-user $USER",
+    "action" : "uwsm stop",
```

Why `uwsm stop`:

- It asks the user manager to stop the compositor unit and waits for the job.
  The `uwsm start` wrapper (the helper's child) exits normally; the helper
  exits 0; SDDM takes `HELPER_SUCCESS` → `Display::stop()` →
  `Seat::displayStopped()` → a new weston/Pixie greeter.
- `loginctl terminate-session "$XDG_SESSION_ID"` still stops the session scope,
  so systemd still sends SIGTERM+SIGHUP to the helper. It is expected to
  reproduce the failure; the VM matrix records it as case B.
- `hyprctl dispatch exit` is the compositor-driven control (VM case D); it is
  not the chosen action because `uwsm stop` expresses the session manager's
  own stop path and works for the production `hyprland-uwsm.desktop` session.

**Explicitly out of scope — do not change:**

- The other five power tiles and their labels, texts and keybinds:
  Lock `l` (`layout:1-6`), Hibernate `h` (`layout:7-12`), Shutdown `s`
  (`layout:19-24`), Suspend `u` (`layout:25-30`), Reboot `r`
  (`layout:31-36`). Only the Logout **action string** changes; Logout keeps
  `"label": "logout"`, `"text": "Logout"`, `"keybind": "e"`.
- The wlogout icons and mappings (`icons/mappings/icons.yaml:174-194`), the
  wlogout stylesheet source (`templates/wlogout/style.css.tpl`) and the
  rendered/deployed `~/.config/wlogout/` copy (deployed by the consumer, not
  edited here).
- SDDM, weston, Pixie, uwsm and provision configuration. No provision config
  change fixes a signal-killed helper's exit-code classification; the only
  systemic fix is upstream PR #2103 / a backport, which is out of scope.

Evidence: `configs/wlogout/layout:1-36`; `uwsm stop -h` → "Stops compositor and
optionally removes generated units."; attribution.md §6 for the clean
`HELPER_SUCCESS` path.
Verify: `sed -n '1,36p' configs/wlogout/layout`, `git diff v0.6.0..v0.6.1 -- configs/wlogout/layout`
(one line), and `uwsm stop -h`.

**Static guard (separate commit).** `scripts/validate-configs.py` now parses
`configs/wlogout/layout` as a sequence of JSON tiles, requires exactly one
`"label": "logout"` tile and requires its action to be exactly `uwsm stop`. A
revert fails `make validate-configs` naming the action. The fix commit itself
changes only line 15 of the layout; the guard and its documentation are
separate commits.

## Status and blockers

**Status: `in-progress`.** The fix and its static guard are on `master`; assets
`v0.6.1` is tagged and released. The remaining work is the separate consumer
pin train followed by the user-run host acceptance.

- **User approval — granted 2026-10-26.** Logout is now a session-manager stop
  (`uwsm stop`), not a user-wide teardown.
- **VM matrix — waived by the user 2026-10-26.** No VM was run. The root cause
  is proven (captured boot plus the upstream SDDM source path), and the
  acceptance is the host logout after re-provision rather than the
  disposable-VM matrix.
- **Consumer pin train — separate orchestration step.** Bumping the provision
  mirrors, the engine tag and `dotfiles-v3`'s `assets.yaml` / `installer.pin`
  is not part of this ticket's assets change.

## Acceptance

- [x] **Approval recorded** for the one-line action change (user decision,
      2026-10-26).
- [x] **VM matrix waived** by the user (2026-10-26); no VM was run. The
      behavioral proof is the host acceptance below after the re-provision.
- [x] **One-line fix:** `configs/wlogout/layout:15` is
      `"action" : "uwsm stop",`; no other tile, keybind, label, icon or
      stylesheet changed.
- [x] **Static guard:** `make validate-configs` fails when the Logout action is
      not `uwsm stop`; the red/green proof is in Regression test.
- [x] **Assets gates green** on the fix commit: `make validate-configs`,
      `make validate`, `make gates`, `make gates-ci`, `make hermetic` and
      `make ci-gates-parity` exit 0.
- [x] **Release:** annotated `v0.6.1` tagged on `master` (tag object
      `b2ad3a9`, commit `f8cc828`), CI run
      [40403377594](https://github.com/RandomGenericUsername/dotfiles-assets/actions/runs/40403377594)
      green (9/9 jobs), GitHub Release
      [v0.6.1](https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.6.1)
      published (notes only, no assets), tag never moved.
- [ ] **Consumer pin train** (separate orchestration step): provision mirrors,
      engine release and `dotfiles-v3` `assets.yaml` + `installer.pin` move to
      `v0.6.1` / the new engine tag.
- [ ] **Host 5-cycle acceptance** (user-run after re-provision): Logout returns
      to the Pixie greeter on seat0 in **< 30 s**; a subsequent login works;
      repeated **5 times**, each session up at least 180 s; no
      `Process crashed` / `exited with 1` for the user-session helper.
- [ ] **Session checker green:** `python3 scripts/check-session-bounce.py
      --since "<start>"` from `dotfiles-v3` exits 0 with five clean cycles and
      no `Process crashed` / `exited with 1` for the user-session helper.
- [x] `tickets/INDEX.md` updated in the same commit as every status change.

## Regression test

The **behavioral regression test** is the host 5-cycle acceptance above, after
the consumer pin train re-provisions `configs/wlogout/layout` through the
user-run `./bootstrap.sh` apply/verify path. The VM matrix was waived on
2026-10-26. Re-running the historical `repro:` on `v0.6.0` or earlier leaves
the black VT; on `v0.6.1` and later the Logout tile must return to the Pixie
greeter.

The **static guard** is now a repo gate, not a manual command:

```bash
make validate-configs
# PASS -- ...; wlogout Logout action is 'uwsm stop'
```

Red proof: with `configs/wlogout/layout:15` temporarily restored to
`"action" : "loginctl terminate-user $USER",`, `make validate-configs` exits
non-zero naming the action; restoring the line makes it pass. The fix commit
still changes exactly line 15 of `configs/wlogout/layout`; the guard lives in
`scripts/validate-configs.py` and its documentation.

## Release and pin plan (assets step complete; consumer steps pending)

Assets, engine, then v3 are pinned in that order. Do not bump a consumer
before the assets tag exists and its CI is green; do not bump the v3 manifest
before the new engine exists, because v3's coverage gate compares the manifest
tag against the engine mirrors.

| # | Repo | Change | Gate |
| --- | --- | --- | --- |
| 1 | `dotfiles-assets` | **This release:** one-line fix, static guard, `CHANGELOG.md` `0.6.1`; annotated PATCH tag `v0.6.1` | `make validate-configs`, `make validate`, `make gates`, `make gates-ci`, `make hermetic`, `make ci-gates-parity`; CI on the tagged commit |
| 2 | `dotfiles-provision` | Bump the nine pin mirrors (below); `pyproject.toml:3` `0.1.15` → next PATCH (e.g. `0.1.16`); `CHANGELOG.md`; annotated engine tag + release | `make test`, `make gates`, `make assets-parity`; CI |
| 3 | `dotfiles-v3` | One commit: `dotfiles/provisioning/assets.yaml` `tag: v0.6.0` → `v0.6.1` (line 20) and the three `assets/v0.6.0/...` source paths (lines 31, 34, 37; the csg `v0.2.0` path stays) **plus** `dotfiles/provisioning/installer.pin` `v0.1.15` → the new engine tag | `make gates-ci`, `make deploy-coverage` |
| 4 | host | Re-provision with `./bootstrap.sh` (user-run; sudo) or the equivalent `make provision` apply/verify path | provision + verify green; 5-cycle acceptance |

Provision pin mirrors — all move to the assets tag from step 1:

- `ansible/roles/assets/vars/main.yml:19` — `assets_pinned_tag`
- `ansible/roles/btop_config/vars/main.yml:78` — `btop_config_assets_pinned_tag`
- `ansible/roles/compositor_configs/vars/main.yml:46` — `compositor_configs_assets_pinned_tag`
- `ansible/roles/config_copies/vars/main.yml:58` — `config_copies_assets_pinned_tag`
- `ansible/roles/display_manager/vars/main.yml:37` — `display_manager_assets_pinned_tag`
- `ansible/roles/kitty_config/vars/main.yml:30` — `kitty_config_assets_pinned_tag`
- `ansible/roles/verify/vars/main.yml:167` — `verify_assets_pinned_tag`
- `ansible/roles/wlogout_config/vars/main.yml:12` — `wlogout_config_assets_pinned_tag`
- `ansible/roles/zsh_config/vars/main.yml:36` — `zsh_config_assets_pinned_tag`

Notes:

- This is a **PATCH** release: one deployment-fixed config file's action
  changes. `configs/` has `schema_major: null` in `catalog.yaml`; no schema,
  path, or class inventory changes, so no MINOR/MAJOR bump and no
  `schema_major` change. Follow the v0.5.1 precedent: `CHANGELOG.md` gets the
  version; `catalog.yaml`'s `tag:` is the inventory tag and stays at `v0.6.0`
  when the inventory does not change.
- The wlogout role deploys `configs/wlogout/layout` through `config_copies`
  (`config-copies.yaml` names wlogout as per-file `files: [layout]`), so the
  re-provision in step 4 is what actually updates `~/.config/wlogout/layout`;
  this repo never edits the deployed copy.
- The host 5-cycle acceptance is **user-run** and only after the re-provision.
  Do not power-cycle or log out the host to test before the fix is deployed.
- **Assets state:** `v0.6.1` is tagged and released; `catalog.yaml` stays at
  `v0.6.0` because the inventory did not change. Steps 2–4 are outside this
  assets ticket and are coordinated by the orchestrator.

## Remaining work (self-contained)

1. **Orchestrator, separate step:** bump the nine provision pin mirrors to
   `v0.6.1`, cut the next provision PATCH with its annotated tag/release, then
   bump `dotfiles-v3/dotfiles/provisioning/assets.yaml` (`tag` plus the three
   `assets/v0.6.1/...` source paths) and `installer.pin`. Do not touch those
   from this assets ticket.
2. **User, after re-provision:** run the host 5-cycle acceptance — log out via
   wlogout Logout five times, each session up at least 180 s; each logout must
   return to the Pixie greeter in **< 30 s** and the next login must work.
3. **User:** run `python3 scripts/check-session-bounce.py --since "<start>"`
   from `dotfiles-v3`; it must exit 0 with five clean cycles and no
   `Process crashed` / `exited with 1` for the user-session helper.
4. **Close the ticket** only when the host acceptance and session-checker boxes
   are ticked; update `tickets/INDEX.md` in the same commit as the status
   change.

## Evidence

- Fix commit `19e82f6` changes exactly one line:
  `git diff v0.6.0..19e82f6 -- configs/wlogout/layout` → 1 file, 1 insertion,
  1 deletion.
- Red proof: with line 15 temporarily restored to
  `"action" : "loginctl terminate-user $USER",`, `make validate-configs` →
  **exit 2** (`make` wraps the validator's exit 1), naming the old action and
  the expected `uwsm stop`.
- Green: `make validate-configs` → exit 0, `make validate` → exit 0,
  `make gates` → exit 0, `make gates-ci` → exit 0, `make hermetic` → exit 0,
  `make ci-gates-parity` → exit 0. The final line for each config gate names
  `wlogout Logout action is 'uwsm stop'`; hermetic ends
  `hermetic: PASS -- the corpus validates with no HOME, no XDG state and a
  foreign cwd`.
- `shellcheck` is present at `/home/inumaki/.local/bin/shellcheck`; the shell
  half of `lint`/`validate-desktop`/`hermetic` ran with no workaround.
- `catalog.yaml` stays at `tag: v0.6.0` because the inventory did not change;
  `make validate` therefore reports `tag=v0.6.0` while the release tag is
  `v0.6.1`.
- Release: annotated tag object `b2ad3a90953633602ec6a04e564f6f98ae11ce2a`,
  peeled commit `f8cc8288eebeab1f0759d6dec05b978b662ae19e`; CI run
  [40403377594](https://github.com/RandomGenericUsername/dotfiles-assets/actions/runs/40403377594)
  → **success**, 9/9 jobs on `f8cc828`; GitHub Release
  [v0.6.1](https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.6.1)
  not a draft/prerelease, `assets: 0`, target `master`.
- Verify: `make validate-configs && make validate && make gates && make gates-ci
  && make hermetic && make ci-gates-parity`; `git cat-file -t v0.6.1` → `tag`;
  `gh release view v0.6.1 --json isDraft,isPrerelease,assets`.

## References

- Provision BUG-005 attribution — <https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md>
- Provision BUG-005 VM matrix — <https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md>
- Provision BUG-005 ticket — <https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/ticket.md>
- SDDM issue #1908 — <https://github.com/sddm/sddm/issues/1908>
- SDDM PR #2103 — <https://github.com/sddm/sddm/pull/2103>
- SDDM v0.21.0 `src/auth/Auth.cpp`, `src/auth/Auth.h`, `src/daemon/Display.cpp`, `src/daemon/Seat.cpp`, `src/helper/HelperApp.cpp`, `src/helper/UserSession.cpp` — <https://github.com/sddm/sddm/tree/v0.21.0>
- systemd v262 `src/login/logind-dbus.c:4517-4521` (`SendSIGHUP`) — <https://github.com/systemd/systemd/blob/v262/src/login/logind-dbus.c>
- Qt v6.12 `src/3rdparty/forkfd/forkfd.c:252-258`, `src/corelib/io/qprocess_unix.cpp:1328-1329` — <https://github.com/qt/qtbase/tree/v6.12.0>
- This repo: `configs/wlogout/layout:1-36`, `scripts/validate-configs.py`, `configs/README.md`, `icons/mappings/icons.yaml:174-194`, `templates/wlogout/style.css.tpl`.
- Consumer acceptance checker: `dotfiles-v3/scripts/check-session-bounce.py`; host procedure in `dotfiles-v3/dev/README.md` (5 logins, each ≥180 s).
