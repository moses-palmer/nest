vim.cmd('packadd! snacks.nvim')

local show_hidden = os.getenv('TMUX_PROJECT_SHOW_HIDDEN') == 'yes'
local show_vcs = os.getenv('TMUX_PROJECT_SHOW_VCS') == 'yes'

require'snacks'.setup {}

local snacks = require'snacks'

vim.keymap.set('n', '<F1>', snacks.picker.help)

vim.keymap.set('n', '<C-p>', function(opts, ctx)
    local opts = opts ~= nil and opts or {}
	opts.hidden = show_hidden
    opts.ignored = show_vcs
	snacks.picker.files(opts, ctx)
end)

vim.keymap.set('n', '<C-k>', function(opts, ctx)
    local opts = opts ~= nil and opts or {}
	opts.hidden = show_hidden
    opts.ignored = show_vcs
    snacks.picker.grep(opts, ctx)
end)

vim.keymap.set('n', '<leader><C-p>', function(opts, ctx)
    local so = vim.system({ 'git', 'diff', '--name-only' }, {}):wait()
    local items = {}
    for i, line in pairs(vim.split(so.stdout, '\n')) do
        if vim.uv.fs_stat(line) ~= nil then
            table.insert(items, {
                idx = i,
                score = i,
                text = line,
                file = line,
            })
        end
    end
    snacks.picker {
        items = items,
        title = 'Modified files',
    }
end)
