vim.lsp.config('jedi_language_server', {
    capabilities = require'cmp_nvim_lsp'.default_capabilities()
})
vim.lsp.enable('jedi_language_server')
