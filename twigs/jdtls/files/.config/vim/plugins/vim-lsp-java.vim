let s:debug_plugin = expand(glob(
\   '~/.local/lib/jdtls/plugins/com.microsoft.java.debug.plugin-*.jar'))
au User lsp_setup
\   call lsp#register_server({
\       'name': 'jdtls',
\       'cmd': {server_info->['jdtls']},
\       'allowlist': ['java'],
\       'initialization_options': filereadable(s:debug_plugin)
\           ? { 'bundles': [s:debug_plugin] }
\           : {},
\   }) |
\   call lsp#register_command(
\       'java.apply.workspaceEdit',
\       function('s:java_apply_workspaceEdit'))
autocmd FileType java setlocal omnifunc=lsp#complete

function! s:java_apply_workspaceEdit(context)
    let l:command = get(a:context, 'command', {})
    call lsp#utils#workspace_edit#apply_workspace_edit(
    \   l:command['arguments'][0])
endfunction
