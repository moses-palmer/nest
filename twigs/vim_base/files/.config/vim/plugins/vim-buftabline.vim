packadd! vim-buftabline

let g:buftabline_separators = v:true

nnoremap <silent> <M-Left> :call <SID>previous_buffer()<CR>
nnoremap <silent> <M-Right> :call <SID>next_buffer()<CR>
imap <silent> <M-Left> <C-o>:call <SID>previous_buffer()<CR>
imap <silent> <M-Right> <C-o>:call <SID>next_buffer()<CR>


" Selects the next buffer in the 'file window'.
function! s:next_buffer()
    call lib#for_main_window(':bnext')
endfunction


" Selects the previous buffer in the 'file window'.
function! s:previous_buffer()
    call lib#for_main_window(':bprevious')
endfunction
