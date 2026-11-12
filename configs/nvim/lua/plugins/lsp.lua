return {
  -- lua_ls is already configured by LazyVim; add bashls for shell scripts.
  { "neovim/nvim-lspconfig", opts = { servers = { bashls = {} } } },
}
