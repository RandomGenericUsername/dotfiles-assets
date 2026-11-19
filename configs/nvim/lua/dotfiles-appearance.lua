-- dotfiles-appearance — editor chrome from the generated Appearance tokens.
--
-- The runtime/provisioning seed publishes the active generation's resolved
-- appearance document as lua/dotfiles-appearance.json (a stable link to
-- current/appearance/tokens.json). This module reads that JSON by module
-- relative path, resolves the documented paint forms against the generated
-- palette role map, and overlays editor chrome on top of the REQ-123 palette.
--
-- Ownership split (dotfiles-v3 REQ-124 §5.1):
--   * syntax / LSP / diagnostics / diff / terminal colours stay palette-owned;
--   * window, float, statusline, tabline, separator and selection paint live
--     here.
--
-- Fallback order (§4.3): missing or malformed JSON -> palette only; an unknown
-- token expression -> keep the palette value for the affected group only. No
-- absolute host path is stored in this file; stdpath("config") is resolved at
-- runtime.

local M = {}

-- Surface-role fallbacks for a palette projection that predates M.roles
-- (theme-producer REQ-028). They are documented degradations, never guesses:
-- the alias is recorded in `degraded` so a caller can see what happened.
local ROLE_FALLBACKS = {
  surface_container_lowest = "surface_container_low",
  surface_container_highest = "surface_container_high",
  surface_dim = "surface",
  surface_bright = "surface",
  on_background = "on_surface",
}

local HEX = "^#%x%x%x%x%x%x$"

local function is_hex(value)
  return type(value) == "string" and value:match(HEX) ~= nil
end

local function to_rgb(hex)
  return tonumber(hex:sub(2, 3), 16),
    tonumber(hex:sub(4, 5), 16),
    tonumber(hex:sub(6, 7), 16)
end

-- sRGB integer composite: alpha over an opaque background. This is the
-- documented flattening of `alpha(@role, n)` for a terminal highlight — it is
-- not real transparency (§5.3).
local function composite(fg, alpha, bg)
  local fr, fg_g, fb = to_rgb(fg)
  local br, bg_g, bb = to_rgb(bg)
  local function mix(f, b)
    return math.floor(f * alpha + b * (1 - alpha) + 0.5)
  end
  return string.format("#%02x%02x%02x", mix(fr, br), mix(fg_g, bg_g), mix(fb, bb))
end

local function role(roles, name, degraded, path)
  local value = roles[name]
  if is_hex(value) then
    return value
  end
  local alias = ROLE_FALLBACKS[name]
  if alias and is_hex(roles[alias]) then
    degraded[path] = string.format("role %s -> %s", name, alias)
    return roles[alias]
  end
  degraded[path] = string.format("unknown role %s", name)
  return nil
end

-- Resolve one documented paint form:
--   @role | alpha(@role, n) | transparent | none | absent
-- Returns a hex string, the sentinel "transparent", or nil for absent /
-- unknown. `over` is the resolved background this paint is flattened over.
local function paint(expression, roles, over, degraded, path)
  if expression == nil or expression == "none" then
    return nil
  end
  if expression == "transparent" then
    return "transparent"
  end
  if type(expression) ~= "string" then
    degraded[path] = "non-string paint"
    return nil
  end

  local bare = expression:match("^@([%w_]+)$")
  if bare then
    return role(roles, bare, degraded, path)
  end

  local alpha_role, alpha_value = expression:match("^alpha%(%s*@([%w_]+)%s*,%s*([%d%.]+)%s*%)$")
  if alpha_role then
    local alpha = tonumber(alpha_value)
    if not alpha or alpha < 0 or alpha > 1 then
      degraded[path] = "alpha outside [0,1]"
      return nil
    end
    local foreground = role(roles, alpha_role, degraded, path)
    if not foreground then
      return nil
    end
    if not is_hex(over) then
      degraded[path] = "alpha has no opaque parent background"
      return nil
    end
    return composite(foreground, alpha, over)
  end

  degraded[path] = string.format("unknown expression %q", expression)
  return nil
end

local function number_at(tokens, group, key)
  local bucket = type(tokens[group]) == "table" and tokens[group] or nil
  local value = bucket and bucket[key]
  if type(value) == "number" then
    return value
  end
  return nil
end

local function string_at(tokens, group, key)
  local bucket = type(tokens[group]) == "table" and tokens[group] or nil
  return bucket and bucket[key] or nil
end

