import argparse
import concurrent.futures
import difflib
import errno
import fnmatch
import os
import sys

from pathlib import Path
from typing import Generator, List, Optional, Sequence, Set

from . import (
    ROOT,
    NestException,
    platforms,
    ui,
)
from .twigs import *
from .twigs import TWIGS, Twig
from .twigs.configuration import Configuration

#: The home directory.
HOME = Path(os.path.expanduser('~/'))


def initialize():
    """Loads the configuration and initialises all twigs.
    """
    (distribution, version) = platforms.current()
    ui.log(ui.bold('Running on {}'.format(distribution)))
    print()

    configuration = Configuration(
        ROOT / '.gitmodules',
        ROOT / 'configuration.conf',
        ROOT / 'local.conf',
        distribution=distribution,
        python_version=platforms.Version(tuple(sys.version_info[:3])),
        version=version)
    for twig in TWIGS:
        twig.configuration = configuration

    enabled_twigs = [t for t in TWIGS if t.enabled]
    files = {}
    for (twig, path) in (
            (t, p)
            for t in enabled_twigs
            for p in t.files):
        ts = files.get(path, [])
        ts.append(twig.name)
        files[path] = ts

    duplicates = {
        p: ts
        for (p, ts) in files.items()
        if len(ts) > 1}

    if duplicates:
        raise NestException('Duplicate files detected: {}'.format(
            '; '.join(
                '{} for twigs {}'.format(p, ', '.join(ts))
                for p, ts in duplicates.items())))


def build(
    target: Path,
):
    initialize()

    with ui.section(ui.bold('Removing disabled twigs'), delay=True):
        for twig in reversed([t for t in TWIGS if not t.enabled]):
            twig.remove()
            with ui.section(ui.bold('Unlinking files'), delay=True):
                for filename in twig.files:
                    path = target / filename
                    if (True
                            and path.exists()
                            and path.is_symlink()
                            and path.readlink().is_relative_to(twig.source)):
                        ui.log(
                            ui.item(ui.removing(filename)))
                        _unlink(target, filename)

    enabled_twigs = [t for t in TWIGS if t.enabled]
    with ui.section(ui.bold('Installing twigs'), delay=True):
        twig_format = '{{name:{}}} - {{description}}'.format(
            max(len(t.name) for t in TWIGS if t.enabled) + len(ui.bold('')))

        for twig in enabled_twigs:
            twig.prepare()

        for twig in enabled_twigs:
            with ui.section(twig_format.format(
                    name=ui.bold(twig.name),
                    description=twig.description)):
                if not twig.present:
                    ui.log(
                        ui.installing('Installing twig...'))
                    twig.install()
                if twig.files:
                    with ui.section('Linking files', delay=True):
                        for rel in twig.files:
                            if _changed(twig.source, target, rel):
                                ui.log(
                                    ui.item(ui.installing(rel)))
                                _link(twig.source, target, rel)

        for twig in reversed(enabled_twigs):
            twig.complete()


def clean(
    target: Path,
    force: bool,
):
    initialize()

    with ui.section(ui.bold('Cleaning deprecated files')):
        for (link, target) in _links_to(_list_files(target), ROOT):
            rel = target.relative_to(ROOT)
            if not target.is_file():
                ui.log(
                    ui.item((ui.removing('{} has been removed'.format(rel)))))
            else:
                continue
            response = ui.query(
                'Remove {} from computer?'.format(link),
                'yes', 'no') if not force else 0
            if response == 0:
                try:
                    link.unlink()
                except OSError:
                    ui.log('Failed to remove file!')
            elif response is None:
                ui.log('Not removing as we are not running in a terminal.')


def dependencies(
    invert: bool,
    twigs: List[Twig],
):
    initialize()

    if not twigs:
        twigs = list(sorted(TWIGS, key=lambda t: t.name))

    if invert:
        ui.log(ui.bold('Dependents for twigs:'))
        def leaves(twig: Optional[Twig]) -> List[Twig]:
            return [
                t for t in TWIGS
                if any(d.name == twig.name
                    for d in t.dependencies)]
    else:
        ui.log(ui.bold('Dependencies for twigs:'))
        def leaves(twig: Optional[Twig]) -> List[Twig]:
            return list(twig.dependencies)

    def string(level: int, twig: Twig) -> str:
        if level == 0:
            return ui.item(ui.bold(twig.name))
        else:
            return ui.ignoring(twig.name)

    for twig in twigs:
        ui.tree(twig, leaves, string)


def update(
    apply: bool,
):
    initialize()

    enabled_twigs = [t for t in TWIGS if t.enabled]
    with ui.section(ui.bold('Updates for twigs'), delay=True):
        with concurrent.futures.ThreadPoolExecutor() as e:
            tasks = {
                e.submit(lambda t: t.updates, twig): twig
                for twig in enabled_twigs}
            for task in concurrent.futures.as_completed(tasks):
                twig = tasks[task]
                updates = task.result()
                with ui.section('{name} - {description}'.format(
                        name=ui.bold(twig.name),
                        description=twig.description), delay=True):
                    for update in updates:
                        ui.log(ui.item(update))

    if apply:
        with ui.section(ui.bold('Updating twigs'), delay=True):
            print()
            for twig in (t for t in enabled_twigs if len(t.updates) > 0):
                with ui.section(ui.item('Updating {}...'.format(
                        ui.bold(twig.name)))):
                    instructions = twig.update()
                    if instructions is not None:
                        ui.log(instructions)


