"""A CLI tool for code structural search, lint and rewriting.
"""

from .. import Twig, build_environment, rust


main = rust.crate(
    name='ast-grep',
    completions=['sg', 'completions', 'bash'])
