autocmd BufWritePost *.py call <SID>black()

function! s:black()
    silent call system([
    \   'black',
    \   '--quiet',
    \   '--config',
    \   s:configuration_file(),
    \   expand('%:p')])
    silent edit!
endfunction


function! s:configuration_file()
    if exists('g:black_configuration_file')
        return g:black_configuration_file
    else
        let l:current = expand('%:p:h')
        for l:name in ['pyproject.toml', 'setup.cfg', 'tox.ini']
            let l:configuration_file = findfile(l:name, l:current . ';')
            if !empty(l:configuration_file)
                return l:configuration_file
            endif
        endfor

        return expand('~/.config/black/configuration')
    endif
endfunction
