" Set options appropriate for reviewing
set colorcolumn=0
set laststatus=2
set lazyredraw
set noexpandtab
set nolist
set nomodifiable
set nomodified
set nonumber
set noshowcmd
set noshowmode
set noswapfile
set nowrap
set readonly

nnoremap <silent> <PageUp> :call <SID>jump_to_file('b')<CR>
nnoremap <silent> <PageDown> :call <SID>jump_to_file('')<CR>
nnoremap <silent> <S-PageUp> :call <SID>jump_to_commit('b')<CR>
nnoremap <silent> <S-PageDown> :call <SID>jump_to_commit('')<CR>
nnoremap <silent> <leader>g :call <SID>open_modifications()<CR>
nnoremap <silent> <2-LeftMouse> :call <SID>open_modifications()<CR>
nnoremap <silent> <F10> :call <SID>toggle_word_diff()<CR>
nnoremap <silent> <Up> <C-y>
nnoremap <silent> <Down> <C-e>
nnoremap <silent> <S-UP> k
nnoremap <silent> <S-Down> j


" A pattern to find the commit header and extract the commit.
let g:COMMIT_RE = ['^commit ([0-9a-h]\{7\})', 1]

" A pattern to find the diff header for a file pair.
let g:START_RE = ['^diff \(--git\)', 1]

" A pattern to find the file revisions and extract the revisions.
let g:INDEX_RE = ['^index \([0-9a-f]*\)\.\.\([0-9a-f]*\) [0-9]*', 2]

" A pattern to find the file names and extract the paths.
let g:FILE_A_RE = ['^--- a/\(.*\)', 1]
let g:FILE_B_RE = ['^+++ b/\(.*\)', 1]

" A pattern to find a chunk and extract the line numbers.
let g:CHUNK_RE = ['^@@ -\([0-9]*\),\([0-9]*\) +\([0-9]*\),\([0-9]*\) @@', 4]

" Whether to use a word diff for change listing
let g:review#word_diff = 1

" The main window is the parent window
let g:review#win_parent = win_getid()

