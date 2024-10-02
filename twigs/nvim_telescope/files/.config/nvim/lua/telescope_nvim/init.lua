vim.cmd('packadd! plenary.nvim')
vim.cmd('packadd! telescope.nvim')

local show_hidden = os.getenv('TMUX_PROJECT_SHOW_HIDDEN') == 'yes'
local show_vcs = os.getenv('TMUX_PROJECT_SHOW_VCS') == 'yes'
local vimgrep_arguments = {
    'rg',
    '--color=never',
    '--no-heading',
    '--with-filename',
    '--line-number',
    '--column',
    '--smart-case',
    '--glob=!.git/*',
    (show_hidden and {'--hidden'} or {'--no-hidden'})[1],
    (show_vcs and {'--no-ignore-vcs'} or {'--ignore-vcs'})[1],
}

require'telescope'.setup {
    defaults = {
        vimgrep_arguments = vimgrep_arguments,
        file_ignore_patterns = {
            '.git/*',
        },
    },
    pickers = {
        find_files = {
            hidden = show_hidden,
            no_ignore = show_vcs,
        },
    },
}

require'telescope'.load_extension('fzf')

vim.keymap.set('n', '<C-p>', require'telescope.builtin'.find_files)
vim.keymap.set('n', '<C-k>', function()
    require'telescope.builtin'.grep_string {
        search = '',
        only_sort_text = false,
    }
end)
vim.keymap.set('n', '<leader><C-k>', require'telescope.builtin'.live_grep)
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
