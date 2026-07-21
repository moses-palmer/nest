vim.cmd('packadd! jdtls')
vim.lsp.config('jdtls', {
    capabilities = require'nvim-lspconfig-load'.capabilities(),
    settings = {
        java = {
            inlayHints = {
                formatParameters = {
                    emabled = true,
                },
            },
        },
    },
})
