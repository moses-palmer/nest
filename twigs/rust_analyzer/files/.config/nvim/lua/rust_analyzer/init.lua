require'lspconfig'.rust_analyzer.setup {
    capabilities = require'cmp_nvim_lsp'.default_capabilities()
}
vim.cmd('autocmd BufWritePre *.rs lua vim.lsp.buf.format()')
