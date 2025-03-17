"""An implementation of Language Server Protocol for the Rust programming
language.
"""
from .. import nvim_lsp_config, rust, rust_src


main = rust.component(name='rust-analyzer')
