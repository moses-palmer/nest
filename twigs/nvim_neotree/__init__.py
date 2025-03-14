"""Neovim plugin to manage the file system and other tree like structures.
"""

from .. import nvim, nvim_nui, nvim_web_devicons


main = nvim.plugin() \
    .provides('vim-nerdtree')
