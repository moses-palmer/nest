function! s:quickshell()
    let node = g:NERDTreeFileNode.GetSelected()
    call system(
    \     'tmux-quickshell ' . fnameescape(node.path.str()))
    call node.refresh()
    call NERDTreeRender()
endfunction


call NERDTreeAddKeyMap({
\     'key': '<leader>s',
\     'callback': function('s:quickshell'),
\     'quickhelpText': 'open a quickshell',
\ })
