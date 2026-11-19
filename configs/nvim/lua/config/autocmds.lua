-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- Live palette reload (dotfiles-v3 REQ-123 follow-up). The runtime/provisioning
-- seed republishes lua/dotfiles-palette.lua; a SIGUSR1 or :DotfilesColorsReload
-- then drops the cached module and reloads it. No polling timer: the signal is
-- the trigger.
local function reload_palette()
  package.loaded["dotfiles-palette"] = nil
  local ok, palette = pcall(require, "dotfiles-palette")
  if not ok or type(palette.load) ~= "function" then
    -- Fresh host before the first runtime seed: nothing to reload.
    return
  end
  palette.load()
  vim.api.nvim_exec_autocmds("ColorScheme", { pattern = "dotfiles" })
  vim.cmd.redraw()
end

vim.api.nvim_create_autocmd("Signal", {
  pattern = "SIGUSR1",
  callback = reload_palette,
  desc = "Reload the generated dotfiles palette",
})

vim.api.nvim_create_user_command("DotfilesColorsReload", reload_palette, {
  desc = "Reload the generated dotfiles palette",
})
