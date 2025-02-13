" Open a new scratch buffer
command! Scratch split
\   | noswapfile hide enew
\   | setlocal buftype=
\   | setlocal bufhidden=hide
\   | file Scratch
