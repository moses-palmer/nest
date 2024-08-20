"""Daemon and tooling that enable snap packages.
"""
import shlex
import shutil

from typing import Optional

from .. import Twig, caller_context, system, twig


def _is_installed(me: Twig, package: Twig) -> bool:
    """Returns whether a snap is present on the system.

    :param me: This twig.
    :param package: The package twig.

    :returns: whether the package exists
    """
    return package.run(
        'snap', 'list', '${snap}',
        check=True,
        silent=True,
        snap=_name(package))


def _install(me: Twig, package: Twig):
    """Installs a snap.

    :param me: This twig.
    :param package: The package twig.
    """
    if not _is_installed(me, package):
        if main.c.packages[package.name].classic() == 'true':
            package.run(
                'sudo', 'snap', 'install', '--classic', '${snap}',
                check=True,
                silent=True,
                snap=_name(package))
        else:
            package.run(
                'sudo', 'snap', 'install', '${snap}',
                check=True,
                silent=True,
                snap=_name(package))


def _remove(me: Twig, package: Twig):
    """Removes a snap.

    :param me: This twig.
    :param package: The package twig.
    """
    package.run(
        'sudo', 'snap', 'remove', '${snap}',
        check=True,
        silent=True,
        snap=_name(package))


def _name(package: Twig) -> str:
    """The name of the snap for a specific twig.

    :param package: The package twig.
    """
    return main.c.packages[package.name].name() or package.name


main = system.provider(system.package(), _is_installed, _install, _remove)
