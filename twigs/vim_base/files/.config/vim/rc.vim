" Enable syntax highlighting; this may not be set in the global resource file
if has('syntax')
    syntax on
    filetype plugin indent on
endif


set backspace=indent,eol,start
set backupdir=~/.cache/vim/backup//
set colorcolumn=80
set cursorline
set directory=~/.cache/vim/swap//
set expandtab
set hidden
set hlsearch
set incsearch
set laststatus=3
set listchars=extends:>,precedes:<
set mouse=a
set nocompatible
set nowrap
set number
set numberwidth=4
set ruler
set shiftwidth=4
set sidescroll=1
set sidescrolloff=2
set signcolumn=yes
set smartcase
set smartindent
set smarttab
set splitbelow
set tabstop=4
set textwidth=79
set undodir=~/.cache/vim/undo//
set updatetime=250
set wildmenu


" Ensure the background is correctly handled in tmux
set t_ut=

" Detect whether the current terminal supports italics
let g:term_has_italics = stridx(
\   system('infocmp ' . $TERM . ' | grep sitm'),
\   'sitm') > -1


" Include library functions
exe 'source' '~/.config/vim/lib.vim'


" Match the readline configuration
let &t_SI .= "\<Esc>[6 q"
let &t_EI .= "\<Esc>[2 q"


" Beautify fillchars
if has('nvim')
    let &fillchars = 'eob: ,stl:─,stlnc:─,horiz:─,vert:│'
else
    let &fillchars = 'eob: ,stl:─,stlnc:─,vert:│'
endif


" Use tab as leader instead of backslash, and clear current search on double
" leader; clear the search now as well, since set hlsearch above will
" re-highlight matches when this file is reloaded
let mapleader="\<tab>"
map <silent> <leader><leader> :nohlsearch<CR>
nohlsearch


" Scroll using arrow keys
map <S-Down> <C-E>
imap <S-Down> <C-O><C-E>
map <S-Up> <C-Y>
imap <S-Up> <C-O><C-Y>


" Send current window to sides
noremap <leader>h <C-w>H
noremap <leader>j <C-w>J
noremap <leader>k <C-w>K
noremap <leader>l <C-w>L


" Quickly run @a
nmap <leader>A qa
nmap <leader>a @a

" Reflow paragraph and selection
vnoremap <C-a> gw
noremap <C-a> gw

" Toggle relative numbers with <leader>r
nnoremap <leader>r :set relativenumber!<CR>


" Let \q and \w close buffers, but not windows
command! KillBufferMoveLeft
\   call lib#for_main_window('call lib#kill_current_buffer(-1)')
command! KillBufferMoveRight
\   call lib#for_main_window('call lib#kill_current_buffer(1)')
command! KillLeft
\   call lib#for_main_window('call lib#kill_other_buffers(-1)')
command! KillRight
\   call lib#for_main_window('call lib#kill_other_buffers(1)')
map <silent> <leader>q :KillBufferMoveLeft<CR>
map <silent> <leader>Q :KillLeft<CR>
map <silent> <leader>w :KillBufferMoveRight<CR>
map <silent> <leader>W :KillRight<CR>


" Strip trailing whitespace
let whitespace_blacklist = ['diff']
autocmd BufWritePre * if index(whitespace_blacklist, &ft) < 0 | %s/\s\+$//e


" Include library functions
source ~/.config/vim/lib.vim


" Allow local overrides
if filereadable(expand('~/.config/vim/local.vim'))
    source ~/.config/vim/local.vim
endif


" Load all plugin configurations
let s:loaded_plugins = []
let s:vimscript_plugin_dir = expand('~/.config/vim/plugins/')
let s:lua_plugin_dir = expand('~/.config/nvim/lua/')
function! s:load_plugin(name)
    if index(s:loaded_plugins, a:name) == -1
        call add(s:loaded_plugins, a:name)
        if has('nvim') && filereadable(s:lua_plugin_dir . a:name . '/init.lua')
            execute 'lua' 'require("' . a:name . '")'
        elseif filereadable(s:vimscript_plugin_dir . a:name . '.vim')
            execute 'source' s:vimscript_plugin_dir . a:name . '.vim'
        endif
    endif
endfunction
if exists('$VIM_PLUGINS')
    for s:name in split($VIM_PLUGINS, ':')
        call s:load_plugin(s:name)
    endfor
else
    " Sort file names to ensure consistent order
    for s:file in sort(readdir(s:vimscript_plugin_dir, '1'))
        call s:load_plugin(join(split(s:file, '\.')[:-2], '.'))
    endfor
    if has('nvim')
        for s:directory in sort(readdir(s:lua_plugin_dir, '1'))
            call s:load_plugin(s:directory)
        endfor
    endif
endif


" Load other configurations; sort file names to ensure consistent order
let s:rc_dir = expand('~/.config/vim/rc.d/')
for f in sort(readdir(s:rc_dir, '1'))
    exe 'source' s:rc_dir . f
endfor


" Load theme
try
    if has('termguicolors')
        set termguicolors
        colorscheme onedark
        highlight ColorColumn guibg=#353535

        " Switch these highlight groups to work better with OneDark
        highlight link BufTabLineCurrent PmenuSel
        highlight link BufTabLineActive TabLineSel
    else
        colorscheme noctu
    endif
catch /^Vim\%((\a\+)\)\=:E185/
    " Ignore
endtry
