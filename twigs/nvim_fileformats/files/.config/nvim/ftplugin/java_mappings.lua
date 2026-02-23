local function is_java_project()
    return next(vim.fs.find(
        { 'pom.xml', 'build.gradle' },
        {
            path = vim.api.nvim_buf_get_name(0),
            type = 'file',
            upward = true
        }
    )) != nil
end

local function toggle()
    local MAIN = { 'src/main/java', '.java' }
    local TEST = { 'src/test/java', 'Test.java' }

    local current = vim.api.nvim_buf_get_name(0)
    local main = string.find(current, MAIN[1], 1, true)
    local test = string.find(current, TEST[1], 1, true)

    local other
    if main and test == nil then
        other = vim.fs.normalize(string.gsub(
            string.gsub(current, MAIN[2] .. '$', TEST[2]), MAIN[1], TEST[1]), {})
    elseif test and main == nil then
        other = vim.fs.normalize(string.gsub(
            string.gsub(current, TEST[2] .. '$', MAIN[2]), TEST[1], MAIN[1]), {})
    end

    if other != nil and vim.uv.fs_stat(other) then
        vim.cmd.edit(other)
    else
        print('No Java main/test file pair found')
    end
end


if is_java_project() then
    vim.keymap.set('n', 'mt', toggle)
end
