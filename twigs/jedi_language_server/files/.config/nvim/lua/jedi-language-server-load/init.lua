vim.lsp.config('jedi_language_server', {
    capabilities = require'nvim-lspconfig-load'.capabilities(),
})
vim.lsp.enable('jedi_language_server')
