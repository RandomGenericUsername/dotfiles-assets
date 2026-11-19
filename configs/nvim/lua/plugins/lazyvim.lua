return {
  -- Generated palette (dotfiles-v3 REQ-123). The runtime/provisioning seed
  -- publishes lua/dotfiles-palette.lua; fall back to Catppuccin when the
  -- pointer is absent (fresh host before the first runtime seed).
  { "LazyVim/LazyVim", opts = {
    colorscheme = function()
      local ok, palette = pcall(require, "dotfiles-palette")
      if ok and type(palette.load) == "function" then
        palette.load()
      else
        vim.cmd.colorscheme("catppuccin")
      end
    end,
  } },
}
