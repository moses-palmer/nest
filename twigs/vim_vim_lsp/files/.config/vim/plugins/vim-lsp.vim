packadd! asyncomplete.vim
packadd! asyncomplete-lsp.vim
packadd! vim-lsp

let g:lsp_async_completion = 1
let g:lsp_diagnostics_echo_cursor = 1
let g:lsp_diagnostics_float_cursor = 1
let g:lsp_diagnostics_virtual_text_enabled = 0
let g:lsp_document_code_action_signs_hint = {'text': '▶'}
let g:lsp_format_sync_timeout = 1000
let g:lsp_semantic_enabled = 1
let g:lsp_use_native_client = 1


" Require explicit toggling, as this may make the UI slow
if get(g:, 'lsp_fold_enabled', 0)
    set foldmethod=expr
    \   foldexpr=lsp#ui#vim#folding#foldexpr()
    \   foldtext=lsp#ui#vim#folding#foldtext()
else
    let g:lsp_fold_enabled = 0
endif


function! s:on_lsp_buffer_enabled() abort
    setlocal omnifunc=lsp#complete
    setlocal signcolumn=yes
    if exists('+tagfunc') | setlocal tagfunc=lsp#tagfunc | endif

    nmap <buffer> ga <plug>(lsp-code-action-float)
    nmap <buffer> gA <plug>(lsp-code-lens)
    nmap <buffer> rr <plug>(lsp-rename)

    nmap <buffer> gd <plug>(lsp-definition)
    nmap <buffer> gD :rightbelow vertical LspDefinition<CR>
    nmap <buffer> <leader>d <plug>(lsp-peek-definition)

    nmap <buffer> gI <plug>(lsp-implementation)
    nmap <buffer> <leader>i <plug>(lsp-peek-implementation)

    nmap <buffer> gt <plug>(lsp-type-definition)
    nmap <buffer> gT :rightbelow vertical LspTypeDefinition<CR>
    nmap <buffer> <leader>t <plug>(lsp-peek-type-definition)

    nmap <buffer> gh <plug>(lsp-call-hierarchy-incoming)
    nmap <buffer> gH <plug>(lsp-call-hierarchy-outgoing)
    nmap <buffer> gr <plug>(lsp-references)

    nmap <buffer> gs <plug>(lsp-document-symbol-search)
    nmap <buffer> gS <plug>(lsp-workspace-symbol-search)

    nmap <buffer> K <plug>(lsp-hover)
    nmap <buffer> <leader>K :LspHover --ui=preview<CR>

    nmap <buffer> <M-Down> <plug>(lsp-next-diagnostic)
    nmap <buffer> <M-Up> <plug>(lsp-previous-diagnostic)
    nnoremap <buffer> <expr><c-f> lsp#scroll(+4)
    nnoremap <buffer> <expr><c-d> lsp#scroll(-4)

    nmap <F3> :call <SID>all_diagnostics()<CR>
    imap <F3> <C-o>:call <SID>all_diagnostics()<CR>

    " Allow mouse navigation; make sure to press the left button to change
    " cursor position before going to definition
    nmap <C-LeftMouse> <LeftMouse><plug>(lsp-definition)
    imap <C-LeftMouse> <LeftMouse><C-o><plug>(lsp-definition)
endfunction


function! s:all_diagnostics()
    if s:toggle_quickfix_window()
        LspDocumentDiagnostics
    endif
endfunction


" Toggles the quickfix window and returns whether is is visible.
function! s:toggle_quickfix_window()
    for l:window in getwininfo()
        if l:window.quickfix == 1
            " Close the quick fix window
            execute l:window.winnr . 'wincmd w'
            execute 'wincmd c'

            " Reselect the editor window
            execute lib#main_window() . 'wincmd w'
            return 0
        endif
    endfor

    return 1
endfunction


augroup lsp_install
    au!
    autocmd User lsp_buffer_enabled call s:on_lsp_buffer_enabled()
augroup END
