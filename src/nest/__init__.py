import difflib
import errno
import os
import shutil

from pathlib import Path
from typing import Optional


#: The nest root.
ROOT = Path(__file__).parent.parent.parent


class NestException(Exception):
    """A non-recoverable exception occurring during a run.
    """
    pass


def template(source: Path, target: Path, **kwargs):
    """Creates a new file from a template.

    All occurrences of ``'{key}'`` in the source file are replaced by
    ``kwargs['key']``.

    The target directory is created if it does not exist.

    :param source: The template file.

    :param target: The target file.
    """
    makedir(target.parent)
    target.write_text(source.read_text().format(**kwargs))


def copy(source: Path, target: Path, rel: Path, copy: bool=False):
    """Attempts to copy a file.

    This file will write a log entry.

    If the file already exists, the user is queries whether to continue.

    :param source: The source directory.
    :param target: The target directory for files.
    :param rel: The file name, relative to the source directory.
    :param copy: Whether to copy the file instead of linking.
    """
    if _changed(source, target, rel):
        ui.log(
            ui.item(ui.installing(rel)))
        _copy(source, target, rel, copy)


def makedir(path: Path):
    """Creates a directory recursively.

    :param path: The directory to create.
    """
    cause = 'directory does not exist'
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        cause = e
    if not path.is_dir():
        raise NestException(
            'failed to create directory {}: {}',
            path, cause)


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


def _copy(source: Path, target: Path, rel: Path, copy: bool):
    """Links a single file.

    :param source: The source directory.
    :param target: The target directory for files.
    :param rel: The file name, relative to the source directory.
    :param copy: Whether to copy the file instead of linking.
    """
    source = (source / rel).absolute()
    target = (target / rel).absolute()

    # Make sure the source exists
    if not source.exists() and source.is_symlink():
        raise NestException(
            'The source file {} is an invalid symlink to {}',
            source.relative_to(ROOT),
            source.readlink())

    # Make sure the target directory exists
    makedir(target.parent)

    while target.exists():
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


    if target.is_symlink():
        target.unlink()
    if copy:
        shutil.copy2(source, target)
    else:
        target.symlink_to(source.absolute())
