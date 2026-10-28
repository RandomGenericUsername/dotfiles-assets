-- Autostart configuration (Lua API)
-- Executed once on Hyprland startup.

hl.on("hyprland.start", function()
    -- Wallpaper daemon
    hl.exec_cmd("hyprpaper")

    -- Restore persisted desktop (wallpaper/palette/icons from current.json).
    -- Without this, every login shows the static default.png from
    -- hyprpaper.conf while the runtime state remembers the last wallpaper.
    -- Waits (bounded, backgrounded) for the hyprpaper IPC socket, then runs
    -- `dotfiles-runtime reconcile`, which repoints current/ and re-fires all
    -- reloaders idempotently. Fail-open (|| true): login must never block on
    -- reconcile; output goes to the state dir for diagnosis. Wrapped in
    -- bash -lc like the staggers below (hl.exec_cmd has no shell semantics).
    hl.exec_cmd("bash -lc '(for i in $(seq 1 60); do [ -S \"$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.hyprpaper.sock\" ] && break; sleep 1; done; PATH=\"$HOME/.local/bin:$PATH\" dotfiles-runtime reconcile >>\"$HOME/.local/state/dotfiles/login-reconcile.log\" 2>&1 || true) &'")

    -- AGS (Aylur's GTK Shell) - status bar (instance `ags`)
    -- Every AGS cold start goes through the shared per-user launch lock
    -- (ags-run-locked, AD-28): AGS 3.1.0 bundles into one
    -- $XDG_RUNTIME_DIR/ags.js, so concurrent `ags run` invocations race each
    -- other and the runtime's restart lane. The wrapper takes
    -- $XDG_RUNTIME_DIR/ags-launch.lock and releases it once `--expect-instance`
    -- registers on the AGS bus — not for the process lifetime — so the
    -- staggers below still order launches without deadlocking login.
    -- ags-run-locked is provisioned into ~/.local/bin by cli_tools; the
    -- explicit path keeps startup independent of a login-shell PATH.
    hl.exec_cmd("bash -lc '$HOME/.local/bin/ags-run-locked --expect-instance ags'")

    -- AGS capture tool (standalone instance `capture`, staggered: two
    -- concurrent `ags run` invocations collide on /run/user/$UID/ags.js).
    -- Wrapped in bash -lc like gloview-activate below: hl.exec_cmd has no
    -- shell semantics (no &&, no $HOME expansion) on its own. The log dir
    -- (~/.local/state/ags) is ensured by the gui_tools role — directory
    -- setup is provisioning's responsibility, this line only starts processes.
    hl.exec_cmd("bash -lc 'sleep 2 && $HOME/.local/bin/ags-run-locked --expect-instance capture -d $HOME/.config/ags-capture --log-file $HOME/.local/state/ags/capture.log'")

    -- Notification overlay (standalone AGS instance `notifications`,
    -- staggered: concurrent `ags run` invocations collide on
    -- /run/user/$UID/ags.js). Owns org.freedesktop.Notifications for the
    -- session (replaces dunst, which stays installed as a manual fallback
    -- but is no longer autostarted). Same stagger/log discipline as the
    -- sibling instances; the log dir is ensured by the gui_tools role.
    hl.exec_cmd("bash -lc 'sleep 4 && $HOME/.local/bin/ags-run-locked --expect-instance notifications -d $HOME/.config/ags-notifications --log-file $HOME/.local/state/ags/notifications.log'")

    -- Polkit authentication agent (hyprpolkitagent)
    hl.exec_cmd("systemctl --user start hyprpolkitagent")

    -- XDG Desktop Portal (for screen sharing, file picking, etc.)
    hl.exec_cmd("systemctl --user start xdg-desktop-portal-hyprland")
    hl.exec_cmd("systemctl --user start xdg-desktop-portal-gtk")

    -- Hyprland plugins require a live IPC session.
    hl.exec_cmd("bash -lc '$HOME/.local/bin/gloview-activate'")

    -- Clipboard history is owned by the resident `dotfiles-runtime clipboard`
    -- job (systemd --user unit dotfiles-runtime-clipboard.service), which
    -- supersedes the old `cliphist` watcher lines. The overlay UI is a
    -- standalone AGS instance `clipboard` (config dir ~/.config/ags-clipboard),
    -- started below, staggered after the capture app and under the same shared
    -- launch lock as every sibling instance.
    hl.exec_cmd("bash -lc 'sleep 3 && $HOME/.local/bin/ags-run-locked --expect-instance clipboard -d $HOME/.config/ags-clipboard --log-file $HOME/.local/state/ags/clipboard.log'")
end)
