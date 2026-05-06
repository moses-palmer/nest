autocmd BufWritePost *.py call <SID>format()

function! s:format()
    silent call system([
    \   'ruff',
    \   'format',
    \   expand('%:p')])
    silent edit!
endfunction
