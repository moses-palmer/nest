"""Simple configuration storage system.
"""

import os

from typing import Any, Sequence

from nest import ui
from .. import Twig, system


main = system.package()


def list(me: Twig, path: str) -> Sequence[str]:
    """Lists all keys under a path.

    Any directory items will have a ``'/'`` suffix.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param path: The path to list. This must start and end with ``'/'``.

    :return: a list of items
    """
    return (
        item.rstrip()
        for item in _run(
            me,
            'list', path,
            capture=True,
            interactive=False).splitlines()
        if item.strip())


def read(me: Twig, path: str) -> str:
    """Reads a specific key.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param path: The path to read. This must start with ``'/'``.

    :return: a value
    """
    return _run(
        me,
        'read', path,
        capture=True,
        interactive=False).strip()


def write(me: Twig, path: str, value: str) -> str:
    """Writes a specific key.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param path: The path to read. This must start with ``'/'``.

    :param value: The value to write. This must be in a *GVariant* format.

    :return: a value
    """
    return _run(
        me,
        'write', path, value,
        interactive=False)


def reset(me: Twig, path: str):
    """Resets a specific path.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param path: The path to read. This must start with ``'/'``.
    """
    return _run(
        me,
        'reset', '-f', path,
        interactive=False)


def _run(me: Twig, *args: str, **kwargs: str) -> Any:
    """Runs dconf with apecific arguments.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param args: Additional command arguments.

    :param kwargs: Additional arguments.

    :return: a value depending on the arguments and the execution
    """
    if not 'DISPLAY' in os.environ:
        ui.log(ui.removing('Cannot run dconf without $DISPLAY set'))
        return ''
    else:
        try:
            return me.run(
                'dconf', *args, **kwargs)
        except FileNotFoundError:
            return ''
