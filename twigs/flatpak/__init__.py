"""Application deployment framework for desktop apps.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from .. import Twig, caller_context, system, twig


main = system.package()


def remote(
        *,
        name: Optional[str]=None,
        url=str,
        globals: Optional[Dict[str, Any]]=None) -> Twig:
    """Defines a Flatpak remote.

    :param name: The name to use for this remote.

    :param url: The URL.
    """
    @twig(
        name=name,
        globals=globals or caller_context())
    def main(me: Twig):
        _run(
            me,
            'remote-add', '--user', '${name}', '${url}',
            name=me.name, url=url)

    @main.checker
    def is_installed(me: Twig) -> bool:
        return _remotes(me).get(me.name, None) == url

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            _run(
                me,
                'remote-delete', me.name)

    return main


def application(
        *,
        remote: Twig,
        name: Optional[str]=None,
        application: str,
        globals: Optional[Dict[str, Any]]=None) -> Twig:
    """A flatpak.

    :param remote: The remote from which this application comes.

    :param name: A short name.

    :param application: The flatpak name.
    """
    @lru_cache
    def info():
        return dict(
            line.strip().lower().split(':', 1)
            for line in _run(
                me,
                'info', '${application}',
                capture=True,
                application=application)
            if ': ' in line)

    @twig(
        name=name,
        globals=globals or caller_context())
    def main(me: Twig):
        _run(
            me,
            'install', '--user', '--assumeyes', application)

    @main.checker
    def is_installed(me: Twig) -> bool:
        return _run(
            me,
            'info', '${application}',
            check=True,
            silent=True,
            application=application)

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        try:
            line = next(
                line
                for line in _run(
                    me,
                    'remote-ls', '${remote}', '--updates',
                    '--columns=application,version',
                    capture=True,
                    remote=remote.name)
                if line.startswith(package))
            _, *result = line.split()
            return result if result else ['new']
        except StopIteration:
            return []

    @main.update_applier
    def update_applier(me: Twig):
        _run(
            me,
            'update', '--app=${application}',
            application=application)

    @main.remover
    def remover(me: Twig):
        if is_installed(me):
            _run(
                me,
                'uninstall', '--app=${application}',
                application=application)


def _run(me: Twig, *args, **kwargs) -> Any:
    """Runs the ``flatpak`` command.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param args: Any arguments.

    :param kwargs: Any key word arguments.
    """
    return me.run('flatpak', *args, **kwargs)


@lru_cache
def _remotes(me: Twig) -> Dict[str, str]:
    """Generates a mapping from repository name to its URL.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :return: a mapping from name to URL
    """
    return dict(
        line.split(maxsplit=1)
        for line in _run(
            me,
            'remotes', '--columns=name,url',
            capture=True).splitlines())

