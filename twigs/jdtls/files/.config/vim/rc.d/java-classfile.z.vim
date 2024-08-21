" Prevent CFR from handling class files if we use nvim-jdtls
if has('nvim')
    autocmd! java_decompile
endif
