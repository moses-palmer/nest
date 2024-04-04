"""Application deployment framework for desktop apps.
"""

import os
import shlex

import nest

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from nest import directories

from .. import Twig, caller_context, system, twig


#: The base path for flatpaks.
BASE_PATH = directories.VAR / 'app'


def _is_installed(me: Twig, flatpak: Twig) -> bool:
    """Returns whether a flatpak is present on the system.

    :param me: This twig.
    :param flatpak: The flatpak twig.

    :returns: whether the flatpak exists
    """
    binary = _binary(me, flatpak)

    return flatpak.run(
        'flatpak', 'info', '${flatpak}',
        check=True,
        silent=True,
        flatpak=me.c.packages[flatpak.name].ref()) \
        and binary.exists() \
        and all(t.exists() for t in _links(me, flatpak))


def _install(me: Twig, flatpak: Twig):
    """Installs a flatpak.

    :param me: This twig.
    :param flatpak: The flatpak twig.
    """
    binary = _binary(me, flatpak)

    flatpak.run(
        'flatpak', 'install', '--user', '--assumeyes', '${flatpak}',
        check=True,
        silent=True,
        flatpak=_ref(me, flatpak))

    for target, source in _links(me, flatpak).items():
        target.unlink(missing_ok=True)
        nest.makedir(source.parent)
        nest.makedir(target.parent)
        target.symlink_to(source)

    with open(binary, 'w', encoding='utf-8') as f:
        f.write(r'''#!/bin/sh
flatpak run --user \
    {} \
    {} "$@"
'''.format(
    ' '.join(
        '--env={}={}'.format(k, shlex.quote(v))
        for (k, v) in _env(me, flatpak).items()),
    _ref(me, flatpak)))
    binary.chmod(0o770)


def _remove(me: Twig, flatpak: Twig):
    """Removes a flatpak.

    :param me: This twig.
    :param flatpak: The flatpak twig.
    """
    binary = _binary(me, flatpak)

    flatpak.run(
        'flatpak', 'uninstall', '--user', '--assumeyes', '--app=${flatpak}',
        check=True,
        silent=True,
        flatpak=_ref(me, flatpak))
    binary.unlink(missing_ok=True)


main = system.provider(system.package(), _is_installed, _install, _remove)


@main.completer
def completer(me: Twig) -> List[str]:
    me.run(
        'flatpak', 'update', '--user', '--noninteractive',
        silent=True)


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
    def remote(me: Twig):
        me.run(
            'flatpak', 'remote-add', '--user', '--if-not-exists', '${name}',
            '${url}',
            silent=True,
            name=me.name,
            url=url)
        _remotes.cache_clear()

    @remote.checker
    def is_installed(me: Twig) -> bool:
        return main.present and me.name in _remotes(me)

    @remote.remover
    def remove(me: Twig):
        if is_installed(me):
            me.run(
                'flatpak', 'remote-delete', '${name}',
                silent=True,
                name=me.name)
            _remotes.cache_clear()

    return remote


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


def _ref(me: Twig, flatpak: Twig) -> str:
    """The flatpak package reference.

    :param me: This twig.
    :param flatpak: The flatpak twig.

    :return: a ref
    """
    return me.c.packages[flatpak.name].ref()


def _binary(me: Twig, flatpak: Twig):
    """The path to the binary used to launch this app.

    :param me: This twig.
    :param flatpak: The flatpak twig.

    :return: a path
    """
    return directories.BIN / flatpak.name


def _links(me: Twig, flatpak: Twig) -> Dict[Path, Path]:
    """The paths to additional files that should be present in the flatpak
    directory.

    The keys are targets in the flatpak directory, and the values are external
    absolute paths.

    :param me: This twig.
    :param flatpak: The flatpak twig.

    :return: a link mapping
    """
    return dict(
        (
            BASE_PATH / _ref(me, flatpak) /  Twig.interpolate(k, os.getenv),
            Path(Twig.interpolate(
                me.c.packages[flatpak.name].links[k](),
                os.getenv,
            )).resolve(),
        )
        for k in me.c.packages[flatpak.name].links)


def _env(me: Twig, flatpak: Twig) -> Dict[Path, Path]:
    """The environment overrides for a flatpak.

    :param me: This twig.
    :param flatpak: The flatpak twig.

    :return: the environment overrides
    """
    environment = me.c.packages[flatpak.name].env() or {}
    return dict(
        (k, me.c.packages[flatpak.name].env[k]())
        for k in environment)
