" Starts the server and creates the command pipe.
"
" A cleanup handler will be registered
function server#start(command_pipe)
    call system('mkfifo ' . shellescape(a:command_pipe))
    if has('nvim')
        let s:server_job = jobstart(['tail', '-f', a:command_pipe], {
        \   'on_stdout': expand('<SID>') . 'on_command_nvim'})
    else
        let s:server_job = job_start(['tail', '-f', a:command_pipe], {
        \   'out_cb': expand('<SID>') . 'on_command_vim'})
    endif
    let s:command_pipe = a:command_pipe

    augroup Server
        autocmd VimLeave * call <SID>stop()<cr>
    augroup END
endfunction


" The function called when a message is read from the command pipe.
"
" It will simply execute the string.
function s:on_command_vim(channel, msg)
    execute a:msg
endfunction

" The function called when a message is read from the command pipe.
"
" It will simply execute the string.
function s:on_command_nvim(job_id, msg, event)
    execute a:msg[0]
endfunction


" Cleans up the server by stopping the job and removing the command pipe.
function s:stop()
    call job_stop(s:server_job)
    call system('rm ' . shellescape(s:command_pipe))
endfunction
