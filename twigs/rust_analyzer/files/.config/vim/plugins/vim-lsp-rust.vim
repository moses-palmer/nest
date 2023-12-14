au User lsp_setup
\ call lsp#register_server({
\   'name': 'rust-analyzer',
\   'cmd': {server_info->['rust-analyzer']},
\   'allowlist': ['rust'] }) |
\ call lsp#register_command(
\   'rust-analyzer.applySourceChange',
\   function('s:applySourceChange'))
autocmd! FileType rust setlocal omnifunc=lsp#complete
autocmd! BufWritePre *.rs call execute('LspDocumentFormatSync')

function! s:applySourceChange(context)
    let l:command = get(
    \   a:context, 'command', {})
    let l:workspace_edit = get(
    \   l:command['arguments'][0], 'workspaceEdit', {})
    if !empty(l:workspace_edit)
        call lsp#utils#workspace_edit#apply_workspace_edit(l:workspace_edit)
    endif

    let l:cursor_position = get(
    \   l:command['arguments'][0], 'cursorPosition', {})
    if !empty(l:cursor_position)
        call cursor(lsp#utils#position#lsp_to_vim('%', l:cursor_position))
    endif
endfunction
