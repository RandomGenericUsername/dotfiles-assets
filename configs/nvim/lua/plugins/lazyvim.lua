return {
  -- Generated palette (dotfiles-v3 REQ-123) plus generated appearance chrome
  -- (REQ-124). The runtime/provisioning seed publishes lua/dotfiles-palette.lua
  -- and lua/dotfiles-appearance.json; fall back to Catppuccin when the palette
  -- pointer is absent (fresh host before the first runtime seed).
  { "LazyVim/LazyVim", opts = {
    colorscheme = function()
      local ok, palette = pcall(require, "dotfiles-palette")
      if ok and type(palette.load) == "function" then
        palette.load()
        -- Appearance overrides chrome only; syntax stays palette-owned. A
        -- missing or malformed appearance document is a safe no-op.
        local appearance_ok, appearance = pcall(require, "dotfiles-appearance")
        if appearance_ok and type(appearance.apply) == "function" then
          pcall(appearance.apply)
        end
      else
        vim.cmd.colorscheme("catppuccin")
      end
    end,
  } },
}
