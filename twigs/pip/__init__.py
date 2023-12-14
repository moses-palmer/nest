"""Python package installer.
"""
import re
import shlex
import sys

from argparse import _SubParsersAction
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .. import Twig, caller_context, downloadable, system, twig


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
        assert_pip(me)
        me.run_progress(
            sys.executable, '-m', MOD, 'install',
            '--user', '--upgrade', '--progress-bar=raw',
            *args(me),
            '${package}==${version}',
            progress_re=INSTALL_PROGRESS,
            package=me.name,
            version=me.stored_version)

    @main.checker
    def is_installed(me: Twig) -> bool:
        global main
        return main.present \
            and _installed_packages().get(me.name, None) == me.stored_version

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            _run(
                me,
                'uninstall', *args(), me.name,
                check=True,
                silent=True)

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
        return shlex.split(me.configuration.pip.additional_arguments(''))

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


def twig_main(me: Twig, **kwargs):
    def package(**kwargs):
        def add(name: str, description: str, version: str, package: str):
            path = TWIG_PATH / name
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            nest.template(
                Path(__file__).parent / 'package.__init__.py.template',
                path / '__init__.py',
                name=name,
                description=description,
                version=version,
                package=package)
            nest.template(
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
    actions = actions.add_parser(me.name, help='Manages pip.') \
        .add_subparsers(required=True, dest='pip_command')

    crate = actions.add_parser('crate', help='Manages pip packages.') \
        .add_subparsers(required=True, dest='pip_package_command')
    add = crate.add_parser(
        'add',
        help='Adds a pip package.')
    add.add_argument(
        '--name',
        help='The name of the package twig',
        required=True)
    add.add_argument(
        '--description',
        help='The description of the package twig',
        default='A pip package.')
    add.add_argument(
        '--version',
        help='The version of the package',
        required=True)
    add.add_argument(
        'package',
        help='The name of the package')

    return {
        me.name: lambda **args: twig_main(me, **args)}
