vim.cmd('packadd! nvim-cmp')
vim.cmd('packadd! cmp-nvim-lsp')
vim.cmd('packadd! vim-vsnip')
vim.cmd('packadd! cmp-vsnip')
vim.cmd('packadd! nvim-lspconfig')

local cmp = require'cmp'
cmp.setup({
    snippet = {
        expand = function(args)
            vim.fn['vsnip#anonymous'](args.body)
        end,
    },
    mapping = cmp.mapping.preset.insert({
        ['<C-Space>'] = cmp.mapping.complete(),
        ['<C-e>'] = cmp.mapping.abort(),
        ['<CR>'] = cmp.mapping.confirm({ select = true }),
    }),
    window = {
        completion = cmp.config.window.bordered(),
        documentation = cmp.config.window.bordered(),
    },
    sources = cmp.config.sources(
        {
            { name = 'nvim_lsp' },
            { name = 'vsnip' },
        },
        {
            { name = 'buffer' },
        })
})

vim.api.nvim_create_autocmd('LspAttach', {
    callback = function(args)
        local options = { buffer = args.buf }
        local split = function(callback)
            return function()
                vim.cmd('vsplit')
                callback()
                vim.cmd('wincmd L')
            end
        end
        vim.keymap.set('n', 'ga', vim.lsp.buf.code_action, options)
        vim.keymap.set('n', 'gA', vim.lsp.codelens.run, options)
        vim.keymap.set('n', 'rr', vim.lsp.buf.rename, options)

        vim.keymap.set('n', 'gd', vim.lsp.buf.definition, options)
        vim.keymap.set('n', 'gD', split(vim.lsp.buf.definition), options)

        -- Allow mouse navigation; make sure to press the left button to change
        -- cursor position before going to definition
        vim.keymap.set(
            'n', '<C-LeftMouse>',
            '<LeftMouse>:lua vim.lsp.buf.definition()<CR>', options)

        vim.keymap.set( 'n', 'gi', vim.lsp.buf.implementation, options)

        vim.keymap.set('n', 'gt', vim.lsp.buf.type_definition, options)
        vim.keymap.set('n', 'gT', split(vim.lsp.buf.type_definition), options)

        vim.keymap.set('n', 'gh', vim.lsp.buf.incoming_calls, options)
        vim.keymap.set('n', 'gH', vim.lsp.buf.outgoing_calls, options)
        vim.keymap.set('n', 'gr', vim.lsp.buf.references, options)

        vim.keymap.set('n', 'gs', vim.lsp.buf.document_symbol, options)

        vim.keymap.set('n', 'K', vim.lsp.buf.hover, options)

        vim.keymap.set('n', '<M-K>', vim.diagnostic.open_float, options)
        vim.keymap.set('n', '<M-Down>', vim.diagnostic.goto_next, options)
        vim.keymap.set('n', '<M-Up>', vim.diagnostic.goto_prev, options)
    end
})
