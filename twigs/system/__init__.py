"""Provides system packages.
"""
import re
import shlex
import shutil

from dataclasses import dataclass
from functools import partial
from typing import Any,Callable, Dict, Optional

from nest import NestException

from .. import Twig, caller_context, twig


#: A function to determine whether a package is managed by a provider.
ManagedCallback = Callable[['Self', Twig], bool]

#: A function to determine whether a package is installed.
IsInstalledCallback = Callable[['Self', Twig], bool]

#: A function to install a package.
InstallCallback = Callable[['Self', Twig], None]

#: A function to remove a package.
RemoveCallback = Callable[['Self', Twig], None]

#: The package providers.
PROVIDERS = []


@twig()
def main(me: Twig):
    me.run(*shlex.split(me.c.self_install()))


@main.checker
def is_installed(me: Twig) -> bool:
    return me.run(
        *shlex.split(me.c.self_check()),
        check=True,
        silent=True)


@main.remover
def remove(me: Twig):
    me.run(*shlex.split(me.c.self_remove()))


def package(
    *,
    package: Optional[str]=None,
    description: Optional[str]=None,
    binary: Optional[str]=None,
    globals: Optional[Dict[str, Any]]=None,
    **kwargs,
) -> Twig:
    """Defines a package twig.

    :param package: The name of the package. The actual package name can be
    overridden in the configuration.

    :param description: A description of the package.

    :param binary: The binary provided by the package. This is used to check
    whether the package exists if specified.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.

    :return: the twig
    """
    @twig(
        name=package,
        description=description,
        globals=globals or caller_context(),
        **kwargs)
    def package(me: Twig):
        try:
            _provider(me).install(me)
        except StopIteration:
            progress_re = re.compile(main.c.progress_re())
            me.run_progress(
                *shlex.split(main.c.install()),
                progress_re=progress_re,
                package=main.c.packages[me.name](me.name))

    @package.checker
    def is_installed(me: Twig) -> bool:
        try:
            return _provider(me).is_installed(me)
        except StopIteration:
            if binary is not None:
                return shutil.which(binary) is not None
            else:
                return package.run(
                    *shlex.split(main.c.check()),
                    interactive=False,
                    silent=True,
                    check=True,
                    package=main.c.packages[me.name](me.name))

    @package.remover
    def remove(me: Twig):
        if is_installed(me):
            try:
                _provider(me).remove(me)
            except StopIteration:
                me.run(
                    *shlex.split(main.c.remove()),
                    package=main.c.packages[me.name](me.name))

    return package


def provider(
        me: Twig,
        is_installed: IsInstalledCallback,
        install: InstallCallback,
        remove: RemoveCallback) -> Twig:
    """Marks a twig as a package installer.

    :param me: The currently handled twig.

    :param is_installed: A callback to determine whether a package is
    installed.

    :param install: A callback to install a package.

    :param remove: A callback to remove a package.
    """
    PROVIDERS.append(Provider(
        me,
        partial(is_installed, me),
        partial(install, me),
        partial(remove, me)))
    return me


@dataclass
class Provider:
    twig: Twig
    is_installed: IsInstalledCallback
    install: InstallCallback
    remove: RemoveCallback


def _provider(me: Twig) -> Twig:
    """Finds the provider to install a system package.

    :param me: The currently handled twig.

    :return: the twig managing the system package
    """
    providers = [
        p
        for p in PROVIDERS
        if p.twig.enabled
            and me.name in p.twig.c.packages
            and p.twig.c.packages[me.name]() is not None]
    if len(providers) > 1:
        raise NestException(
            'The twig {} is provided by several twig providers: {}\n'
            '\n'
            'Please add {} to the section [$PROVIDER.packages] without a '
            'value for the providers to ignore.',
            me.name, ', '.join(p.twig.name for p in providers), me.name)
    else:
        return next(iter(providers))
