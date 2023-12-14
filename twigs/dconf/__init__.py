"""Simple configuration storage system.
"""

import os

from typing import Any, Sequence

from nest import ui
from .. import Twig, run, system


main = system.package()


def list(name: str, path: str) -> Sequence[str]:
    """Lists all keys under a path.

    Any directory items will have a ``'/'`` suffix.

    :param name: The name of the twig running the command. This will be used
    to print an error message if the command fails.

    :param path: The path to list. This must start and end with ``'/'``.

    :return: a list of items
    """
    return (
        item.rstrip()
        for item in _run(
            name,
            'list', path,
            capture=True,
            interactive=False).splitlines()
        if item.strip())


def read(name: str, path: str) -> str:
    """Reads a specific key.

    :param name: The name of the twig running the command. This will be used
    to print an error message if the command fails.

    :param path: The path to read. This must start with ``'/'``.

    :return: a value
    """
    return _run(
        name,
        'read', path,
        capture=True,
        interactive=False).strip()


def write(name: str, path: str, value: str) -> str:
    """Writes a specific key.

    :param name: The name of the twig running the command. This will be used
    to print an error message if the command fails.

    :param path: The path to read. This must start with ``'/'``.

    :param value: The value to write. This must be in a *GVariant* format.

    :return: a value
    """
    return _run(
        name,
        'write', path, value,
        interactive=False)


def reset(name: str, path: str):
    """Resets a specific path.

    :param name: The name of the twig running the command. This will be used
    to print an error message if the command fails.

    :param path: The path to read. This must start with ``'/'``.
    """
    return _run(
        name,
        'reset', '-f', path,
        interactive=False)


def _run(name: str, *args: str, **kwargs: str) -> Any:
    """Runs dconf with apecific arguments.

    :param name: The name of the twig running the command. This will be used
    to print an error message if the command fails.

    :param args: Additional command arguments.

    :param kwargs: Additional arguments.

    :return: a value depending on the arguments and the execution
    """
    if not 'DISPLAY' in os.environ:
        ui.log(ui.removing('Cannot run dconf without $DISPLAY set'))
        return ''
    else:
        try:
            return run(
                name,
                'dconf', *args, **kwargs)
        except FileNotFoundError:
            return ''
