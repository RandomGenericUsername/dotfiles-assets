-- End-to-end apply verification: read the JSON through stdpath("config"),
-- overlay the chrome groups, and compare Neovim's own highlight table.
-- Run with an isolated XDG_CONFIG_HOME through ../verify.sh.
local function fail(message)
  io.stderr:write("FAIL: " .. message .. "\n")
  vim.cmd("cquit 1")
end

local root = vim.env.NVIM_APPEARANCE_FIXTURES
  or (vim.fn.getcwd() .. "/tests/fixtures/nvim-appearance")
local expected = vim.json.decode(
  table.concat(vim.fn.readfile(root .. "/expected-chrome.json"), "\n")
).glass

-- Same palette role source the generated projection exposes.
package.loaded["dotfiles-palette"] = {
  palette = vim.json.decode(table.concat(vim.fn.readfile(root .. "/palette.roles.json"), "\n")),
}

local appearance = require("dotfiles-appearance")
if appearance.load() ~= true then
  fail("load() did not find stdpath('config')/lua/dotfiles-appearance.json")
end
if appearance.apply() ~= true then
  fail("apply() returned false")
end

local function hex(value)
  if value == nil then
    return nil
  end
  return string.format("#%06x", value)
end

local function group(name)
  return vim.api.nvim_get_hl(0, { name = name })
end

if hex(group("Normal").bg) ~= expected.normal_bg then
  fail("Normal.bg " .. tostring(hex(group("Normal").bg)) .. " ~= " .. expected.normal_bg)
end
if hex(group("NormalFloat").bg) ~= expected.float_bg then
  fail("NormalFloat.bg " .. tostring(hex(group("NormalFloat").bg)) .. " ~= " .. expected.float_bg)
end
if hex(group("FloatBorder").fg) ~= expected.float_border then
  fail("FloatBorder.fg " .. tostring(hex(group("FloatBorder").fg)) .. " ~= " .. expected.float_border)
end
if hex(group("StatusLine").bg) ~= expected.statusline_bg then
  fail("StatusLine.bg " .. tostring(hex(group("StatusLine").bg)) .. " ~= " .. expected.statusline_bg)
end
if hex(group("Visual").bg) ~= expected.visual_bg or hex(group("Visual").fg) ~= expected.visual_fg then
  fail("Visual fg/bg do not match " .. expected.visual_bg .. "/" .. expected.visual_fg)
end
if vim.o.winborder ~= expected.winborder then
  fail("winborder " .. tostring(vim.o.winborder) .. " ~= " .. expected.winborder)
end

print(string.format("apply        -> Normal=%s NormalFloat=%s StatusLine=%s Visual=%s winborder=%s",
  hex(group("Normal").bg), hex(group("NormalFloat").bg), hex(group("StatusLine").bg),
  hex(group("Visual").bg), vim.o.winborder))
print("APPLY VERIFICATION PASSED")
