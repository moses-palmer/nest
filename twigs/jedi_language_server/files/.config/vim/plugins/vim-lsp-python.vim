au User lsp_setup call lsp#register_server({
\   'name': 'jedi-language-server',
\   'cmd': {server_info->['jedi-language-server']},
\   'allowlist': ['python'],
\ })
autocmd FileType python setlocal omnifunc=lsp#complete

