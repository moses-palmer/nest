local bundles = {
    vim.fn.glob(
        '~/.local/lib/jdtls/plugins/com.microsoft.java.debug.plugin-*.jar', 1),
}
require('jdtls').start_or_attach({
    cmd = {'jdtls'},
    capabilities = require'cmp_nvim_lsp'.default_capabilities(),
    init_options = {
        bundles = bundles,
    },
})
