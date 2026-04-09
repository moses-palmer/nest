set packpath+=~/.vim
source ~/.vimrc

" Beautify fillchars even more
let &fillchars = 'eob: ,stl:─,stlnc:─,horiz:─,vert:│'

" Enable global window borders for nvim 0.11
if has('nvim-0.11')
    set winborder=rounded
endif
