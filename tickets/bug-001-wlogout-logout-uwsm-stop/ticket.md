---
id: BUG-001
title: "wlogout Logout runs terminate-user and leaves SDDM on a black VT"
kind: bug
status: triage
lane: 2 — bounded config change (bug lane; no OpenSpec change)
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/bug-001/
branch: ticket/bug-001-wlogout-logout-uwsm-stop
repro: "In the disposable dotfiles VM on the production `hyprland-uwsm.desktop` session, run wlogout -> Logout (key `e`), whose action is `loginctl terminate-user $USER` (`configs/wlogout/layout:15`); the session disappears, the VT stays black with a cursor, and no Pixie greeter returns."
observed: "Boot `ccd99035ee63446bb6493da9a6cfb82b` (2026-10-26, local -05): `Session started true` at 14:31:34, then at 14:35:11 systemd SIGTERMs `sddm-helper` inside `session-2.scope`; SDDM logs `Authentication error: SDDM::Auth::ERROR_INTERNAL \"Process crashed\"`, `sddm-helper ... crashed (exit code 1)` and `sddm-helper exited with 1`, and never logs a second `Greeter starting` or `Display server started`; both session 2 (user) and session 3 (manager) are removed; the power key at 14:36:31 is the only recovery. The same helper exit-1 signature appears on 8 boots from 2026-10-23 to 2026-10-26."
expected: "Logout returns to the Pixie greeter on seat0 in <30 s with `Auth: sddm-helper exited successfully` and a second `Greeter starting` / `Display server started`; no `Process crashed` / `exited with 1` for the user-session helper; the next login works; repeated 5 times with each session up at least 180 s; `check-session-bounce.py` exits 0."
---

# wlogout Logout runs terminate-user and leaves SDDM on a black VT

## Summary

The **Logout** tile in this repo's wlogout layout is the controllable trigger of
the black-VT logout failure attributed in `dotfiles-provision` BUG-005. The tile
runs `loginctl terminate-user $USER`, which ends every session of the user,
including the graphical session and the systemd user manager. The
`sddm-helper` process lives in the graphical session's scope; logind sends it
`SIGTERM` **and** `SIGHUP`, the helper catches only `SIGTERM`, and `SIGHUP`
kills it. SDDM 0.21.0 reads the resulting exit code 1 as
`Auth::HELPER_AUTH_ERROR` and deliberately skips the greeter restart, so the VT
is left with no compositor and no greeter: black VT plus cursor.

