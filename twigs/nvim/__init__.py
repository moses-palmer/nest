"""Heavily refactored vim fork.
"""

import os

import nest

from argparse import _SubParsersAction
from pathlib import Path
from typing import List

from .. import ROOT, TWIG_PATH, Twig, caller_context, git, system, twig


@twig()
def main(me: Twig):
    if _use_snap(me):
        from .. import snap
        snap.install(me, True)
    else:
        system.install(me)

main.provides('vim')


@main.checker
def is_installed(me):
    if _use_snap(me):
        from .. import snap
        snap.is_installed(me, me.name)
    else:
        return system.is_installed(me, me.name)


@main.remover
def remove(me: Twig):
    if is_installed(me):
        if _use_snap(me):
            from .. import snap
            snap.remove(me)
        else:
            system.remove(me)


def _use_snap(me: Twig) -> bool:
    """Whether to use ``snap`` to install the application.

    :param me: The currently handled twig.
    """
    system.is_installed(me, 'snap')


def plugin() -> Twig:
    """Defines a twig that is an nvim plugin.
    """
    @twig(globals=caller_context())
    def main(me: Twig):
        pass

    @main.checker
    def is_installed(me: Twig):
        return True

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        return [
            l.rstrip()
            for repopath in repopaths(me)
            for l in git.command(
                me,
                'submodule', '--quiet', 'foreach',
                'if [ "$displaypath" = "${path}" ]; then '
                '   git fetch --quiet; '
                '   git log --format=format:%s '
                '       HEAD.."$(git default-remote)/$(git default-branch)"; '
                'fi',
                capture=True,
                path=repopath.relative_to(nest.ROOT),
            ).splitlines()]

    @main.update_applier
    def update_applier(me: Twig) -> List[str]:
        for repopath in repopaths(me):
            git.command(
                me,
                'submodule', '--quiet', 'foreach',
                'if [ "$displaypath" = "${path}" ]; then '
                '   git checkout "$(git default-branch)"; '
                '   git pull; '
                'fi',
                silent=True,
                path=repopath.relative_to(nest.ROOT))

    def repopaths(me: Twig) -> List[Path]:
        directory = me.source / '.config' / 'nvim' / 'pack' / 'nvim' / 'start'
        return [
            directory / p
            for p in directory.iterdir()
            if  p.is_dir()]

    return main


def twig_main(me: Twig, **kwargs):
    def plugin(**kwargs):
        def add(name: str, description: str, repository: str):
            path = TWIG_PATH / name.replace('-', '_')
            pack = repository.rsplit('/', 1)[-1]
            repopath = path / 'files' / '.config' / 'nvim' / 'pack' / 'nvim' \
                / 'start'
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            try:
                os.makedirs(repopath)
            except:
                pass
            git.command(
                me,
                'submodule', 'add',
                repository,
                repopath.relative_to(ROOT) / pack)
            nest.template(
                Path(__file__).parent / 'plugin.__init__.py.template',
                path / '__init__.py',
                name=name,
                description=description,
                pack=pack,
                repository=repository)
            nest.template(
                Path(__file__).parent / 'plugin.packadd.template',
                path / 'files' / '.config' / 'nvim' / 'lua' / pack / 'init.lua',
                name=name,
                description=description,
                pack=pack,
                repository=repository)

        {
            'add': add,
        }[kwargs.pop('nvim_plugin_command')](**kwargs)

    {
        'plugin': plugin,
    }[kwargs.pop('nvim_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='Manages neovim.') \
        .add_subparsers(required=True, dest='nvim_command')

    plugin = actions.add_parser('plugin', help='Manages neovim plugins.') \
        .add_subparsers(required=True, dest='nvim_plugin_command')
    add = plugin.add_parser(
        'add',
        help='Adds a neovim plugin.')
    add.add_argument(
        '--name',
        help='The name of the plugin twig.',
        required=True)
    add.add_argument(
        '--description',
        help='The description of the plugin twig.',
        default='A neovim plugin.')
    add.add_argument(
        'repository',
        help='The plugin repository.')

    return {
        me.name: lambda **args: twig_main(me, **args)}
