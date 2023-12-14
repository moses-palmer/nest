"""Local files for this computer only.
"""

import importlib

from argparse import _SubParsersAction
from pathlib import Path

from .. import Twig, empty, run


main = empty()


for p in (
        p
        for p in Path(__file__).parent.iterdir()
        if p.is_file() and p.suffix == '.py' and p.name[0] != '_'):
    importlib.import_module('.' + p.name.rsplit('.', 1)[0], __package__)


def twig_main(me: Twig, **kwargs):
    def list(**kwargs):
        run(
            me.name,
            'tree', '-a',
            '-I', '__pycache__',
            '-I', '.gitignore',
            me.source.parent)

    {
        'list': list,
    }[kwargs.pop('local_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    from .. import tree

    if tree.main.enabled:
        actions = actions.add_parser(me.name, help='Manages local files.') \
            .add_subparsers(required=True, dest='local_command')

        list = actions.add_parser(
            'list',
            help='Lists local files')

        return {
            me.name: lambda **args: twig_main(me, **args)}
