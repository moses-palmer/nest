"""A base configuration for vim.
"""

from .. import Twig, git, nvim, shell_utilities


main = git.with_submodules(Twig.empty())
