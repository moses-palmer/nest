"""Recursively searches directories for a regex pattern.
"""

from .. import rust


main = rust.crate(
    completions=['rg', '--generate=complete-bash'])
