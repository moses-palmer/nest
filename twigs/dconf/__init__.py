"""Simple configuration storage system.
"""

import os
import re

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

from .. import Twig, caller_context, system, twig


main = system.package()


@dataclass
class KeyBinding:
    """A global key binding.
    """
    #: The path to custom key bindings.


    #: The name of the binding.
    name: str

    #: The actual binding.
    binding: str

    #: The command to execute.
    command: str


def keybindings(
        *bindings: KeyBinding,
        name: Optional[str]=None,
        globals: Optional[Dict[str, Any]]=None) -> Twig:
    """Defines a *key binding* twig.

    This twig will ensure that a set of global GNOME key bindings exist.
    """
    path = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings'
    custom_bindings_re = re.compile(r'custom([0-9]+)')

    @twig(
        name=name,
        globals=globals or caller_context())
    def main(me: Twig):
        for binding in list_missing(me):
            index = max(
                (
                    int(custom_bindings_re.match(binding).group(1))
                    for binding in list(me, '{}/'.format(path))
                    if custom_bindings_re.match(binding)),
                default=0) + 1
            base = '{}/custom{}'.format(path, index)
            write(me, '{}/name'.format(base), binding.name)
            write(me, '{}/binding'.format(base), binding.binding)
            write(me, '{}/command'.format(base), binding.command)

    @main.checker
    def is_installed(me: Twig):
        return len(list_missing(me)) == 0

    @main.completer
    def complete(me: Twig):
        write(me, path, '[{}]'.format(
            ','.join(
                '\'{}/{}\''.format(path, name)
                for name in list(me, '{}/'.format(path)))))

    @main.remover
    def remove(me: Twig):
        for item in list(me, '{}/'.format(path)):
            subpath = '{}/{}'.format(path, item)
            name = read(me, '{}name'.format(subpath))
            if any(name == binding.name for binding in bindings):
                reset(me, subpath)

    def list_missing(me):
        current_names = [
            read(me, '{}/{}name'.format(path, binding))
            for binding in list(me, '{}/'.format(path))]
        return [
            binding
            for binding in bindings
            if binding.name not in current_names]

    return main


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
        return ''
    else:
        try:
            return me.run(
                'dconf', *args, **kwargs)
        except FileNotFoundError:
            return ''
