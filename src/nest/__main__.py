import argparse
import concurrent.futures
import fnmatch
import os
import subprocess
import sys

from pathlib import Path
from typing import Generator, List, Optional, Sequence, Set

from . import (
    ROOT,
    NestException,
    directories,
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

    try:
        configuration = Configuration(
            directories.ROOT / '.gitmodules',
            directories.ROOT / 'configuration.conf',
            distribution=distribution,
            python_version=platforms.Version(tuple(sys.version_info[:3])),
            version=version)
    except ValueError as e:
        sys.stderr.write('Invalid configuration: {}'.format(e))
        sys.exit(1)
    for twig in TWIGS:
        twig.configuration = configuration

    enabled_twigs = [t for t in TWIGS if t.enabled]
    files = {}
    for (twig, path) in (
            (t, p)
            for t in enabled_twigs
            for p in t.user_files):
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
    with ui.section(ui.bold('Removing disabled twigs'), delay=True):
        for twig in reversed([t for t in TWIGS if not t.enabled]):
            twig.remove()
            with ui.section(ui.bold('Unlinking files'), delay=True):
                for rel in twig.user_files:
                    ui.unlink(twig, twig.user_source, directories.HOME, rel)
                for rel in twig.system_files:
                    ui.unlink(
                        twig, twig.system_source, twig.system_source.root, rel)

    enabled_twigs = [t for t in TWIGS if t.enabled]
    with ui.section(ui.bold('Installing twigs'), delay=True):
        twig_format = '{{name:{}}} - {{description}}'.format(
            max(len(t.name) for t in TWIGS if t.enabled) + len(ui.bold('')))
        twig_format_no_format = '{{name:{}}} - {{description}}'.format(
            max(len(t.name) for t in TWIGS if t.enabled))

        for twig in enabled_twigs:
            header = twig_format.format(
                name=ui.bold(twig.name),
                description=twig.description)
            header_no_format = twig_format_no_format.format(
                name=twig.name,
                description=twig.description)
            with ui.section(header, length=len(header_no_format)):
                if not twig.present:
                    ui.log(ui.installing('Installing twig...'))
                    twig.install()
                with ui.section('Linking files', delay=True):
                    for rel in twig.user_files:
                        ui.link(twig, twig.user_source, target, rel)
                    for rel in twig.system_files:
                        ui.link(
                            twig, twig.system_source, twig.system_source.root,
                            rel)

        for twig in reversed(enabled_twigs):
            twig.complete()


def clean(
    target: Path,
    force: bool,
):
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
    enabled_twigs = [t for t in TWIGS if t.enabled]
    updates_for_twigs = {}
    with ui.section(ui.bold('Updates for twigs'), delay=True):
        with concurrent.futures.ThreadPoolExecutor() as e:
            tasks = {
                e.submit(lambda t: t.updates, twig): twig
                for twig in enabled_twigs}
            for task in concurrent.futures.as_completed(tasks):
                twig = tasks[task]
                updates = task.result()
                if updates:
                    updates_for_twigs[twig.name] = updates
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
        subprocess.check_call(
            ['git', 'add', 'twigs'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent.parent.parent)
        try:
            subprocess.check_call(
                ['git', 'commit', '--message=Update twigs\n\n'
                    + '\n\n'.join(
                        '{}\n{}'.format(twig, '\n'.join(
                            ' • {}'.format(update)
                            for update in updates))
                        for (twig, updates) in sorted(
                            updates_for_twigs.items(),
                            key=lambda a: a[0]))],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=Path(__file__).parent.parent.parent)
        except subprocess.CalledProcessError:
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

    return (
        (s, t)
        for (s, t) in (
            (p, readlink(p))
            for p in (
                p
                for p in files
                if is_symlink(p)))
        if t is not None and t.is_relative_to(target))


if __name__ == '__main__':
    def _wrap(f, exc=ValueError):
        def inner(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except Exception as e:
                if isinstance(e, exc):
                    raise
                else:
                    raise exc(str(e))
        return inner

    parser = argparse.ArgumentParser(
        prog='nest',
        description='Install packages, applications and dotfiles')
    actions = parser.add_subparsers(required=True, dest='command')

    build_parser = actions.add_parser(
        'build',
        help='remove all disabled twigs and installs all enabled twigs')
    build_parser.add_argument(
        '--target',
        help='the target directory',
        type=Path,
        default=HOME)

    clean_parser = actions.add_parser(
        'clean',
        help='remove all dangling links into this directory from the user '
        'home directory')
    clean_parser.add_argument(
        '--target',
        help='the target directory',
        type=Path,
        default=HOME)
    clean_parser.add_argument(
        '--force',
        help='whether to force removal of files without querying',
        action='store_true')

    dependencies_parser = actions.add_parser(
        'dependencies',
        help='list all twigs and their dependencies')
    dependencies_parser.add_argument(
        '--invert',
        help='invert the tree to show dependents',
        action='store_true')
    dependencies_parser.add_argument(
        'twigs',
        help='the twigs to list; leave empty to list all',
        type=_wrap(lambda s: next(t for t in TWIGS if t.name == s)),
        nargs='*')

    update_parser = actions.add_parser(
        'update',
        help='manage updates for twigs')
    update_parser.add_argument(
        '--apply',
        action='store_true',
        dest='apply',
        help='apply the updates')

    handlers = {
        'build': build,
        'clean': clean,
        'dependencies': dependencies,
        'update': update,
    }

    for twig in (t for t in TWIGS if t.enabled):
        handlers.update(**{
            command: _wrap(handler, NestException)
            for (command, handler) in twig.list_actions(actions).items()})

    try:
        initialize()
        arguments = vars(parser.parse_args())
        handlers[arguments.pop('command')](**arguments)
    except NestException as e:
        sys.stderr.write('An unexpected error occurred: {}\n'.format(
            e.args[0].format(*e.args[1:])))
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print('Cancelled')
