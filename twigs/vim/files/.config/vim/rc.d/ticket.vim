nmap <silent> <leader>t :call TicketOpen()<CR>


" Opens the ticket at the cursor.
"
" The ticket name is extracted using <cfile>.
function! TicketOpen()
    if !exists('g:ticket_url_format')
        echo 'No URL format defined; set g:ticket_url_format'
        return
    endif

    let l:ticket = expand('<cfile>')

    " Attempt to split the ticket name
    let l:parts = split(l:ticket, '-')
    if len(l:parts) == 2
        let [l:project, l:number] = l:parts
    else
        let [l:project, l:number] = ['', l:ticket]
    endif

    " Replace the keys in the URL format string
    let l:url = g:ticket_url_format
    for [l:k, l:v] in [
            \ ['ticket', l:ticket],
            \ ['project', l:project],
            \ ['number', l:number]]
        let l:url = substitute(l:url, '${' . l:k . '}', l:v, '')
    endfor

    call system('gio open "' . l:url . '" & >/dev/null')
    echo 'Opened ' . l:url
endfunction
