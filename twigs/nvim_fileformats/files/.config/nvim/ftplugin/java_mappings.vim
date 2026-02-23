function! s:is_java_project()
    let l:current = expand('%:p:h')
    for l:name in ['pom.xml', 'build.gradle']
        let l:project_file = findfile(l:name, l:current . ';')
        if !empty(l:project_file)
            return v:true
        endif
    endfor

    return v:false
endfunction


" Is this a Java project?
if s:is_java_project()
    nnoremap <buffer> mt :call <SID>toggle_test()<cr>
endif


if exists('s:is_loaded')
    finish
endif


" Toggles between a class and its test suite.
function! s:toggle_test()
    let l:is_test = expand('%:p') =~ 'src/test/java/.*Test\.java$'
    let l:is_main = expand('%:p') =~ 'src/main/java/.*\.java$'
    if l:is_test && !l:is_main
        execute(':e ' . substitute(
        \   substitute(expand('%:p'), 'Test\.java$', '.java', 'g'),
        \   'src/test/java',
        \   'src/main/java',
        \   'g'))
    elseif !l:is_test && l:is_main
        execute(':e ' . substitute(
        \   substitute(expand('%:p'), '\.java$', 'Test.java', 'g'),
        \   'src/main/java',
        \   'src/test/java',
        \   'g'))
    endif
endfunction


let s:is_loaded = v:true
