"""Python package installer.
"""
import re
import shlex
import sys

from argparse import _SubParsersAction
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .. import (
    Twig,
    as_mod,
    caller_context,
    downloadable,
    normalize,
    system,
    twig,
)


#: The pip module name.
MOD = 'pip'

#: A regular expression to extract the progress from pip install.
INSTALL_PROGRESS = re.compile(r'Progress (?P<current>\d+) of (?P<max>\d+)')

#: A regular expression to extract a package description from the output of
#: ``python -m pip list``
PACKAGE_EXTRACTOR = re.compile(r'([^\s]+)\s+([^\s]+)')

#: A format string to generate the URL for a package.
PACKAGE_URL_FORMAT = 'https://pypi.org/pypi/{}/json'


main = system.package()


def package(
    *,
    package: Optional[str]=None,
    description: Optional[str]=None,
    globals: Optional[Dict[str, Any]]=None,
    **kwargs,
) -> Twig:
    """Defines a *Python pip* twig.

    This twig type requires a stored version.

    :param package: The name of the package. If not specified, the name of the
    calling module is used.

    :param description: A description of the package. If not specified, the
    docstring of the calling module is used.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.

    :return: the twig
    """
    def _package(me: Twig) -> str:
        return package or me.name

    def _specification(me: Twig) -> str:
        return '{}=={}'.format(me.package, me.stored_version)

    @lru_cache
    def latest_version(me: Twig) -> str:
        data = me.web.json(PACKAGE_URL_FORMAT.format(me.name))
        return data['info']['version']

    @twig(
        description=description,
        globals=globals or caller_context(),
        **kwargs)
    def main(me: Twig):
        assert_pip(me)
        me.run_progress(
            sys.executable, '-m', MOD, 'install',
            '--user', '--upgrade', '--progress-bar=raw',
            *args(me),
            '${specification}',
            progress_re=INSTALL_PROGRESS,
            specification=me.specification)

    type(main).package = property(_package)
    type(main).specification = property(_specification)

    @main.checker
    def is_installed(me: Twig) -> bool:
        return _installed_packages().get(me.name, None) == me.stored_version

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            _run(
                me,
                'uninstall', *args(), '${specification}',
                check=True,
                silent=True,
                specification=me.specification)

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

    def assert_pip(me: Twig):
        """Asserts that the current version of pip supports the
        ``--progress-bar=raw`` argument.
        """
        _, version_string, *_ = _run(me, '--version', capture=True).split()
        version = tuple(int(v) for v in version_string.split('.'))

        # This argument was introduced in 24.1
        if version < (24, 1):
            _run(me, 'install', '--upgrade', *args(me), MOD, silent=True)

    def args(me: Twig) -> List[str]:
        global main
        return shlex.split(main.c.additional_arguments(''))

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
        normalize(package): version
        for (package, version) in (
            m.groups()
            for m in (
                PACKAGE_EXTRACTOR.match(line)
                for line in main.run(
                    sys.executable, '-m', MOD, 'list',
                    capture=True, interactive=False).splitlines())
            if m)}


def twig_main(me: Twig, **kwargs):
    def package(**kwargs):
        def add(name: str, description: str, version: str, package: str):
            path = TWIG_PATH / as_mod(name)
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            me.template(
                Path(__file__).parent / 'package.__init__.py.template',
                path / '__init__.py',
                name=name,
                description=description,
                version=version,
                package=package)
            me.template(
                Path(__file__).parent / 'package.VERSION.template',
                path / 'VERSION',
                name=name,
                description=description,
                version=version,
                package=package)

        {
            'add': add,
        }[kwargs.pop('pip_package_command')](**kwargs)

    {
        'package': package,
    }[kwargs.pop('pip_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='manage pip') \
        .add_subparsers(required=True, dest='pip_command')

    package = actions.add_parser('package', help='manages pip packages') \
        .add_subparsers(required=True, dest='pip_package_command')
    add = package.add_parser(
        'add',
        help='add a pip package')
    add.add_argument(
        '--name',
        help='the name of the package twig',
        required=True)
    add.add_argument(
        '--description',
        help='the description of the package twig',
        default='A pip package.')
    add.add_argument(
        '--version',
        help='the version of the package',
        required=True)
    add.add_argument(
        'package',
        help='the name of the package')

    return {
        me.name: lambda **args: twig_main(me, **args)}
