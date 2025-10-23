vim.lsp.config('ts_ls', {
    capabilities = require'cmp_nvim_lsp'.default_capabilities()
})
vim.lsp.enable('ts_ls')