-- Pure resolver, exported for headless fixture tests. It never touches the
-- editor: given a tokens document and a flat role -> hex map it returns the
-- chrome values plus a provenance/degradation record.
function M.resolve(tokens, roles)
  tokens = type(tokens) == "table" and tokens or {}
  local chrome = {
    provenance = {},
    degraded = {},
  }
  local degraded = chrome.degraded
  local provenance = chrome.provenance
  roles = roles or {}

  local function note(field, path)
    provenance[field] = path
  end

  local palette_bg = role(roles, "background", degraded, "palette.background")

  local window = type(tokens.surface) == "table" and tokens.surface.window or nil

  -- Normal: window paint. `transparent` keeps the palette background.
  local window_bg = window and window.bg
  local normal_bg = paint(window_bg, roles, palette_bg, degraded, "surface.window.bg")
  if normal_bg == "transparent" or normal_bg == nil then
    normal_bg = palette_bg
  end
  chrome.normal_bg = normal_bg
  note("normal_bg", "surface.window.bg")

  -- Floats/cards sit over Normal. `transparent` means no separation.
  local card = type(tokens.surface) == "table" and tokens.surface.card or nil
  local card_bg = card and card.bg
  local float_bg = paint(card_bg, roles, normal_bg, degraded, "surface.card.bg")
  if float_bg == "transparent" or float_bg == nil then
    float_bg = normal_bg
  end
  chrome.float_bg = float_bg
  note("float_bg", "surface.card.bg")

  -- Statusline/tabline panel paint also sits over Normal.
  local panel = type(tokens.surface) == "table" and tokens.surface.panel or nil
  local panel_bg = panel and panel.bg
  local statusline_bg = paint(panel_bg, roles, normal_bg, degraded, "surface.panel.bg")
  if statusline_bg == "transparent" or statusline_bg == nil then
    statusline_bg = normal_bg
  end
  chrome.statusline_bg = statusline_bg
  note("statusline_bg", "surface.panel.bg")

  -- Borders: transparent/none or width 0 means "no border", which becomes an
  -- invisible FloatBorder and winborder = none.
  local card_border_width = card and card["border-width"] or nil
  local window_border_width = window and window["border-width"] or nil

  local function border_color(group, bg, path)
    if type(group) ~= "table" then
      return nil
    end
    if type(group["border-width"]) == "number" and group["border-width"] <= 0 then
      return nil
    end
    local value = paint(group.border, roles, bg, degraded, path)
    if value == "transparent" then
      return nil
    end
    return value
  end

  chrome.float_border = border_color(card, float_bg, "surface.card.border")
  note("float_border", "surface.card.border")
  chrome.window_border = border_color(window, normal_bg, "surface.window.border")
  note("window_border", "surface.window.border")

  local dim = paint(string_at(tokens, "ink", "ink-dim") or string_at(tokens, "ink", "ink_dim"),
    roles, normal_bg, degraded, "ink.ink-dim")
  local ink = paint(string_at(tokens, "ink", "ink"), roles, normal_bg, degraded, "ink.ink")
  local accent = paint(string_at(tokens, "ink", "accent"), roles, normal_bg, degraded, "ink.accent")

  chrome.ink = ink
  chrome.dim = dim
  chrome.accent = accent
  note("ink", "ink.ink")
  note("dim", "ink.ink-dim")
  note("accent", "ink.accent")

  local selected = type(tokens.state) == "table" and tokens.state.selected or nil
  local hover = type(tokens.state) == "table" and tokens.state.hover or nil

  chrome.selected_fill = paint(selected and selected.fill, roles, normal_bg, degraded, "state.selected.fill")
  chrome.selected_ink = paint(selected and selected.ink, roles, normal_bg, degraded, "state.selected.ink")
  chrome.hover_fill = paint(hover and hover.fill, roles, normal_bg, degraded, "state.hover.fill")
  note("selected_fill", "state.selected.fill")
  note("selected_ink", "state.selected.ink")
  note("hover_fill", "state.hover.fill")

  -- Chrome foregrounds. Missing state paint keeps the palette value by leaving
  -- the field nil; FloatTitle falls back to ink.accent per §5.2.
  chrome.visual_bg = chrome.selected_fill
  chrome.visual_fg = chrome.selected_ink
  chrome.pmenu_sel_bg = chrome.selected_fill
  chrome.pmenu_sel_fg = chrome.selected_ink
  chrome.tabline_sel_bg = chrome.selected_fill
  chrome.tabline_sel_fg = chrome.selected_ink
  chrome.cursorline_bg = chrome.hover_fill
  chrome.colorcolumn_bg = chrome.hover_fill

  chrome.statusline_fg = ink
  chrome.statusline_nc_fg = dim
  chrome.tabline_fg = dim
  chrome.tabline_fill = normal_bg
  chrome.pmenu_bg = float_bg
  chrome.pmenu_thumb = dim
  chrome.cursorline_nr = accent
  chrome.linenr = dim
  chrome.signcolumn_bg = normal_bg
  chrome.folded_bg = float_bg
  chrome.folded_fg = dim
  chrome.float_title_bg = chrome.selected_fill
  chrome.float_title_fg = chrome.selected_ink or accent

  -- Separators use the card border, falling back to dim ink when the skin has
  -- no border (width 0 or transparent). §5.2.
  chrome.separator = chrome.float_border or dim
  note("separator", "surface.card.border")

  -- Radius/padding/opacity/shadow/blur have no terminal-editor equivalent and
  -- are deliberately ignored (§5.4). Only border presence maps to 'winborder'.
  local effective_border_width = window_border_width
  if type(effective_border_width) ~= "number" then
    effective_border_width = card_border_width
  end
  if type(effective_border_width) == "number" then
    chrome.winborder = effective_border_width > 0 and "single" or "none"
    note("winborder", "surface.window.border-width")
  else
    chrome.winborder = nil
  end

  local weight = number_at(tokens, "type", "font-weight")
  chrome.statusline_bold = weight ~= nil and weight >= 600
  chrome.font_weight = weight
  note("statusline_bold", "type.font-weight")

  return chrome
