vim.cmd('packadd! neo-tree.nvim')


if vim.fn.exists('g:filetree_size') == 0 then
    vim.g.filetree_size = 52
end


local show_hidden = os.getenv('TMUX_PROJECT_SHOW_HIDDEN') == 'yes'
local show_vcs = os.getenv('TMUX_PROJECT_SHOW_VCS') == 'yes'
local show_filetree = os.getenv('FILETREE_SHOW') == 'yes'
require('neo-tree').setup({
    close_if_last_window = true,
    enable_git_status = true,
    commands = {
        quickshell = function(state)
            local node = state.tree:get_node()
            if node.type == 'directory' then
                pcall(vim.fn['quickshell#open'], node.path)
            end
        end,
        system_open = function(state)
            local node = state.tree:get_node()
            vim.system({ 'g', node.path })
        end,
    },
    window = {
        width = vim.g.filetree_size,
        mappings = {
            ['<leader>s'] = 'quickshell',
            ['gx'] = 'system_open',
        },
    },
    nesting_rules = {},
    filesystem = {
        filtered_items = {
            hide_dotfiles = not show_hidden,
            hide_gitignored = not show_vcs,
            hide_by_name = {
                '.egg-info',
                '.git',
                '__pycache__',
            },
            hide_by_pattern = {
                '*.pyc',
            },
        },
        use_libuv_file_watcher = true,
    },
})

vim.keymap.set({'i', 'n'}, '<C-t>', '<Cmd>Neotree toggle<CR>')
vim.keymap.set({'i', 'n'}, '<C-h>', function()
    local filename = vim.api.nvim_buf_get_name(0)
    if vim.uv.fs_stat(filename) then
        vim.fn.execute('Neotree reveal_file=' .. filename)
    else
        vim.fn.execute('Neotree reveal')
    end
    vim.api.nvim_win_set_width(0, vim.g.filetree_size)
end)

local filetree_fits = vim.fn.winwidth(0) - vim.g.filetree_size > vim.o.textwidth
local std_in = false
vim.api.nvim_create_autocmd('StdInReadPre', {
    callback = function()
        std_in = true
    end
})
local files_passed = next(vim.fn.argv()) ~= nil
vim.api.nvim_create_autocmd('VimEnter', {
    callback = function()
        if show_filetree or (
                filetree_fits and not std_in and not files_passed) then
            vim.fn.execute('Neotree show')
        end
    end,
})
