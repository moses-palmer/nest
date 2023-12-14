"""A language empowering everyone to build reliable and efficient software.
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
    curl,
    run,
    system,
    twig,
)


#: The Rust compiler.
BIN_RUSTC = 'rustc'

#: The rustup binary.
BIN_RUSTUP = 'rustup'

#: The cargo binary.
BIN_CARGO = 'cargo'

#: A format string to generate the URL for crate versions.
VERSIONS_URL_FORMAT = 'https://crates.io/api/v1/crates/{}/versions'

#: A regular expression to extract a crate description from the output of
#: ``cargo install --list``.
CRATE_EXTRACTOR = re.compile(r'^([^\s]+)\s+v([^:]+):$')


@twig()
def main(me: Twig):
    if me.configuration['env']['distribution'] == 'termux':
        system.install(me)
    else:
        with curl.get(me, 'https://sh.rustup.rs') as script:
            run(me.name, 'sh', script, '-y', '--no-modify-path')


@main.checker
def is_installed(me: Twig):
    return system.is_installed(me, BIN_RUSTC)


@main.remover
def remove(me: Twig):
    if is_installed(me):
        run(me.name, 'rustup', 'self', 'uninstall')


def crate(
        *,
        name: Optional[str]=None,
        completions: Optional[List[str]]=None,
        globals: Optional[Dict[str, Any]]=None) -> Twig:
    """Defines a *Rust crate* twig.

    This twig type requires a stored version.

    :param name: The name of the crate. If not specified, the name of the
    calling module is used.

    :param name: A shell command to generate completions for this application.
    If specified, the command is expected to generate a completions description
    on ``STDOUT``. This data will be written to a file loaded by ``bash``.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.

    :return: the twig
    """
    @lru_cache
    def versions(me: Twig) -> Optional[str]:
        data = json.loads(
            curl.read(me, VERSIONS_URL_FORMAT.format(me.name)))
        return [
            version
            for version in (
                Version(description['num'])
                for description in data['versions']
                if not description['yanked']
                    and _version() >= Version(
                        description['rust_version'] or '0'))]

    def completions_path(me: Twig) -> Path:
        return bash.RC_PATH / 'completions.{}'.format(me.name)

    @twig(
        name=name,
        globals=globals or caller_context())
    def main(me: Twig):
        _run(
            me.name,
            BIN_CARGO, 'install', '${crate}@${version}',
            interactive=False,
            crate=me.name,
            version=me.stored_version)

    @main.completer
    def completer(me: Twig):
        if completions is not None:
            path = completions_path(me)
            if not path.exists():
                path.write_text(run(
                    me.name,
                    *completions,
                    capture=True))

    @main.checker
    def is_installed(me: Twig) -> bool:
        return _installed_crates().get(me.name, None) == me.stored_version

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            try:
                _run(
                    me.name,
                    BIN_CARGO, 'uninstall', me.name,
                    check=True,
                    silent=True)
            except FileNotFoundError:
                pass
        if completions is not None:
            path = completions_path(me)
            if path.exists():
                path.unlink()

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
            path = completions_path(me)
            if path.exists():
                path.unlink()
        me.complete()

    return main


def component(
    *,
    name: str,
    description: Optional[str]=None,
):
    """Defines a component feature.

    :param name: The name of the component.

    :param description: A description.

    :param args: Additional dependencies.
    """
    @twig(
        name=name,
        description=description,
        globals=caller_context())
    def main(me: Twig):
        _run(
            me.name,
            BIN_RUSTUP, 'component', 'add', me.name)

    @main.checker
    def is_installed(me: Twig):
        return any(
            component.startswith(me.name)
            for component in _installed_components())

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            try:
                _run(
                    me.name,
                    BIN_RUSTUP, 'component', 'remove', me.name,
                    check=True)
            except FileNotFoundError:
                pass

    return main


def _run(name: str, binary: str, *args: str, **kwargs: str):
    """Executes a Rust binary.

    This function ensures that the absolute path to the binary is passed, to
    ensure that it can be found without sourcing the cargo configuration file.

    :param name: The name of the twig running the command. This will be used
    to print an error message if the command fails.

    :param binary: The binary name.

    :param args: Additional command arguments.

    :param kwargs: Additional arguments.
    """
    return run(name, _qualify(binary), *args, **kwargs)


def _qualify(binary: str):
    """Generates a qualified path to a rust binary.

    If the local cargo directory exists, and contains a corrresponding
    executable, the absolute path of the file is returned, otherwise
    ``binary```is returned.

    :param binary: The name of the binary.

    :return: a path
    """
    path = os.path.join(os.path.expanduser('~/.cargo/bin'), binary)
    if os.access(path, os.X_OK):
        return path
    else:
        return binary


@lru_cache
def _installed_crates() -> Dict[str, str]:
    """Lists all installed crates and their versions.

    :return: a mapping from crate name to version
    """
    try:
        return {
            crate: version
            for (crate, version) in (
                m.groups()
                for m in (
                    CRATE_EXTRACTOR.match(line)
                    for line in _run(
                        'rust',
                        BIN_CARGO, 'install', '--list',
                        capture=True, interactive=False).splitlines())
                if m)}
    except FileNotFoundError:
        return {}


@lru_cache
def _installed_components() -> Set[str]:
    """Lists all installed components.

    :return: a set of installed components
    """
    try:
        return {
            line.strip()
            for line in _run(
                'rust',
                BIN_RUSTUP, 'component', 'list', '--installed',
                capture=True, interactive=False).splitlines()}
    except FileNotFoundError:
        return set()


@lru_cache
def _version() -> Version:
    """The version of Rust installed.

    If Rust is not installed, the version ``0.0.0`` will be returned.

    :return: the Rust version
    """
    try:
        return Version(_run(
            'rust',
            BIN_RUSTC, '--version',
            capture=True).split()[1])
    except FileNotFoundError:
        return Vecsion('0.0.0')


def twig_main(me: Twig, **kwargs):
    def crate(**kwargs):
        def add(name: str, description: str, version: str, crate: str):
            path = TWIG_PATH / name
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            nest.template(
                Path(__file__).parent / 'crate.__init__.py.template',
                path / '__init__.py',
                name=name,
                description=description,
                version=version,
                crate=crate)
            nest.template(
                Path(__file__).parent / 'crate.VERSION.template',
                path / 'VERSION',
                name=name,
                description=description,
                version=version,
                crate=crate)

        {
            'add': add,
        }[kwargs.pop('rust_crate_command')](**kwargs)

    {
        'crate': crate,
    }[kwargs.pop('rust_command')](**kwargs)


@main.arguments
def arguments(me: Twig, actions: _SubParsersAction):
    actions = actions.add_parser(me.name, help='Manages Rust.') \
        .add_subparsers(required=True, dest='rust_command')

    crate = actions.add_parser('crate', help='Manages Rust crates.') \
        .add_subparsers(required=True, dest='rust_crate_command')
    add = crate.add_parser(
        'add',
        help='Adds a Rust crate.')
    add.add_argument(
        '--name',
        help='The name of the crate twig',
        required=True)
    add.add_argument(
        '--description',
        help='The description of the crate twig',
        default='A Rust crate.')
    add.add_argument(
        '--version',
        help='The version of the crate',
        required=True)
    add.add_argument(
        'crate',
        help='The name of the crate')

    return {
        me.name: lambda **args: twig_main(me, **args)}
