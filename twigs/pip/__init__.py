"""Python package installer.
"""
import re
import shlex
import sys

from functools import lru_cache
from typing import Any, Dict, List, Optional

from .. import Twig, caller_context, downloadable, system, twig


#: The pip module name.
MOD = 'pip'

#: A regular expression to extract a package description from the output of
#: ``python -m pip list``
PACKAGE_EXTRACTOR = re.compile(r'([^\s]+)\s+([^\s]+)')

#: A format string to generate the URL for a package.
PACKAGE_URL_FORMAT = 'https://pypi.org/pypi/{}/json'


main = system.package()


def package(
        *,
        name: Optional[str]=None,
        globals: Optional[Dict[str, Any]]=None) -> Twig:
    """Defines a *Python pip* twig.

    This twig type requires a stored version.

    :param name: The name of the package. If not specified, the name of the
    calling module is used.

    :param description: A description of the package. If not specified, the
    docstring of the calling module is used.

    :return: the twig
    """
    @lru_cache
    def latest_version(me: Twig) -> str:
        data = me.web.json(PACKAGE_URL_FORMAT.format(me.name))
        return data['info']['version']

    @twig(
        name=name,
        globals=globals or caller_context())
    def main(me: Twig):
        _run(
            me,
            'install', '--user', '--upgrade', *args(me),
            '${package}==${version}',
            interactive=False,
            package=me.name,
            version=me.stored_version)

    @main.checker
    def is_installed(me: Twig) -> bool:
        return _installed_packages().get(me.name, None) == me.stored_version

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            _run(
                me,
                'uninstall', *args(), me.name)

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        if latest_version(me) is not None \
                and latest_version(me) != me.stored_version:
            return [latest_version(me)]
        else:
            return []

    @main.update_applier
    def update_applier(me: Twig) -> Optional[str]:
        me.stored_version = latest_version(me)
        me.install()

    def args(me: Twig) -> List[str]:
        return shlex.split(me.configuration
            .get('pip',{})
            .get('additional-arguments', ''))

    return main


def _run(me: Twig, *args: str, **kwargs: str):
    """Executes *Python pip*.

    This function ensures that the absolute path to the binary is passed, to
    ensure that it can be found without sourcing the cargo configuration file.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param args: Additional command arguments.

    :param kwargs: Additional arguments.
    """
    return me.run(
        sys.executable, '-m', MOD, *args, **kwargs)


@lru_cache
def _installed_packages() -> Dict[str, str]:
    """Lists all installed packages and their versions.

    :return: a mapping from package name to version
    """
    return {
        package.replace('_', '-'): version
        for (package, version) in (
            m.groups()
            for m in (
                PACKAGE_EXTRACTOR.match(line)
                for line in main.run(
                    sys.executable, '-m', MOD, 'list',
                    capture=True, interactive=False).splitlines())
            if m)}
