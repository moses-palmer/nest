vim.lsp.config('rust_analyzer', {
    capabilities = require'nvim-lspconfig-load'.capabilities(),
})
vim.lsp.enable('rust_analyzer')
