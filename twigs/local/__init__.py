"""Local files for this computer only.
"""

import importlib
import os
import tempfile
import zipfile

from argparse import _SubParsersAction
from itertools import chain
from pathlib import Path
from typing import List

import nest
import nest.ui
from .. import Twig, ROOT, git


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
            and path.is_relative_to(local_root.relative_to(ROOT))
            and git.command(
                me,
                'check-ignore', '${path}',
                check=True,
                silent=True,
                path=str(path)))

    def export_command(archive, **kwargs):
        def files(me):
            return sorted(
                path.relative_to(ROOT)
                for path in ROOT.rglob('**/*')
                if path.is_file() and is_valid_file(path.relative_to(ROOT)))

        with zipfile.ZipFile(archive, mode='w') as zf:
            for rel in files(me):
                with zf.open(str(rel), mode='w') as f:
                    f.write(rel.read_bytes())

    def import_command(archive, **kwargs):
        def files(zf):
            paths = sorted(
                (ROOT / f).resolve().relative_to(ROOT)
                for f in zf.namelist())
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
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                for rel in files(zf):
                    target = root / rel
                    nest.makedir(target.parent)
                    with zf.open(str(rel), 'r') as f:
                        target.write_bytes(f.read())
                    nest.copy(root, ROOT, rel, copy=True)

    def list_command(**kwargs):
        def leaves(path: Path) -> List[Path]:
            if path.is_dir():
                return sorted((
                    p for p in path.iterdir()
                    if is_valid_file(p.relative_to(ROOT))),
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
    actions = actions.add_parser(me.name, help='Manages local files.') \
        .add_subparsers(required=True, dest='local_command')

    export_parser = actions.add_parser(
        'export',
        help='Exports local files to an archive')
    export_parser.add_argument(
        'archive',
        help='the target archive',
        type=Path)
    import_parser = actions.add_parser(
        'import',
        help='Imports local files from an archive')
    import_parser.add_argument(
        'archive',
        help='the source archive',
        type=Path)
    actions.add_parser(
        'list',
        help='Lists local files')

    return {
        me.name: lambda **args: twig_main(me, **args)}




