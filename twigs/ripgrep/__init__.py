"""Recursively searches directories for a regex pattern.
"""

from .. import fzf, rust


main = rust.crate(
    completions=['rg', '--generate=complete-bash'])
