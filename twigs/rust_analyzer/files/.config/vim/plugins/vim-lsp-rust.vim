au User lsp_setup
\   call lsp#register_server({
\       'name': 'rust-analyzer',
\       'cmd': {server_info->['rust-analyzer']},
\       'allowlist': ['rust'] }) |
\   call lsp#register_command(
\       'rust-analyzer.applySourceChange',
\       function('s:applySourceChange')) |
\   call lsp#register_command(
\       'rust-analyzer.runSingle',
\       function('s:runSingle'))
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

function! s:runSingle(context) abort
    let l:command = get(
    \   a:context, 'command', {})
    let l:arguments = get(
    \   l:command, 'arguments', [])
	let l:argument = get(
    \   l:arguments, 0, {})

    if !has_key(l:argument, 'kind')
        call lsp_settings#utils#error(
        \   'unsupported rust-analyzer.runSingle command. '
        \   . json_encode(l:command))
        return
    elseif l:argument['kind'] ==# 'cargo'
        let l:args = get(
        \   l:argument, 'args', {})
        let l:workspaceRoot = get(
        \   l:args, 'workspaceRoot', getcwd())
        let l:cmd = ['cargo']
        \   + get(l:args, 'cargoArgs', [])
        \   + get(l:args, 'cargoExtraArgs', [])
        \   + has_key(l:args, 'executableArgs')
        \      ? ['--'] + get(l:args, 'executableArgs')
        \      : []

        call lsp_settings#utils#term_start(l:cmd, {'cwd': l:workspaceRoot})
    else
        call lsp_settings#utils#error(
        \   'unsupported rust-analyzer.runSingle command. '
        \   . json_encode(l:command))
    endif
endfunction
