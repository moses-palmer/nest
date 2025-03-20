"""Neovim plugin to manage the file system and other tree like structures.
"""

from .. import nvim, nvim_nui, nvim_plenary_nvim, nvim_web_devicons


main = nvim.plugin() \
    .provides('vim-nerdtree')
