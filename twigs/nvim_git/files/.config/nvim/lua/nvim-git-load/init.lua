vim.cmd('packadd! vim-fugitive')
vim.cmd('packadd! vim-gitgutter')

vim.api.nvim_create_user_command('Log', 'Git log --patch --decorate %', {})
vim.keymap.set('n', 'hk', '<Plug>(GitGutterPrevHunk)')
vim.keymap.set('n', 'hj', '<Plug>(GitGutterNextHunk)')
vim.keymap.set('n', '<leader>s', '<Plug>(GitGutterStageHunk)')
