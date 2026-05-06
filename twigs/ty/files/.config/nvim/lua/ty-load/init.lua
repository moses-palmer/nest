vim.lsp.config('ty', {
    capabilities = require'nvim-lspconfig-load'.capabilities(),
})
vim.lsp.enable('ty')
