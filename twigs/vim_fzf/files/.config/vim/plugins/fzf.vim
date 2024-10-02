packadd! fzf
packadd! fzf.vim


if $TMUX_PROJECT_SHOW_HIDDEN == 'yes'
    let $FZF_DEFAULT_COMMAND = $FZF_DEFAULT_COMMAND . ' --hidden'
    let $FZF_SEARCH_COMMAND = $FZF_SEARCH_COMMAND . ' --hidden'
endif
if $TMUX_PROJECT_SHOW_VCS == 'yes'
    let $FZF_DEFAULT_COMMAND = $FZF_DEFAULT_COMMAND . ' --no-ignore-vcs'
    let $FZF_SEARCH_COMMAND = $FZF_SEARCH_COMMAND . ' --no-ignore-vcs'
endif


map <C-p> :call <SID>fzf_for_file_window()<CR>
imap <C-p> <C-o>:call <SID>fzf_for_file_window()<CR>
map <leader><C-p> :call <SID>fzf_for_file_window_git_dirty()<CR>
map <C-k> :call <SID>rg_for_file_window()<CR>
imap <C-k> <C-o>:call <SID>rg_for_file_window()<CR>


" Runs FZF in the 'file window'.
function! s:fzf_for_file_window()
    call lib#for_main_window(':FZF')
endfunction


" Runs FZF in the 'file window' for dirty git files.
function! s:fzf_for_file_window_git_dirty()
    try
        let l:fzf_default_command = $FZF_DEFAULT_COMMAND
        let $FZF_DEFAULT_COMMAND = 'git diff --name-only'
        call s:fzf_for_file_window()
    finally
        let $FZF_DEFAULT_COMMAND = l:fzf_default_command
    endtry
endfunction


" Runs RGPreview in the 'file window'.
function! s:rg_for_file_window()
    call lib#for_main_window(':call ' . expand('<SID>') . 'rg()')
endfunction

function! s:rg()
    call fzf#vim#grep(
    \   $FZF_SEARCH_COMMAND . ' -- ""',
    \   1,
    \   fzf#vim#with_preview())
endfunction
