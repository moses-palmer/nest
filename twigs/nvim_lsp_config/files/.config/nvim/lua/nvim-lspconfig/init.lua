vim.cmd('packadd! nvim-cmp')
vim.cmd('packadd! cmp-nvim-lsp')
vim.cmd('packadd! vim-vsnip')
vim.cmd('packadd! cmp-vsnip')
vim.cmd('packadd! actions-preview.nvim')
vim.cmd('packadd! nvim-lspconfig')


require'actions-preview'.setup {
    diff = {
        ctxlen = 3,
    },
    highlight_command = {
        require('actions-preview.highlight').delta(),
    },
    backend = { 'telescope' },
    telescope = {
        sorting_strategy = 'ascending',
        layout_strategy = 'vertical',
        layout_config = {
            width = 0.8,
            height = 0.9,
            prompt_position = 'top',
            preview_cutoff = 20,
            preview_height = function(_, _, max_lines)
                return max_lines - 15
            end,
        },
    },
}


local cmp = require'cmp'
cmp.setup {
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
}


vim.api.nvim_create_autocmd('LspAttach', {
    callback = function(args)
        local actions_preview = require'actions-preview'
        local telescope = require'telescope.builtin'
        local options = { buffer = args.buf }
        local split = function(callback)
            return function(...)
                vim.cmd('vsplit')
                callback(...)
                vim.cmd('wincmd L')
            end
        end

        vim.keymap.set('n', 'ga', actions_preview.code_actions, options)
        vim.keymap.set('n', 'gA', vim.lsp.codelens.run, options)
        vim.keymap.set('n', 'rr', vim.lsp.buf.rename, options)

        vim.keymap.set('n', 'gd', vim.lsp.buf.definition, options)
        vim.keymap.set('n', 'gD', split(vim.lsp.buf.definition), options)

        -- Allow mouse navigation; make sure to press the left button to change
        -- cursor position before going to definition
        vim.keymap.set(
            'n', '<C-LeftMouse>',
            '<LeftMouse>:lua vim.lsp.buf.definition()<CR>', options)

        vim.keymap.set( 'n', 'gi', telescope.lsp_implementations, options)

        vim.keymap.set('n', 'gt', vim.lsp.buf.type_definition, options)
        vim.keymap.set('n', 'gT', split(vim.lsp.buf.type_definition), options)

        vim.keymap.set('n', 'gh', telescope.lsp_incoming_calls, options)
        vim.keymap.set('n', 'gH', telescope.lsp_outgoing_calls, options)
        vim.keymap.set('n', 'gr', telescope.lsp_references, options)

        vim.keymap.set('n', 'gs', telescope.lsp_document_symbols, options)
        vim.keymap.set('n', 'gS', telescope.lsp_workspace_symbols, options)

        vim.keymap.set('n', 'K', vim.lsp.buf.hover, options)

        vim.keymap.set('n', 'ge', function()
            telescope.diagnostics {
                bufnr = 0,
                no_sign = true,
            }
        end, options)
        vim.keymap.set('n', 'gE', function()
            telescope.diagnostics {
                bufnr = nil,
                no_sign = true,
            }
        end, options)
        vim.keymap.set('n', '<M-K>', vim.diagnostic.open_float, options)
        vim.keymap.set('n', '<M-Down>', vim.diagnostic.goto_next, options)
        vim.keymap.set('n', '<M-Up>', vim.diagnostic.goto_prev, options)
    end
})


vim.diagnostic.config {
    signs = {
        text = {
            [vim.diagnostic.severity.ERROR] = '■',
            [vim.diagnostic.severity.WARN] = '■',
            [vim.diagnostic.severity.INFO] = '■',
        }
    }
}
