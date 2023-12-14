"""Local files for this computer only.
"""

import importlib
import os
import zipfile

from argparse import _SubParsersAction
from itertools import chain
from pathlib import Path
from typing import List

import nest
import nest.ui

from nest import directories
from .. import Twig, git


#: The local configuration file.
CONFIGURATION_FILE = 'local.conf'


main = Twig.empty()


for p in (
        p
        for p in Path(__file__).parent.iterdir()
        if p.is_file() and p.suffix == '.py' and p.name[0] != '_'):
    importlib.import_module('.' + p.name.rsplit('.', 1)[0], __package__)


def twig_main(me: Twig, **kwargs):
    local_root = Path(__file__).parent

    def is_valid_file(path):
        return str(path) == CONFIGURATION_FILE or (True
            and '__pycache__' not in path.parts
            and path.is_relative_to(local_root.relative_to(directories.ROOT))
            and git.command(
                me,
                'check-ignore', '${path}',
                check=True,
                silent=True,
                path=str(path)))

    def export_command(archive, **kwargs):
        def files(me):
            return sorted(
                path.relative_to(directories.ROOT)
                for path in directories.ROOT.rglob('**/*')
                if path.is_file() and is_valid_file(
                    path.relative_to(directories.ROOT)))

        with zipfile.ZipFile(archive, mode='w') as zf:
            for rel in files(me):
                with zf.open(str(rel), mode='w') as f:
                    f.write(rel.read_bytes())

    def import_command(archive, **kwargs):
        def files(zf):
            paths = sorted(
                (directories.ROOT / i.filename).resolve()
                    .relative_to(directories.ROOT)
                for i in zf.infolist()
                if not i.is_dir())
            invalid = [
                p
                for p in paths
                if not is_valid_file(p)]
            if invalid:
                raise ValueError('invalid files: {}'.format(', '.join(
                    str(p)
                    for p in invalid)))
            else:
                return paths

        with zipfile.ZipFile(archive, mode='r') as zf:
            for rel in files(zf):
                target = directories.ROOT / rel
                with zf.open(str(rel), 'r') as f:
                    me.file(f, target)

    def list_command(**kwargs):
        def leaves(path: Path) -> List[Path]:
            if path.is_dir():
                return sorted((
                    p for p in path.iterdir()
                    if is_valid_file(p.relative_to(directories.ROOT))),
                    key=lambda p: (not p.is_dir(), p))
            else:
                return []

        def string(level: int, path: Path) -> str:
            if level == 0:
                return nest.ui.bold('Local files')
            elif path.is_dir():
                return nest.ui.ignoring(path.name)
            else:
                return path.name

        nest.ui.tree(local_root, leaves, string)

    {
        'export': export_command,
        'import': import_command,
        'list': list_command,
    }[kwargs.pop('local_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='manage local files') \
        .add_subparsers(required=True, dest='local_command')

    export_parser = actions.add_parser(
        'export',
        help='export local files to an archive')
    export_parser.add_argument(
        'archive',
        help='the target archive',
        type=Path)
    import_parser = actions.add_parser(
        'import',
        help='import local files from an archive')
    import_parser.add_argument(
        'archive',
        help='the source archive',
        type=Path)
    actions.add_parser(
        'list',
        help='list local files')

    return {
        me.name: lambda **args: twig_main(me, **args)}
