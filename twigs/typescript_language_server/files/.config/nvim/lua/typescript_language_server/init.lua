vim.lsp.config('ts_ls', {
    capabilities = require'nvim-lspconfig-load'.capabilities(),
})
vim.lsp.enable('ts_ls')
