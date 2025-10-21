"""Package manager for Node.js.
"""

import json
import re
import os
import types

import nest

from pathlib import Path
from argparse import _SubParsersAction
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Union

from nest.platforms import Version
from .. import (
    TWIG_PATH,
    Twig,
    NestException,
    bash,
    caller_context,
    system,
    twig,
)


#: The Rust compiler.
BIN_NPM = 'npm'


main = system.package()


def package(
    *,
    package: Optional[str]=None,
    ignore_scripts: bool=True,
    globals: Optional[Dict[str, Any]]=None,
    **kwargs,
) -> Twig:
    """Defines a *npm package* twig.

    This twig type supports a stored version.

    :param package: The name of the package. If not specified, the name of the
    calling module is used.

    :param ignore_scripts: Whether to ignore running scripts.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.

    :return: the twig
    """
    def _package(me: Twig) -> str:
        return package or me.name

    def _specification(me: Twig) -> str:
        try:
            return '{}@{}'.format(me.package, me.stored_version)
        except NestException:
            return me.package

    @lru_cache
    def versions(me: Twig) -> List[Optional[str]]:
        try:
            return [json.loads(me.run(
                BIN_NPM, 'outdate', '--global', '--json', me.package,
                capture=True))[me.package]['latest']]
        except (KeyError, NestException):
            return []

    @twig(
        globals=globals or caller_context(),
        **kwargs)
    def main(me: Twig):
        me.run(
            BIN_NPM, 'install',
            '--global',
            '--ignore-scripts={}'.format(
                'true' if ignore_scripts else 'false'),
            '${specification}',
            specification=me.specification,
            check=True,
            silent=True)

    type(main).package = property(_package)
    type(main).specification = property(_specification)

    @main.checker
    def is_installed(me: Twig) -> bool:
        version = _installed_packages(me).get(me.package, None)
        try:
            return version == me.stored_version
        except NestException:
            return version is not None

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            try:
                me.run(
                    BIN_NPM, 'uninstall', '${specification}',
                    specification=me.specification,
                    check=True,
                    silent=True)
            except FileNotFoundError:
                pass

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        current = Version(me.stored_version)
        return [
            str(v)
            for v in versions(me)
            if v > current]

    @main.update_applier
    def update_applier(me: Twig) -> Optional[str]:
        me.stored_version = str(max(versions(me)))
        me.install()
        if completions is not None:
            completions_path(me).unlink(missing_ok=True)
        me.complete()

    return main


@lru_cache
def _installed_packages(me: Twig) -> Dict[str, str]:
    """Lists all installed packages and their versions.

    :return: a mapping from package name to version
    """
    try:
        return {
            package: specification['version']
            for (package, specification) in json.loads(me.run(
                BIN_NPM, 'list', '--global', '--json',
                capture=True))['dependencies'].items()}
    except (FileNotFoundError, NestException):
        return {}


def twig_main(me: Twig, **kwargs):
    def package(**kwargs):
        def add(
                name: str, description: str, version: Optional[str],
                package: str):
            path = TWIG_PATH / name
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            me.template(
                Path(__file__).parent / 'package.__init__.py.template',
                path / '__init__.py',
                description=description,
                name=name,
                package=package,
                version=version)
            if version is not None:
                me.template(
                    Path(__file__).parent / 'package.VERSION.template',
                    path / 'VERSION',
                    description=description,
                    name=name,
                    package=package,
                    version=version)

        {
            'add': add,
        }[kwargs.pop('npm_package_command')](**kwargs)

    {
        'package': package,
    }[kwargs.pop('npm_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='manage npm') \
        .add_subparsers(required=True, dest='npm_command')

    crate = actions.add_parser('package', help='manage npm packages') \
        .add_subparsers(required=True, dest='npm_package_command')
    add = crate.add_parser(
        'add',
        help='add a npm package')
    add.add_argument(
        '--name',
        help='the name of the package twig',
        required=True)
    add.add_argument(
        '--description',
        help='the description of the package twig',
        default='A NPM package.')
    add.add_argument(
        '--version',
        help='the version of the package',
        required=False)
    add.add_argument(
        'package',
        help='the name of the package')

    return {
        me.name: lambda **args: twig_main(me, **args)}
