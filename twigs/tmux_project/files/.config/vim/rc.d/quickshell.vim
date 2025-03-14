" Opens a tmux quickshell in a directory.
function! quickshell#open(directory)
    call system(
    \   'tmux-quickshell ' . fnameescape(a:directory))
endfunction
