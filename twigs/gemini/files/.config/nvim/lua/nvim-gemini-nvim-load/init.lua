vim.cmd('packadd! gemini.nvim')


require'gemini'.setup {
    completion = {
        insert_result_key = '<Tab>',
    },
}
