" We set this to have :Man open in the main window
set ft=man

" Load the built-in plugin
let g:no_plugin_maps = 1
let g:no_man_maps = 1
source $VIMRUNTIME/ftplugin/man.vim

nnoremap <silent> <2-LeftMouse> :execute(':Man ' . expand('<cword>'))<CR>
nnoremap <silent> <Up> <C-y>
nnoremap <silent> <Down> <C-e>
nnoremap <silent> <S-UP> k
nnoremap <silent> <S-Down> j
nnoremap <silent> q :q!<cr>

" Ensure no plugin autocmds are used on startup
autocmd! VimEnter *
