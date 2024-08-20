"""A base configuration for vim.
"""

from .. import Twig, git, vim


main = git.with_submodules(Twig.empty())
