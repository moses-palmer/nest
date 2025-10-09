" Let :W save with sudo
command! W :call <sid>write_sudo()


" Attempts to write the current buffer with elevated privileges.
function! s:write_sudo()
    if exists('$TMUX')
        let l:temporary = tempname()
        execute 'silent write ' . l:temporary
        try
            let l:source = shellescape(l:temporary)
            let l:target = shellescape(expand('%:p'))
            execute 'silent !tmux-sudo "Write ' . l:target . ' as root" '
            \   . 'sh -c "cat ' . l:source . ' > ' . l:target . '"'
        finally
            call delete(l:temporary)
        endtry
    else
        silent write !sudo tee % > /dev/null
    endif
    if v:shell_error == 0
        edit!
    endif
endfunction
