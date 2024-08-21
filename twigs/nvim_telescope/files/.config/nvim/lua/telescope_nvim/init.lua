vim.cmd('packadd! plenary.nvim')
vim.cmd('packadd! telescope.nvim')

local hidden = false
if string.match(os.getenv('FZF_DEFAULT_COMMAND'), '[-][-]hidden') then
    hidden = true
end

require'telescope'.setup {
    pickers = {
        find_files = {
            hidden = hidden,
        },
        live_grep = {
            additional_args = {
                '--hidden',
            }
        },
    },
}

vim.keymap.set('n', '<C-p>', require'telescope.builtin'.find_files)
vim.keymap.set('n', '<C-k>', require'telescope.builtin'.live_grep)
vim.keymap.set('n', '<leader><C-p>', function()
    local conf = require('telescope.config').values
    local finders = require 'telescope.finders'
    local pickers = require 'telescope.pickers'
    pickers.new({}, {
        prompt_title = 'Modified files',
        finder = finders.new_oneshot_job(
            { 'git', 'diff', '--name-only' },
            opts
        ),
        previewer = conf.file_previewer({}),
        sorter = conf.file_sorter({}),
    })
    :find()
end)
