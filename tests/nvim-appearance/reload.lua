-- Live-reload verification: the SIGUSR1 autocmd and :DotfilesColorsReload must
-- re-read the appearance JSON and re-apply chrome. Run through ../verify.sh.
local function fail(message)
  io.stderr:write("FAIL: " .. message .. "\n")
  vim.cmd("cquit 1")
end

local root = vim.env.NVIM_APPEARANCE_FIXTURES
  or (vim.fn.getcwd() .. "/tests/fixtures/nvim-appearance")
local assets = vim.env.NVIM_APPEARANCE_ASSETS or (vim.fn.getcwd() .. "/configs/nvim")
local expected = vim.json.decode(
  table.concat(vim.fn.readfile(root .. "/expected-chrome.json"), "\n")
)

package.loaded["dotfiles-palette"] = {
  load = function() end,
  palette = vim.json.decode(table.concat(vim.fn.readfile(root .. "/palette.roles.json"), "\n")),
}
dofile(assets .. "/lua/config/autocmds.lua")

local target = vim.fn.stdpath("config") .. "/lua/dotfiles-appearance.json"
local function install(skin)
  vim.fn.writefile(vim.fn.readfile(root .. "/" .. skin .. ".tokens.json"), target)
end

local function normal_bg()
  return string.format("#%06x", vim.api.nvim_get_hl(0, { name = "Normal" }).bg or 0)
end

install("glass")
vim.api.nvim_exec_autocmds("Signal", { pattern = "SIGUSR1" })
if normal_bg() ~= expected.glass.normal_bg then
  fail("SIGUSR1 did not apply glass (" .. normal_bg() .. ")")
end

install("terminal")
vim.api.nvim_exec_autocmds("Signal", { pattern = "SIGUSR1" })
if normal_bg() ~= expected.terminal.normal_bg then
  fail("SIGUSR1 did not reload terminal (" .. normal_bg() .. ")")
end

install("flat")
vim.cmd("DotfilesColorsReload")
if normal_bg() ~= expected.flat.normal_bg then
  fail(":DotfilesColorsReload did not reload flat (" .. normal_bg() .. ")")
end

print(string.format("reload       -> SIGUSR1 glass/terminal, command flat (Normal=%s)", normal_bg()))
print("RELOAD VERIFICATION PASSED")