def _changed(source: Path, target: Path, rel: Path) -> bool:
    """Determines whether a file has been changed.

    :param source: The source directory.

    :param target: The target directory for files.

    :param rel: The file name, relative to the source directory.

    :return: whether the file has changed
    """
    source = (source / rel).absolute()
    target = (target / rel).absolute()

    if not target.exists():
        # The file is changed if it has not yet been copied
        return True

    else:
        # The target file must be a symlink pointing to the source file
        return not target.is_symlink() or target.readlink() != source


def _link(source: Path, target: Path, rel: Path):
    """Links a single file.

    :param source: The source directory.

    :param target: The target directory for files.

    :param rel: The file name, relative to the source directory.
    """
    source = (source / rel).absolute()
    target = (target / rel).absolute()

    # Make sure the target directory exists
    try:
        os.makedirs(target.parent)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    while target.exists() or target.is_symlink():
        r = ui.query(
            '{} already exists. Overwrite? '.format(target),
             'yes', 'no', 'diff')
        if r is None:
            return
        elif r == 0:
            target.unlink()
            break
        elif r == 1:
            return
        elif r == 2:
            with open(source, encoding='utf-8') as f:
                sdata = f.readlines()
            try:
                with open(target, encoding='utf-8') as f:
                    tdata = f.readlines()
            except FileNotFoundError:
                # The target file may be an invalid link
                tdata = ''
            for line in difflib.unified_diff(
                    sdata, tdata, fromfile=str(source), tofile=str(target)):
                if line[0] == '+':
                    ui.log(ui.installing(line.rstrip()))
                elif line[0] == '-':
                    ui.log(ui.removing(line.rstrip()))
                else:
                    ui.log(line.rstrip())


    target.symlink_to(source.absolute())


def _unlink(target: Path, rel: Path):
    """Unlinks a single file.

    :param target: The target directory for files.

    :param rel: The file name, relative to the source directory.
    """
    try:
        (target / rel).unlink()
    except FileNotFoundError:
        pass


def _list_files(target: Path) -> Generator[Path, None, None]:
    """Lists all files in a directory.

    :param target: The target directory for files.

    :return: a generator of paths
    """
    for (root, dirs, files) in os.walk(target):
        root = Path(root)
        yield from (
            path
            for path in (root / f for f in files))


def _links_to(
    files: Sequence[Path],
    target: Path,
) -> Generator[str, None, None]:
    """Filters a sequence of files so that only those that are links to files
    under ``target`` remain.

    :param files: A sequence of file names that.

    :param target: The target directory for files.
    """
    def is_symlink(p):
        try:
            return p.is_symlink()
        except OSError:
            ui.log('Failed to determine whether {} is a symlink!'.format(
                ui.removing(p)))
            return False

    def readlink(p):
        try:
            return p.readlink()
        except OSError:
            ui.log('Failed to read target of link {}!'.format(
                ui.removing(p)))

    links = (
        p
        for p in files
        if is_symlink(p))
    link_and_target = (
        (p, readlink(p))
        for p in links)
    return (
        (s, t)
        for (s, t) in link_and_target
        if t is not None and t.is_relative_to(target))


if __name__ == '__main__':
    def _wrap(f):
        def inner(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except Exception as e:
                raise ValueError(str(e))
        return inner

    parser = argparse.ArgumentParser(
        prog='nest',
        description='Installs packages, applications and and dotfiles')
    actions = parser.add_subparsers(required=True, dest='command')

    build_parser = actions.add_parser(
        'build',
        help='Removes all disabled twigs and installs all enabled twigs')
    build_parser.add_argument(
        '--target',
        help='The target directory.',
        type=Path,
        default=HOME)

    clean_parser = actions.add_parser(
        'clean',
        help='Removes all dangling links into this directory from the user '
        'home directory.')
    clean_parser.add_argument(
        '--target',
        help='The target directory.',
        type=Path,
        default=HOME)
    clean_parser.add_argument(
        '--force',
        help='Whether to force removal of files without querying.',
        action='store_true')

    dependencies_parser = actions.add_parser(
        'dependencies',
        help='Lists all twigs and their dependencies.')
    dependencies_parser.add_argument(
        '--invert',
        help='Invert the tree to show dependents',
        action='store_true')
    dependencies_parser.add_argument(
        'twigs',
        help='The twigs to list; leave empty to list all.',
        type=_wrap(lambda s: next(t for t in TWIGS if t.name == s)),
        nargs='*')

    update_parser = actions.add_parser(
        'update',
        help='Manages updates for twigs.')
    update_parser.add_argument(
        '--apply',
        action='store_true',
        dest='apply',
        help='Apply the updates.')

    handlers = {
        'build': build,
        'clean': clean,
        'dependencies': dependencies,
        'update': update,
    }

    for twig in (t for t in TWIGS if t.enabled):
        handlers.update(twig.list_actions(actions))

    try:
        arguments = vars(parser.parse_args())
        handlers[arguments.pop('command')](**arguments)
    except NestException as e:
        sys.stderr.write('An unexpected error occurred: {}\n'.format(
            e.args[0].format(*e.args[1:])))
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print('Cancelled')
