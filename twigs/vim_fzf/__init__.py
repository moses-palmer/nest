"""FZF integration for vim.
"""

from .. import Twig, fzf, vim


main = vim.plugin()


@main.completer
def complete(me: Twig):
    me.run(
        (me.source / '.vim' / 'pack' / 'plugins' / 'opt' / 'fzf' / 'install')
            .as_posix(),
        '--xdg', '--no-bash', '--no-fish', '--no-zsh',
        silent=True)
