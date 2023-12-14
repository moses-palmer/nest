import shlex
import shutil

from typing import Optional

from .. import Twig, caller_context, twig


def package(
        *,
        package: Optional[str]=None,
        description: Optional[str]=None,
        binary: Optional[str]=None) -> Twig:
    """Defines a package twig.

    :param package: The name of the package. The actual package name can be
    overridden in the configuration.

    :param binary: The binary provided by the package. This is used to check
    whether the package exists if specified.

    :param description: A description of the package.
    """
    @twig(
        name=package,
        description=description,
        globals=caller_context())
    def main(me: Twig):
        install(me)

    @main.checker
    def package_is_installed(me: Twig) -> bool:
        if binary is not None:
            return is_installed(me, binary)
        else:
            return me.run(
                *shlex.split(me.configuration['commands']['package_check']),
                interactive=False,
                silent=True,
                check=True,
                package=me.configuration.get('package_names', {}).get(
                    me.name, me.name))

    @main.remover
    def package_remove(me: Twig):
        if package_is_installed(me):
            remove(me)

    return main


def install(me: Twig):
    """Installs a package.

    :param me: The currently handled twig.
    """
    me.run(
        *shlex.split(me.configuration['commands']['package_install']),
        package=me.configuration.get('package_names', {}).get(
            me.name, me.name))


def is_installed(me: Twig, name: str) -> bool:
    """Returns whether a binary with a specific name is present on the system.

    :param me: The currently handled twig.

    :param name: The binary name.

    :returns: whether the binary exists
    """
    return shutil.which(name) is not None


def remove(me: Twig):
    """Removes a package.

    :param me: The currently handled twig.
    """
    me.run(
        *shlex.split(me.configuration['commands']['package_remove']),
        package=me.configuration.get('package_names', {}).get(
            me.name, me.name))
