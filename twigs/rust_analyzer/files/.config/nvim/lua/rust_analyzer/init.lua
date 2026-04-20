vim.lsp.config('rust_analyzer', {
    capabilities = require'nvim-lspconfig-load'.capabilities(),
    settings = {
        ['rust-analyzer'] = {
            cargo = {
                targetDir = 'target/.rust-analyzer',
            },
            diagnostics = {
                styleLints = {
                    enable = true,
                },
            },
            gotoImplementations = {
                filterAdjacentDerives = true,
            },
            imports = {
                merge = {
                    glob = false,
                },
            },
        },
    },
})
vim.lsp.enable('rust_analyzer')
