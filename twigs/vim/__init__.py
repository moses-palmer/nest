"""Vi IMproved - enhanced vi editor.
"""

import os

import nest

from argparse import _SubParsersAction
from pathlib import Path
from typing import List

from .. import ROOT, TWIG_PATH, Twig, caller_context, git, system, twig


main = system.package()


@main.completer
def complete(me: Twig):
    me.run(
        'vim',
        '--cmd', 'try | helptags ALL | finally | q! | endtry')


def plugin() -> Twig:
    """Defines a twig that is a vim plugin.
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
            path = TWIG_PATH / name.replace('-', '_').replace('.', '_')
            pack = repository.rsplit('/', 1)[-1].replace('.', '_')
            packfile = (
                pack + '.vim'
                if not pack.endswith('.vim') else
                pack)
            repopath = path / 'files' / '.vim' / 'pack' / 'plugins' / 'opt'
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            try:
                os.makedirs(repopath)
            except:
                pass
            try:
                git.command(
                    me,
                    'submodule', 'add',
                    repository,
                    repopath.relative_to(ROOT) / packfile)
                nest.template(
                    Path(__file__).parent / 'plugin.__init__.py.template',
                    path / '__init__.py',
                    name=name,
                    description=description,
                    pack=pack,
                    repository=repository)
                nest.template(
                    Path(__file__).parent / 'plugin.packadd.template',
                    path / 'files' / '.config' / 'vim' / 'plugins' / packfile,
                    name=name,
                    description=description,
                    pack=pack,
                    repository=repository)
            except:
                os.removedirs(path)
                raise

        {
            'add': add,
        }[kwargs.pop('vim_plugin_command')](**kwargs)

    {
        'plugin': plugin,
    }[kwargs.pop('vim_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='Manages vim.') \
        .add_subparsers(required=True, dest='vim_command')

    plugin = actions.add_parser('plugin', help='Manages vim plugins.') \
        .add_subparsers(required=True, dest='vim_plugin_command')
    add = plugin.add_parser(
        'add',
        help='Adds a vim plugin.')
    add.add_argument(
        '--name',
        help='The name of the plugin twig.',
        required=True)
    add.add_argument(
        '--description',
        help='The description of the plugin twig.',
        default='A vim plugin.')
    add.add_argument(
        'repository',
        help='The plugin repository.')

    return {
        me.name: lambda **args: twig_main(me, **args)}
