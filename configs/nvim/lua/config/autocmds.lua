-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- Live palette + appearance reload (dotfiles-v3 REQ-123/REQ-124). The
-- runtime/provisioning seed republishes lua/dotfiles-palette.lua and
-- lua/dotfiles-appearance.json; a SIGUSR1 or :DotfilesColorsReload then drops
-- the cached modules and reloads both. Appearance is applied after the palette
-- so chrome overrides win; a missing or malformed appearance document is a
-- safe no-op (palette-only). No polling timer: the signal is the trigger.
local function reload_palette()
  package.loaded["dotfiles-palette"] = nil
  local palette_ok, palette = pcall(require, "dotfiles-palette")
  palette_ok = palette_ok and type(palette.load) == "function"
  local applied = false
  if palette_ok then
    palette.load()
    applied = true
  end

  package.loaded["dotfiles-appearance"] = nil
  local appearance_ok, appearance = pcall(require, "dotfiles-appearance")
  appearance_ok = appearance_ok and type(appearance.apply) == "function"
  if appearance_ok and appearance.apply() then
    applied = true
  end

  -- Fresh host before the first runtime seed: nothing to reload.
  if not applied then
    return
  end

  vim.api.nvim_exec_autocmds("ColorScheme", { pattern = "dotfiles" })
  vim.cmd.redraw()
end

vim.api.nvim_create_autocmd("Signal", {
  pattern = "SIGUSR1",
  callback = reload_palette,
  desc = "Reload the generated dotfiles palette and appearance",
})

vim.api.nvim_create_user_command("DotfilesColorsReload", reload_palette, {
  desc = "Reload the generated dotfiles palette and appearance",
})
