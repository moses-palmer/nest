"""Quickstart configs for Nvim LSP.
"""

from .. import Twig, nvim


main = nvim.plugin() \
    .provides('vim-vim-lsp')
