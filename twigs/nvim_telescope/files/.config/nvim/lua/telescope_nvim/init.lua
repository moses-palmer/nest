vim.cmd('packadd! plenary.nvim')
vim.cmd('packadd! telescope.nvim')

local hidden = os.getenv('TMUX_PROJECT_SHOW_HIDDEN') == 'yes'
local no_ignore = os.getenv('TMUX_PROJECT_SHOW_VCS') == 'yes'
local vimgrep_arguments = {
    'rg',
    '--color=never',
    '--no-heading',
    '--with-filename',
    '--line-number',
    '--column',
    '--smart-case',
}
if hidden then
    table.insert(vimgrep_arguments, '--hidden')
end
if no_ignore then
    table.insert(vimgrep_arguments, '--no-ignore')
end

require'telescope'.setup {
    defaults = {
        vimgrep_arguments = vimgrep_arguments,
    },
    pickers = {
        find_files = {
            hidden = hidden,
            no_ignore = no_ignore,
        },
    },
}

require'telescope'.load_extension('fzf')
local telescope_builtin = require'telescope.builtin'

vim.keymap.set('n', '<F1>', telescope_builtin.help_tags)
vim.keymap.set('n', '<C-p>', telescope_builtin.find_files)
vim.keymap.set('n', '<C-k>', function()
    telescope_builtin.grep_string({
        search = '',
        only_sort_text = false,
    })
end)

vim.keymap.set('n', '<leader><C-k>', telescope_builtin.live_grep)
vim.keymap.set('n', '<leader><C-p>', function()
    local config = require'telescope.config'.values
    local finders = require'telescope.finders'
    local pickers = require'telescope.pickers'
    pickers.new({}, {
        prompt_title = 'Modified files',
        finder = finders.new_oneshot_job(
            { 'git', 'diff', '--name-only' },
            opts
        ),
        previewer = config.file_previewer({}),
        sorter = config.file_sorter({}),
    })
    :find()
end)