This is upstream SDDM [#1908](https://github.com/sddm/sddm/issues/1908); the fix
is open as PR [#2103](https://github.com/sddm/sddm/pull/2103) and is not in
0.21.0. weston, Pixie, uwsm and the provision configuration are not the cause.
The proposed assets change is one line: `"action" : "uwsm stop"` in
`configs/wlogout/layout:15`.

**This ticket is triage docs only.** It records the evidence, the proposed
one-line fix, the acceptance gate and the release/pin path. It does **not**
approve the behavior change and does not edit the layout.

Cross-repo evidence:

- [BUG-005 attribution — logout leaves a black VT](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md)
- [BUG-005 VM-only logout matrix](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md)
- [BUG-005 ticket — repro, captured boot, recurrence](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/ticket.md)

## Repro

**GUI path (production session; the failing action):**

1. Log in to Hyprland through SDDM using the **Hyprland (uwsm-managed)**
   session (`/usr/share/wayland-sessions/hyprland-uwsm.desktop`,
   `Exec=uwsm start -e -D Hyprland hyprland.desktop`).
2. Open the AGS bar power menu, then the wlogout **Logout** tile (or press `e`).
   The tile action is `loginctl terminate-user $USER`
   (`configs/wlogout/layout:14-17`).
3. Observe: the session stops, the screen drops to a black VT with a blinking
   cursor, and no greeter returns. A short power-button press is the only
   recovery.

**Non-GUI equivalent (disposable VM only — do not run on the host):**

```sh
loginctl terminate-user "$USER"
```

**VM precondition:** the stock `dotfiles-v3` `make vm-fresh` autologin uses
`Session=hyprland.desktop` (plain `/usr/bin/start-hyprland`), **not** the
production `hyprland-uwsm.desktop`. Switch the VM autologin or log in through
the greeter before testing; the full procedure is
[vm-matrix.md §0](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md).

Evidence: `configs/wlogout/layout:14-17` in this repo; the GUI path and the
production session entry are quoted in the provision BUG-005 ticket.
Verify: `sed -n '13,18p' configs/wlogout/layout` and
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

1. **Trigger — this repo's Logout tile.** `configs/wlogout/layout:15` runs
   `loginctl terminate-user $USER`. That ends every session of the user — the
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

## Proposed fix (NOT implemented)

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
  not the proposed action because `uwsm stop` expresses the session manager's
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
Verify: `sed -n '1,36p' configs/wlogout/layout` and `uwsm stop -h`.

## Status and blockers

**Status: `triage`. Blocked — no implementation until both gates clear.**

1. **User approval of the wlogout behavior change.** Logout would become a
   session-manager stop instead of a user-wide `terminate-user`. This is a
   user-visible behavior decision, not an implementation detail.
2. **VM matrix result.** Case C (`uwsm stop`) must show the Pixie greeter
   returning < 30 s with `Auth: sddm-helper exited successfully`; case D
   (`hyprctl dispatch exit`) is the ideal control. The matrix is user-run
   (sudo + disposable Incus VM); the host logout is destructive. See
   [vm-matrix.md §4](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md)
   for the decision rule.

If A/B/C/D all fail, **stop**: the wlogout action is not the only problem;
escalate to the SDDM helper-exit handling (upstream PR #2103 / a backport) and
do not implement the wlogout change. If C passes (D ideally), this ticket can
move to `in-progress` after the user approves.

No edit to `configs/wlogout/layout`, the deployed `~/.config/wlogout/`, or any
other repo is made by this ticket. Filing it does not approve the change.

## Acceptance

- [ ] **Approval recorded** for the one-line action change (user decision on
      this ticket).
- [ ] **VM case C** (`uwsm stop`): Pixie greeter returns on seat0 in **< 30 s**;
      `Auth: sddm-helper exited successfully`; a second `Greeter starting...` /
      `Display server started.`; weston + greeter processes present.
- [ ] **VM case D** (`hyprctl dispatch exit`, control): same clean helper exit
      and greeter return.
- [ ] **VM cases A/B recorded** for contrast: A reproduces the black VT; B
      records whether `terminate-session` also reproduces (expected: yes).
- [ ] **Subsequent login works** after each acceptance cycle; **5 cycles**,
      each session up at least 180 s.
- [ ] **Session checker green:** `python3 scripts/check-session-bounce.py
      --since "<start>"` from `dotfiles-v3` exits 0 with five clean cycles and
      no `Process crashed` / `exited with 1` for the user-session helper.
- [ ] **Assets gates green** on the fix commit: `make validate-configs`,
      `make gates`, `make gates-ci`, `make ci-gates-parity` exit 0.
- [ ] **Scope guard:** the fix commit changes exactly one line in
      `configs/wlogout/layout`; no tile/keybind/icon/style change.
- [ ] **Release and pin path complete:** assets `v0.6.1` tagged, v3
      `assets.yaml` + provision mirrors + engine release + v3
      `installer.pin` bumped, host re-provisioned (user-run).
- [ ] **Host 5-cycle acceptance** (user-run) passes after re-provision.
- [ ] `tickets/INDEX.md` updated in the same commit as every status change.

## Regression test

This repo has no runtime/VM harness, so the **behavioral regression test is the
VM matrix** (case C, ideally D) run on the fix commit, followed by the host
5-cycle acceptance above. Re-running the `repro:` command must return to the
greeter, not a black VT.

The **static guard** executed on the fix commit (and repeatable at review
time):

```sh
test "$(sed -n '15p' configs/wlogout/layout)" = '    "action" : "uwsm stop",'
test "$(grep -c 'terminate-user' configs/wlogout/layout)" -eq 0
git diff --stat <base>..HEAD -- configs/wlogout/layout   # 1 file, 1 insertion, 1 deletion
```

Do not add a validator assertion or any other file to the one-line fix; the
one-line diff is the contract. If a CI-level guard on the action string is
wanted later, file it separately.

## Release and pin plan (no tag/release in this ticket)

Assets, engine, then v3 are pinned in that order. Do not bump a consumer
before the assets tag exists and its CI is green; do not bump the v3 manifest
before the new engine exists, because v3's coverage gate compares the manifest
tag against the engine mirrors.

| # | Repo | Change | Gate |
| --- | --- | --- | --- |
| 1 | `dotfiles-assets` | Apply the one-line fix; `CHANGELOG.md` `0.6.1`; PATCH tag `v0.6.1` (or the next PATCH if another change lands first) | `make validate-configs`, `make gates`, `make gates-ci`, `make ci-gates-parity`; CI on the tag |
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

## Next-session starting points (self-contained)

1. **Read:** this ticket; [attribution.md](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md);
   [vm-matrix.md](https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md).
   Root cause is attributed; the remaining unknown is the VM behavior of
   `uwsm stop` (and `hyprctl dispatch exit`), not the mechanism.
2. **Ask the user to approve** the wlogout Logout action change. Do not edit
   anything before that.
3. **Run the VM matrix** exactly as vm-matrix §0–§3 (user-run; sudo + Incus).
   Switch the VM autologin to `hyprland-uwsm.desktop` first; run cases A, B, C,
   D; capture `preflight.txt`, `sddm.log` greps, `state.txt`, and the
   session/scope journal lines; paste the results into the provision BUG-005
   ticket. Case C is the gate; D is the ideal control.
4. **If C passes (D ideally) and the user approves:** move this ticket to
   `in-progress` (same commit updates `tickets/INDEX.md`), apply the one-line
   diff on `ticket/bug-001-wlogout-logout-uwsm-stop` (worktree
   `.worktrees/bug-001/`), and run the assets gates and scope guard above.
5. **If C and D fail:** stop; do not change wlogout. Comment the matrix result
   on this ticket and escalate to the SDDM helper-exit handling (upstream PR
   #2103 / backport). The wlogout action is not the fix in that outcome.
6. **After the fix commit is merged and tagged:** execute the release/pin plan
   in order, re-provision (user-run), then run the host 5-cycle acceptance and
   the session checker. Close the ticket only when every acceptance box is
   ticked.

## References

- Provision BUG-005 attribution — <https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/attribution.md>
- Provision BUG-005 VM matrix — <https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/vm-matrix.md>
- Provision BUG-005 ticket — <https://github.com/RandomGenericUsername/dotfiles-provision/blob/main/tickets/BUG-005-sddm-logout-greeter-crash/ticket.md>
- SDDM issue #1908 — <https://github.com/sddm/sddm/issues/1908>
- SDDM PR #2103 — <https://github.com/sddm/sddm/pull/2103>
- SDDM v0.21.0 `src/auth/Auth.cpp`, `src/auth/Auth.h`, `src/daemon/Display.cpp`, `src/daemon/Seat.cpp`, `src/helper/HelperApp.cpp`, `src/helper/UserSession.cpp` — <https://github.com/sddm/sddm/tree/v0.21.0>
- systemd v262 `src/login/logind-dbus.c:4517-4521` (`SendSIGHUP`) — <https://github.com/systemd/systemd/blob/v262/src/login/logind-dbus.c>
- Qt v6.12 `src/3rdparty/forkfd/forkfd.c:252-258`, `src/corelib/io/qprocess_unix.cpp:1328-1329` — <https://github.com/qt/qtbase/tree/v6.12.0>
- This repo: `configs/wlogout/layout:1-36`, `configs/README.md:35-44`, `icons/mappings/icons.yaml:174-194`, `templates/wlogout/style.css.tpl`.
- Consumer acceptance checker: `dotfiles-v3/scripts/check-session-bounce.py`; host procedure in `dotfiles-v3/dev/README.md` (5 logins, each ≥180 s).
