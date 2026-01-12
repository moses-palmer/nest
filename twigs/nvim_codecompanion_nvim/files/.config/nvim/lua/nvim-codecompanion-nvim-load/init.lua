vim.cmd('packadd! codecompanion.nvim')


require'codecompanion'.setup {
    display = {
        chat = {
            window = {
                position = 'right',
            },
        },
    },
    interactions = {
        background = {
            adapter = {
                name = vim.g.codecompanion_adapter_name,
                model = vim.g.codecompanion_adapter_model,
            },
        },
        chat = {
            adapter = vim.g.codecompanion_adapter_name,
        },
    },
}

vim.keymap.set('n', '<F2>', ':CodeCompanionActions<CR>')
