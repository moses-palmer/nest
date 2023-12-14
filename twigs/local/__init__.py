"""Local files for this computer only.
"""

import importlib

from argparse import _SubParsersAction
from pathlib import Path
from typing import List

import nest.ui
from .. import Twig


main = Twig.empty()


for p in (
        p
        for p in Path(__file__).parent.iterdir()
        if p.is_file() and p.suffix == '.py' and p.name[0] != '_'):
    importlib.import_module('.' + p.name.rsplit('.', 1)[0], __package__)


def twig_main(me: Twig, **kwargs):
    def list(**kwargs):
        def leaves(path: Path) -> List[Path]:
            if path.is_dir():
                return [p for p in path.iterdir()]
            else:
                return []

        def string(level: int, path: Path) -> str:
            if level == 0:
                return nest.ui.bold('Local files')
            elif path.is_dir():
                return nest.ui.ignoring(path.name)
            else:
                return path.name

        nest.ui.tree(me.source, leaves, string)

    {
        'list': list,
    }[kwargs.pop('local_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='Manages local files.') \
        .add_subparsers(required=True, dest='local_command')

    list = actions.add_parser(
        'list',
        help='Lists local files')

    return {
        me.name: lambda **args: twig_main(me, **args)}
