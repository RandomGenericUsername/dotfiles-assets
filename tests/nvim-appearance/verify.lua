-- Headless resolver verification for dotfiles-appearance (dotfiles-v3 REQ-124 §6.2).
-- No UI, no user config: run through ../verify.sh.
local failures = 0

local function fail(message)
  failures = failures + 1
  io.stderr:write("FAIL: " .. message .. "\n")
end

local function check(name, actual, expected)
  if expected == vim.NIL then
    expected = nil
  end
  if actual ~= expected then
    fail(string.format("%s: expected %s, got %s", name, vim.inspect(expected), vim.inspect(actual)))
  end
end

local function read_json(path)
  return vim.json.decode(table.concat(vim.fn.readfile(path), "\n"))
end

local root = vim.env.NVIM_APPEARANCE_FIXTURES
  or (vim.fn.getcwd() .. "/tests/fixtures/nvim-appearance")
local appearance = require("dotfiles-appearance")
local roles = read_json(root .. "/palette.roles.json")
local expected = read_json(root .. "/expected-chrome.json")

local fields = {
  "normal_bg",
  "float_bg",
  "statusline_bg",
  "float_border",
  "window_border",
  "separator",
  "visual_bg",
  "visual_fg",
  "winborder",
  "statusline_bold",
}

for _, skin in ipairs({ "glass", "flat", "terminal" }) do
  local tokens = read_json(root .. "/" .. skin .. ".tokens.json")
  local chrome = appearance.resolve(tokens, roles)
  local want = expected[skin]
  for _, field in ipairs(fields) do
    check(skin .. "." .. field, chrome[field], want[field])
  end
  for field, path in pairs(want.provenance) do
    check(skin .. ".provenance." .. field, chrome.provenance[field], path)
  end
  if next(chrome.degraded) ~= nil then
    fail(skin .. ": unexpected degradation " .. vim.inspect(chrome.degraded))
  end
  print(string.format("resolve %-8s normal=%s float=%s statusline=%s winborder=%s",
    skin, chrome.normal_bg, chrome.float_bg, chrome.statusline_bg, chrome.winborder))
end

-- One bad token keeps the affected group palette-owned; it must not discard
-- the whole skin (§4.3).
do
  local tokens = read_json(root .. "/glass.tokens.json")
  local baseline = appearance.resolve(tokens, roles)
  tokens.surface.card.bg = "linear-gradient(red, blue)"
  local chrome = appearance.resolve(tokens, roles)
  check("bad-token.normal_bg", chrome.normal_bg, baseline.normal_bg)
  check("bad-token.float_bg", chrome.float_bg, baseline.normal_bg)
  if not chrome.degraded["surface.card.bg"] then
    fail("bad-token: surface.card.bg was not recorded as degraded")
  end
  print("bad token    -> float_bg falls back to Normal, normal_bg preserved")
end

-- Missing full role map: the documented surface alias is used and recorded,
-- never guessed.
do
  local tokens = read_json(root .. "/glass.tokens.json")
  local partial = vim.deepcopy(roles)
  partial.surface_container_lowest = nil
  tokens.surface.card.bg = "@surface_container_lowest"
  local chrome = appearance.resolve(tokens, partial)
  check("role-alias.float_bg", chrome.float_bg, partial.surface_container_low)
  if not chrome.degraded["surface.card.bg"] then
    fail("role-alias: surface_container_lowest fallback was not recorded")
  end
  print("role alias   -> surface_container_lowest -> surface_container_low")
end

-- Missing pointer: false, never an error.
check("missing.load", appearance.load("/nonexistent/dotfiles-appearance.json"), false)

-- Malformed / wrong-version / missing-window documents: false, never an error.
local function rejects(name, body)
  local path = vim.fn.tempname()
  vim.fn.writefile({ body }, path)
  local ok, result = pcall(appearance.load, path)
  os.remove(path)
  if not ok then
    fail(name .. ": load raised " .. tostring(result))
  elseif result ~= false then
    fail(name .. ": load did not return false")
  end
end

rejects("malformed", '{"version": 2,')
rejects("wrong-version", '{"version": 3}')
rejects("missing-window", '{"version": 2, "surface": {}}')
print("fallbacks    -> missing/malformed/wrong-version/missing-window all return false")

if failures > 0 then
  vim.cmd("cquit 1")
end
print("RESOLVER VERIFICATION PASSED")
