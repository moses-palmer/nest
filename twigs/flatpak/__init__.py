"""Application deployment framework for desktop apps.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from .. import Twig, caller_context, system, twig


def _is_installed(me: Twig, flatpak: Twig) -> bool:
    """Returns whether a flatpak is present on the system.

    :param me: This twig.
    :param flatpak: The flatpak twig.

    :returns: whether the flatpak exists
    """
    return flatpak.run(
        'flatpak', 'info', '${flatpak}',
        check=True,
        silent=True,
        flatpak=me.configuration.flatpak.packages[flatpak.name]())


def _install(me: Twig, flatpak: Twig):
    """Installs a flatpak.

    :param me: This twig.
    :param flatpak: The flatpak twig.
    """
    flatpak.run(
        'flatpak', 'install', '--user', '--assumeyes', '${flatpak}',
        check=True,
        silent=True,
        flatpak=me.configuration.flatpak.packages[flatpak.name]())


def _remove(me: Twig, flatpak: Twig):
    """Removes a flatpak.

    :param me: This twig.
    :param flatpak: The flatpak twig.
    """
    flatpak.run(
        'flatpak', 'uninstall', '--user', '--assumeyes', '--app=${flatpak}',
        check=True,
        silent=True,
        flatpak=me.configuration.flatpak.packages[flatpak.name]())


main = system.provider(system.package(), _is_installed, _install, _remove)


def remote(
        *,
        name: Optional[str]=None,
        url=str,
        globals: Optional[Dict[str, Any]]=None,
        **kwargs) -> Twig:
    """Defines a Flatpak remote.

    :param name: The name to use for this remote.

    :param url: The URL.
    """
    @twig(
        name=name,
        globals=globals or caller_context(),
        **kwargs)
    def main(me: Twig):
        me.run(
            'flatpak', 'remote-add', '--user', '--if-not-exists', '${name}',
            '${url}',
            silent=True,
            name=me.name,
            url=url)
        _remotes.cache_clear()

    @main.checker
    def is_installed(me: Twig) -> bool:
        global main
        return main.present and _remotes(me).get(me.name, None) is not None

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            me.run(
                'flatpak', 'remote-delete', '${name}',
                silent=True,
                name=me.name)
            _remotes.cache_clear()

    return main


flathub = remote(
    name='flathub',
    description='Apps for Linux.',
    url='https://flathub.org/repo/flathub.flatpakrepo').depends(main)


@lru_cache
def _remotes(me: Twig) -> Dict[str, str]:
    """Generates a mapping from repository name to its URL.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :return: a mapping from name to URL
    """
    return dict(
        line.split(maxsplit=1)
        for line in me.run(
            'flatpak', 'remotes', '--columns=name,url',
            capture=True).splitlines()
        if line)

