"""A base configuration for vim.
"""

from .. import Twig, git, vim, shell_utilities


main = git.with_submodules(Twig.empty())
