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
    backend = { 'snacks' },
    snacks = {
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


local open_floating_preview = vim.lsp.util.open_floating_preview
vim.api.nvim_create_autocmd('LspAttach', {
    callback = function(args)
        local actions_preview = require'actions-preview'
        local snacks = require'snacks'
        local options = { buffer = args.buf }

        split_id = nil
        local split = function(callback)
            return function(...)
                if split_id ~= nil and vim.api.nvim_win_is_valid(split_id) then
                    vim.api.nvim_win_close(split_id, true)
                end
                split_id = vim.api.nvim_open_win(0, true, {
                    split = 'right',
                })
                callback(...)
            end
        end
        local no_float = function(callback)
            return function(...)
                vim.lsp.util.open_floating_preview = function(c, s, opts)
                    local buf = vim.api.nvim_create_buf(false, true)
                    vim.api.nvim_set_current_buf(buf)
                    vim.api.nvim_buf_set_lines(buf, 0, -1, false, c)
                    vim.opt.filetype = s
                    vim.opt_local.bufhidden = 'wipe'
                    vim.opt_local.conceallevel = 3
                    vim.opt_local.concealcursor = 'nvic'
                    vim.opt_local.modifiable = false
                    vim.keymap.set('n', '<esc>',
                        function()
                            vim.api.nvim_win_close(0, true)
                        end, {
                        buffer = true,
                    })

                    vim.lsp.util.open_floating_preview = open_floating_preview
                end
                callback(...)
            end
        end

        vim.keymap.set('n', 'ga', actions_preview.code_actions, options)
        vim.keymap.set('n', 'gA', vim.lsp.codelens.run, options)
        vim.keymap.set('n', 'rr', vim.lsp.buf.rename, options)

        vim.keymap.set('n', 'gd', snacks.picker.lsp_definitions, options)
        vim.keymap.set('n', 'gD', split(vim.lsp.buf.definition), options)

        -- Allow mouse navigation; make sure to press the left button to change
        -- cursor position before going to definition
        vim.keymap.set(
            'n', '<C-LeftMouse>',
            '<LeftMouse>:lua vim.lsp.buf.definition()<CR>', options)

        vim.keymap.set('n', 'gi', snacks.picker.lsp_implementations, options)

        vim.keymap.set('n', 'gt', vim.lsp.buf.type_definition, options)
        vim.keymap.set('n', 'gT', split(vim.lsp.buf.type_definition), options)

        vim.keymap.set('n', 'gh', snacks.picker.lsp_incoming_calls, options)
        vim.keymap.set('n', 'gH', snacks.picker.lsp_outgoing_calls, options)
        vim.keymap.set('n', 'gr', snacks.picker.lsp_references, options)

        vim.keymap.set('n', 'gs', snacks.picker.lsp_symbols, options)
        vim.keymap.set('n', 'gS', snacks.picker.lsp_workspace_symbols, options)

        vim.keymap.set('n', 'K', vim.lsp.buf.hover, options)
        vim.keymap.set('n', 'gK', split(no_float(vim.lsp.buf.hover)), options)

        vim.keymap.set('n', 'ge', snacks.picker.diagnostics_buffer, options)
        vim.keymap.set('n', 'gE', snacks.picker.diagnostics, options)
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
