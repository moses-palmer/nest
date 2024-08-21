local debug_plugin = vim.fn.glob(
    '~/.local/lib/jdtls/plugins/com.microsoft.java.debug.plugin-*.jar', 1)
require('jdtls').start_or_attach({
    cmd = {'jdtls'},
    capabilities = require'cmp_nvim_lsp'.default_capabilities(),
    root_dir = vim.fs.dirname(vim.fs.find(
        {'gradlew', '.git', 'mvnw'}, { upward = true })[1]),
    init_options = {
        bundles = debug_plugin and { debug_plugin } or {},
    },
})
