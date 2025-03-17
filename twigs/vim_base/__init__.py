"""A base configuration for vim.
"""

from .. import Twig, git, nvim


main = git.with_submodules(Twig.empty())