end

function M.path()
  return vim.fn.stdpath("config") .. "/lua/dotfiles-appearance.json"
end

-- Read and validate the appearance document. Returns true when a state was
-- stored, false (never an error) when the pointer is absent, the JSON is
-- malformed, the version is not 2, surface.window is missing, or the palette
-- role source is unavailable. An optional path argument exists for headless
-- verification; production callers omit it.
function M.load(path)
  M.state = nil
  local file = path or M.path()
  local ok, handle = pcall(io.open, file, "r")
  if not ok or not handle then
    return false
  end
  local read_ok, content = pcall(handle.read, handle, "*a")
  handle:close()
  if not read_ok or type(content) ~= "string" or content == "" then
    return false
  end

  local decoded, tokens = pcall(vim.json.decode, content)
  if not decoded or type(tokens) ~= "table" then
    return false
  end
  if tokens.version ~= 2 then
    return false
  end
  if type(tokens.surface) ~= "table" or type(tokens.surface.window) ~= "table" then
    return false
  end

  local palette_ok, palette = pcall(require, "dotfiles-palette")
  if not palette_ok or type(palette) ~= "table" then
    return false
  end
  local roles = palette.roles or palette.palette
  if type(roles) ~= "table" then
    return false
  end

  M.state = {
    tokens = tokens,
    chrome = M.resolve(tokens, roles),
  }
  return true
end

local function set(group, attrs)
  vim.api.nvim_set_hl(0, group, attrs)
end

-- Overlay chrome groups. Called after palette.load() so these values win.
-- Returns true when the overlay ran, false when no valid appearance is loaded.
function M.apply()
  if not M.state then
    if not M.load() then
      return false
    end
  end

  local c = M.state.chrome
  local no_border = c.float_bg

  if c.normal_bg then
    set("Normal", { bg = c.normal_bg })
  end
  if c.float_bg then
    set("NormalFloat", { bg = c.float_bg })
    set("FloatBorder", { fg = c.float_border or no_border, bg = c.float_bg })
    set("FloatTitle", { fg = c.float_title_fg, bg = c.float_title_bg })
    set("Folded", { fg = c.folded_fg, bg = c.folded_bg })
  end
  if c.pmenu_bg then
    set("Pmenu", { fg = c.ink, bg = c.pmenu_bg })
    set("PmenuSel", { fg = c.pmenu_sel_fg, bg = c.pmenu_sel_bg })
    set("PmenuThumb", { bg = c.pmenu_thumb })
  end
  if c.statusline_bg then
    set("StatusLine", { fg = c.statusline_fg, bg = c.statusline_bg, bold = c.statusline_bold })
    set("StatusLineNC", { fg = c.statusline_nc_fg, bg = c.statusline_bg })
    set("StatusLineTerm", { fg = c.statusline_fg, bg = c.statusline_bg, bold = c.statusline_bold })
  end
  if c.tabline_fg or c.tabline_fill then
    set("TabLine", { fg = c.tabline_fg, bg = c.float_bg })
    set("TabLineSel", { fg = c.tabline_sel_fg, bg = c.tabline_sel_bg })
    set("TabLineFill", { bg = c.tabline_fill })
  end
  if c.separator then
    set("WinSeparator", { fg = c.separator })
    set("VertSplit", { fg = c.separator })
  end
  if c.visual_bg then
    set("Visual", { fg = c.visual_fg, bg = c.visual_bg })
  end
  if c.cursorline_bg then
    set("CursorLine", { bg = c.cursorline_bg })
  end
  if c.colorcolumn_bg then
    set("ColorColumn", { bg = c.colorcolumn_bg })
  end
  if c.cursorline_nr then
    set("CursorLineNr", { fg = c.cursorline_nr })
  end
  if c.linenr then
    set("LineNr", { fg = c.linenr })
  end
  if c.signcolumn_bg then
    set("SignColumn", { bg = c.signcolumn_bg })
  end
  if c.winborder and vim.fn.exists("+winborder") == 1 then
    vim.o.winborder = c.winborder
  end

  return true
end

-- Drop state and re-read the JSON; the caller is responsible for reloading the
-- palette first (autocmds.lua) so a now-missing file falls back to palette-only.
function M.reload()
  M.state = nil
  if not M.load() then
    return false
  end
  return M.apply()
end

return M
