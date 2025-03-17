"""Heavily refactored vim fork.
"""

import shutil

import nest

from argparse import _SubParsersAction
from pathlib import Path
from typing import List

from .. import (
    ROOT,
    TWIG_PATH,
    Twig,
    as_mod,
    caller_context,
    git,
    normalize,
    system,
    twig,
)


main = system.package()


@main.completer
def complete(me: Twig):
    me.run(
        'nvim',
        '--cmd', 'try | helptags ALL | finally | q! | endtry')


def plugin() -> Twig:
    """Defines a twig that is an nvim plugin.
    """
    @twig(globals=caller_context())
    def main(me: Twig):
        pass

    @main.checker
    def is_installed(me: Twig):
        return True

    return git.with_submodules(main)


def twig_main(me: Twig, **kwargs):
    def plugin(**kwargs):
        def add(name: str, description: str, repository: str):
            pack = repository.rsplit('/', 1)[-1]
            loader_name = normalize(name) + '-load'

            twig_path = TWIG_PATH / as_mod(name)
            base_path = twig_path / 'files' / '.config' / 'nvim'
            repo_path = base_path / 'pack' / 'nvim' / 'start' / pack
            loader_path = base_path / 'lua' / loader_name / 'init.lua'
            if twig_path.exists():
                raise nest.NestException(
                    'Directory {} already exists!', twig_path)

            me.directory(repo_path.parent)
            try:
                git.command(
                    me,
                    'submodule', 'add',
                    repository,
                    repo_path.relative_to(ROOT))
                me.template(
                    Path(__file__).parent / 'plugin.__init__.py.template',
                    twig_path / '__init__.py',
                    name=name,
                    description=description,
                    pack=pack,
                    repository=repository)
                me.template(
                    Path(__file__).parent / 'plugin.packadd.template',
                    loader_path,
                    name=name,
                    description=description,
                    pack=pack,
                    repository=repository)
            except:
                shutil.rmtree(twig_path)
                raise

        {
            'add': add,
        }[kwargs.pop('nvim_plugin_command')](**kwargs)

    {
        'plugin': plugin,
    }[kwargs.pop('nvim_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='manage neovim') \
        .add_subparsers(required=True, dest='nvim_command')

    plugin = actions.add_parser('plugin', help='manage neovim plugins') \
        .add_subparsers(required=True, dest='nvim_plugin_command')
    add = plugin.add_parser(
        'add',
        help='add a neovim plugin')
    add.add_argument(
        '--name',
        help='the name of the plugin twig',
        required=True)
    add.add_argument(
        '--description',
        help='the description of the plugin twig',
        default='A neovim plugin.')
    add.add_argument(
        'repository',
        help='the plugin repository')

    return {
        me.name: lambda **args: twig_main(me, **args)}
