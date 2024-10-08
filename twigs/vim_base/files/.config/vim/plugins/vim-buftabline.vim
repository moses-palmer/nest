packadd! vim-buftabline

let g:buftabline_separators = v:true

nnoremap <silent> <M-Left> :call <SID>previous_buffer()<CR>
nnoremap <silent> <M-Right> :call <SID>next_buffer()<CR>
imap <silent> <M-Left> <C-o>:call <SID>previous_buffer()<CR>
imap <silent> <M-Right> <C-o>:call <SID>next_buffer()<CR>


" Selects the next buffer in the 'file window'.
function! s:next_buffer()
    call s:cycle(':bnext')
endfunction


" Selects the previous buffer in the 'file window'.
function! s:previous_buffer()
    call s:cycle(':bprevious')
endfunction


" Cycles between buffers in the main window until an editor buffer is
" encountered.
"
" If the original buffer is encountered, the command is executed a final time.
"
" command must be a buffer changing command.
function! s:cycle(command)
    let l:main_window = lib#main_window()
    let l:original_buffer = winbufnr(l:main_window)
    while 1
        call lib#for_window(l:main_window, a:command)
        if lib#is_editor_window(l:main_window)
            return
        elseif winbufnr(l:main_window) == l:original_buffer
            call lib#for_window(l:main:window, a:command)
            return
        endif
    endwhile
endfunction
