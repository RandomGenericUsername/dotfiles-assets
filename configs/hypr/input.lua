-- Input configuration (Lua API)

hl.config({
    input = {
        kb_layout     = "us",
        follow_mouse  = 1,
        sensitivity   = 0,
        accel_profile = "flat",
        touchpad      = {
            natural_scroll = true,
            tap_to_click   = true,
        },
    },
})

local gloview_loaded = pcall(function()
    return hl.plugin.gloview.toggle
end)

if gloview_loaded then
    hl.gesture({
        fingers = 3,
        direction = "left",
        action = function()
            hl.exec_cmd("hyprctl gloviewnext")
        end,
    })

    hl.gesture({
        fingers = 3,
        direction = "right",
        action = function()
            hl.exec_cmd("hyprctl gloviewprev")
        end,
    })
else
    -- Missing/stale GloView must leave the compositor usable. Hyprland's
    -- native horizontal workspace gesture keeps three-finger left/right
    -- switching instead of dispatching unknown `gloview*` commands.
    hl.gesture({
        fingers = 3,
        direction = "horizontal",
        action = "workspace",
    })
end