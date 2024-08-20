"""Daemon and tooling that enable snap packages.
"""
import shlex
import shutil

from typing import Optional

from .. import Twig, caller_context, system, twig


def _is_installed(me: Twig, snap: Twig) -> bool:
    """Returns whether a snap is present on the system.

    :param me: This twig.
    :param snap: The snap twig.

    :returns: whether the snap exists
    """
    return snap.run(
        'snap', 'list', '${snap}',
        check=True,
        silent=True,
        snap=snap.name)


def _install(me: Twig, snap: Twig):
    """Installs a snap.

    :param me: This twig.
    :param snap: The snap twig.
    """
    if not _is_installed(me, snap):
        if me.configuration.snap.packages[snap.name].classic() == 'true':
            snap.run(
                'sudo', 'snap', 'install', '--classic', '${snap}',
                check=True,
                silent=True,
                snap=snap.name)
        else:
            snap.run(
                'sudo', 'snap', 'install', '${snap}',
                check=True,
                silent=True,
                snap=snap.name)


def _remove(me: Twig, snap: Twig):
    """Removes a snap.

    :param me: This twig.
    :param snap: The snap twig.
    """
    snap.run(
        'sudo', 'snap', 'remove', '${snap}',
        check=True,
        silent=True,
        snap=me.name)


main = system.provider(system.package(), _is_installed, _install, _remove)