" The search pattern to use when a terminal job completes to return to the
" previous position.
let g:review#search = ''
autocmd TermClose * if len(g:review#search) > 0
\   | call search(g:review#search, '')
\   | normal zt
\   | endif


" Create the chunk signs
sign define review_s text=↘ linehl= texthl=SignColumn
sign define review_c text=→ linehl=DiffText texthl=SignColumn
sign define review_e text=↗ linehl= texthl=SignColumn


" Loads the change listing.
function! s:load_changes()
    " Make sure we focus the parent window
    call s:goto_parent()

    " Store the current start tag or commit so we can return
    if search(g:START_RE[0], 'bcW') || search(g:COMMIT_RE[0], 'bcW')
        let g:review#search = getline('.')
    else
        let g:review#search = ''
    endif

    " Read the change listing and update the current file name
    if g:review#word_diff
        let l:git_command = 'lc --ignore-all-space'
    else
        let l:git_command = 'log --patch --color=always'
    endif
    bd
    silent! execute('terminal ' .
    \   'git ' .
    \   '--no-pager ' .
    \   l:git_command . ' ' .
    \   '--unified=1 ' .
    \   '--reverse ' .
    \   $REVIEW_TARGET . '..' . $REVIEW_SOURCE)
    file $REVIEW_SOURCE -> $REVIEW_TARGET

    0
    setlocal nomodified
    set modifiable<
    nnoremap <buffer> q :qa<CR>
endfunction


" Finds the files for the current git diff section and opens them in new
" windows.
function! s:open_modifications()
    let l:lineno = line('.')

    " Find the header line
    if !search(g:START_RE[0], 'bcW')
        return
    endif
    let l:start_lineno = line('.')

    " Find the revisions
    let l:m = s:next_match(g:INDEX_RE)
    if empty(l:m)
        echo('Failed to locate index.')
        return
    else
        let [l:rev_a, l:rev_b] = l:m
    endif

    let l:m = s:next_match(g:FILE_A_RE)
    if empty(l:m)
        echo('Failed to locate files.')
        return
    else
        let [l:path_a] = l:m
    endif

    let l:m = s:next_match(g:FILE_B_RE)
    if empty(l:m)
        echo('Failed to locate files.')
        return
    else
        let [l:path_b] = l:m
    endif

    " Find the start of the current chunk
    let l:m = s:find_previous_chunk(l:lineno)
    if empty(l:m)
        let [l:hunk_a_lineno, l:hunk_b_lineno] = [1, 1]
    else
        let [l:hunk_a_lineno, l:hunk_b_lineno] = l:m
    endif

    " Close any previous child windows
    if s:goto_parent()
        call s:close_modifications()
    endif

    " Find the chunks
    let [l:chunks_a, l:chunks_b] = s:find_chunks(l:start_lineno)

    " Open the files
    below vnew
    let l:win_a = win_getid()
    silent call s:open_at_rev(
        \ 'a', l:path_a, l:rev_a, l:chunks_a, l:hunk_a_lineno)

    belowright new
    let l:win_b = win_getid()
    silent call s:open_at_rev(
        \ 'b', l:path_b, l:rev_b, l:chunks_b, l:hunk_b_lineno)

    " Return to the main window and store the child window IDs
    call s:goto_parent()
    let w:review_win_a = l:win_a
    let w:review_win_b = l:win_b
    let g:review#zoomed = 0

    " Add buffer local mappings for diff interactions
    nnoremap <buffer> <Up> :call <SID>for_children("normal k")<CR>
    nnoremap <buffer> <Down> :call <SID>for_children("normal j")<CR>
    nnoremap <buffer> <Left> :call <SID>for_children("normal h'")<CR>
    nnoremap <buffer> <Right> :call <SID>for_children("normal l'")<CR>
    nnoremap <buffer> <PageUp> :call <SID>for_children("normal ['")<CR>
    nnoremap <buffer> <PageDown> :call <SID>for_children("normal ]'")<CR>
    nnoremap <buffer> q :call <SID>close_modifications()<CR>
    nnoremap <buffer> <F9> :call <SID>toggle_zoom()<CR>
endfunction


" Restores the state after having viewed diff files.
function! s:close_modifications()
    if !s:goto_parent() || !s:has_children()
        return
    endif

    call s:for_children('wincmd c')
    call s:goto_parent()
    unlet w:review_win_a
    unlet w:review_win_b

    " Restore mappings
    mapclear <buffer>
    nnoremap <buffer> q :qa<CR>
endfunction


" Toggles word diff mode.
function! s:toggle_word_diff()
    let g:review#word_diff = !g:review#word_diff
    call s:load_changes()
endfunction


" Toggles zooming of the parent window.
function! s:toggle_zoom()
    if !s:goto_parent() || !s:has_children()
        return
    endif
    let l:win_a = w:review_win_a
    let l:win_b = w:review_win_b

    let g:review#zoomed = !g:review#zoomed
    if g:review#zoomed
        call s:for_child(l:win_a, 'wincmd H')
        call s:for_child(l:win_b, 'wincmd L')
        call s:for_parent('wincmd J')
        call s:for_parent('resize 1')
    else
        call s:for_child(l:win_a, 'wincmd K')
        call s:for_child(l:win_b, 'wincmd J')
        call s:for_parent('wincmd H')
    endif
endfunction


" Jumps to a file by searching for a file diff header line.
function! s:jump_to_file(flags)
    call search(g:START_TAG, a:flags)
    normal zt
endfunction


" Jumps to a commit by searching for a commit header line.
function! s:jump_to_commit(flags)
    call search(g:COMMIT_TAG, a:flags)
    normal zt
endfunction


" Determines whether the child window IDs exist.
function! s:has_children()
    return exists('w:review_win_a') && exists('w:review_win_b')
endfunction


" Executes a command in all diff-open child windows.
function! s:for_children(cmd)
    if !s:goto_parent() || !s:has_children()
        return
    endif

    for l:win_id in [w:review_win_a, w:review_win_b]
        call s:for_child(l:win_id, a:cmd)
    endfor

    call s:goto_parent()
endfunction


" Executes a command for a child window.
function! s:for_child(win_id, cmd)
    let l:winnr = win_id2win(a:win_id)
    if l:winnr > 0
        execute(l:winnr . 'wincmd w')
        execute(a:cmd)
    endif
endfunction


" Executes a command for the parent window.
function! s:for_parent(cmd)
    if s:goto_parent()
        execute(a:cmd)
    endif
endfunction


" Finds the chunk header by starting at the current line and moving up until a
" header is found.
function! s:find_previous_chunk(lineno)
    let l:lineno = a:lineno
    while l:lineno > 0
        let l:m = s:match(l:lineno, g:CHUNK_RE)
        let l:lineno = l:lineno - 1
        if empty(l:m)
            if empty(s:match(l:lineno, g:START_RE))
                continue
            else
                break
            endif
        else
            return [l:m[0], l:m[2]]
        endif
    endwhile
endfunction


" Finds chunk data following the git diff header at s:lineno.
"
" The search is continued until the end of the buffer, or until a new git diff
" header is encountered.
function! s:find_chunks(lineno)
    let l:chunks_a = []
    let l:chunks_b = []

    let l:lineno = a:lineno
    while l:lineno <= line('$')
        let l:lineno = l:lineno + 1
        let l:m = s:match(l:lineno, g:CHUNK_RE)
        if empty(l:m)
            if empty(s:match(l:lineno, g:START_RE))
                continue
            else
                break
            endif
        else
            let [l:lineno_a, l:count_a, l:lineno_b, l:count_b] = l:m
            call add(l:chunks_a, [l:lineno_a, l:lineno_a + l:count_a])
            call add(l:chunks_b, [l:lineno_b, l:lineno_b + l:count_b])
        endif
    endwhile

    return [l:chunks_a, l:chunks_b]
endfunction


" Opens a file at a specific revision.
"
" The file is opened in read only mode. A mark is added for each chunk.
function! s:open_at_rev(prefix, path, rev, chunks, lineno)
    " Open the file at the specified revision
    let l:file = a:prefix . '/' . a:path
    setlocal bufhidden=wipe
    \   buftype=nofile
    \   modifiable
    \   nobuflisted
    \   nowrap
    \   number
    if match(a:rev, '^0\+$') == -1
        execute('0read !git show ' . a:rev . ' -- ' . a:path)
        execute('file ' . l:file)
        filetype detect
    endif
    setlocal nomodifiable

    " Add signs and marks for the chunks
    let l:i = 0
    let l:s = 1
    let l:mark = char2nr('a')
    let l:max = char2nr('z') - l:mark
    for [l:start, l:end] in a:chunks
        let l:j = l:start
        while l:j < l:end
            if l:j == l:start
                let l:sign = 'review_s'
            elseif l:j == l:end - 1
                let l:sign = 'review_e'
            else
                let l:sign = 'review_c'
            endif
            execute('sign place ' . l:s . ' '
            \   . 'line=' . l:j . ' '
            \   . 'name=' . l:sign . ' '
            \   . 'buffer=' . bufnr('$'))
            let l:s = l:s + 1
            let l:j = l:j + 1
        endwhile
        if l:i < l:max
            execute(l:start . 'ma ' . nr2char(l:mark + l:i))
            let l:i = l:i + 1
        endif
    endfor

    " Go to the specified line
    execute('normal ' . a:lineno . 'Gz.')

    " Add useful mappings
    nnoremap <buffer> q :silent! call <SID>close_modifications()<CR>
    nnoremap <buffer> k <C-y>
    nnoremap <buffer> j <C-e>
    nnoremap <buffer> h zh
    nnoremap <buffer> l zl
endfunction


" Attempts to match a regular expression agains a line.
"
" Only matched groups are returned, so if the regular expression does not
" contain any groups, it is not possible to determine whether the expression
" matched.
function! s:match(lineno, regex_and_count)
    let [l:regex, l:count] = a:regex_and_count
    let l:m = matchlist(getline(a:lineno), l:regex)
    if empty(l:m)
        return []
    else
        return l:m[1:l:count]
    endif
endfunction


" Searches for the next match for a regular expression, and returns a match if
" found.
function! s:next_match(regex)
    if search(a:regex[0], 'cW')
        return s:match(line('.'), a:regex)
    endif
endfunction


" Moves to the review parent window.
function! s:goto_parent()
    if exists('g:review#win_parent')
        let l:winnr = win_id2win(g:review#win_parent)
        if l:winnr > 0
            execute(l:winnr . 'wincmd w')
            return 1
        else
            echo('Failed to find review window.')
            return 0
        endif
    else
        return 0
    endif
endfunction


call s:load_changes()
