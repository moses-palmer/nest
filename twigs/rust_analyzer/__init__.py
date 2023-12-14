"""An implementation of Language Server Protocol for the Rust programming
language.
"""
from .. import rust, rust_src, vim_vim_lsp


main = rust.component(name='rust-analyzer')
