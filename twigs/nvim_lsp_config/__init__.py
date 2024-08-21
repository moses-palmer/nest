"""Quickstart configs for Nvim LSP.
"""

from .. import Twig, nvim, nvim_telescope


main = nvim.plugin() \
    .provides('vim-vim-lsp')
