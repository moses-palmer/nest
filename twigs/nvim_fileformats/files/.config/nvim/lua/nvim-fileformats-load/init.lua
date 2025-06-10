vim.cmd('packadd! ron.vim')
vim.cmd('packadd! rust.vim')

vim.g.rustfmt_autosave = 1
vim.api.nvim_create_autocmd('FileType', {
    pattern = 'rust',
    callback = function()
        vim.opt.colorcolumn = '+1'
        vim.opt.textwidth = 99
    end,
})
