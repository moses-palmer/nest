"""Neovim plugin for GitHub Copilot.
"""

from .. import npm, nvim


cli = npm.package(
    name='copilot-cli',
    package='@github/copilot',
    description='GitHub Copilot CLI brings the power of Copilot coding agent '
    'directly to your terminal.')
main = nvim.plugin() \
    .depends(cli)
