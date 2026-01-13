"""Gemini bindings for Neovim.
"""

from .. import npm, nvim


cli = npm.package(
    name='gemini-cli',
    package='@google/gemini-cli',
    description='Gemini CLI.')
main = nvim.plugin() \
    .depends(cli)
