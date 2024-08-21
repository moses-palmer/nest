vim.cmd('packadd! nvim-dap')

local dap = require'dap'
local widgets = require'dap.ui.widgets'


vim.keymap.set('n', '<leader>b', dap.toggle_breakpoint)
vim.keymap.set('n', '<leader>B', dap.list_breakpoints)

vim.keymap.set('n', '<F3>', dap.repl.toggle)

vim.keymap.set('n', '<F5>', dap.continue)
vim.keymap.set('n', '<S-F5>', dap.pause)
vim.keymap.set('n', '<leader><F5>', dap.run_to_cursor)
vim.keymap.set('n', '<leader><S-F5>', dap.goto_)
vim.keymap.set('n', '<F10>', dap.disconnect)

vim.keymap.set('n', '<F7>', dap.step_into)
vim.keymap.set('n', '<S-F7>', dap.step_out)
vim.keymap.set('n', '<F8>', dap.step_over)

vim.keymap.set('n', '<leader><up>', dap.up)
vim.keymap.set('n', '<leader><down>', dap.down)
vim.keymap.set('n', '<leader>K', widgets.hover)


vim.fn.sign_define('DapBreakpoint', {
    text='🔴', texthl='', linehl='', numhl='',
})
vim.fn.sign_define('DapBreakpointCondition', {
    text='🟡', texthl='', linehl='', numhl='',
})
vim.fn.sign_define('DapBreakpointRejected', {
    text='⭕', texthl='', linehl='', numhl='',
})
vim.fn.sign_define('DapStopped', {
    text='🔷', texthl='', linehl='', numhl='',
})


if os.getenv('TMUX_PROJECT_STAGE') == 'editor' then
    local dap_rc = '.nvim-dap.lua'
    if vim.fn.filereadable(dap_rc) == 1 then
        vim.cmd('luafile ' .. dap_rc)
    end
end
