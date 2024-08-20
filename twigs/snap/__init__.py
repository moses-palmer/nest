"""Daemon and tooling that enable snap packages.
"""
import shlex
import shutil

from typing import Optional

from .. import Twig, caller_context, system, twig


main = system.package()


def package(
        *,
        snap: Optional[str]=None,
        description: Optional[str]=None,
        binary: Optional[str]=None,
        classic: bool=False) -> Twig:
    """Defines a snap twig.

    :param snap: The name of the snap.

    :param description: A description of the snap.

    :param binary: The binary provided by the snap. This is used to check
    whether the snap exists if specified.

    :param classic: Whether to install the snap as a classic snap.
    """
    @twig(
        name=snap,
        description=description,
        globals=caller_context())
    def main(me: Twig):
        install(me, classic)

    @main.checker
    def snap_is_installed(me: Twig) -> bool:
        if binary is not None:
            return system.is_installed(me, binary)
        else:
            return is_installed(me, me.name)

    @main.remover
    def snap_remove(me: Twig):
        if snap_is_installed(me):
            remove(me)

    return main


def install(me: Twig, classic: bool):
    """Installs a package.

    :param me: The currently handled twig.

    :param classic: Whether to install the snap as a classic snap.
    """
    if classic:
        me.run(
            'snap', 'install', '--classic', me.name)
    else:
        me.run(
            'snap', 'install', me.name)


def is_installed(me: Twig, name: str) -> bool:
    """Returns whether a binary with a specific name is present on the system.

    :param me: The currently handled twig.

    :param name: The binary name.

    :returns: whether the binary exists
    """
    return me.run('snap', 'info', name, check=True)


def remove(me: Twig):
    """Removes a snap.

    :param me: The currently handled twig.
    """
    me.run(
        'snap', 'remove', me.name)
