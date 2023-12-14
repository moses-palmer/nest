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
    system,
    twig,
)


#: The Rust compiler.
BIN_RUSTC = 'rustc'

#: The rustup binary.
BIN_RUSTUP = 'rustup'

#: The cargo binary.
BIN_CARGO = 'cargo'

#: The Cargo directory.
CARGO_DIR = Path.home() / '.cargo'

#: A format string to generate the URL for crate versions.
VERSIONS_URL_FORMAT = 'https://crates.io/api/v1/crates/{}/versions'

#: The location of rust component metadata.
COMPONENT_METADATA_URL = 'https://static.rust-lang.org/' \
    'dist/channel-rust-stable.toml'

#: A regular expression to extract the progress from cargo install.
INSTALL_PROGRESS = re.compile(
    r'Building \[[^]]*\] (?P<current>\d*)/(?P<max>\d*):')

#: A regular expression to extract a crate description from the output of
#: ``cargo install --list``.
CRATE_EXTRACTOR = re.compile(
    r'^([^\s]+)\s+v([^:]+)(?: \([^?]*\?tag=([^#]+).*\))?:$')

#: A regular expresison to extract the TOML key name from a string. This works
#: only for simple keys, like ``'[key.name]``.
METADATA_KEY_EXTRACTOR_RE = re.compile(r'\[([^[\]]+)\]')


@twig()
def main(me: Twig):
    with me.web.resource('https://sh.rustup.rs') as script:
        me.run('sh', script, '-y', '--no-modify-path')


@main.checker
def is_installed(me: Twig):
    return os.access(_qualify(BIN_RUSTUP), os.X_OK)


@main.completer
def completer(me: Twig) -> List[str]:
    try:
        current = _version()
        newest = Version(
            _component_metadata()['pkg.rust']['version'].split()[0])
        if newest > current:
            _run(me, BIN_RUSTUP, 'update')
    except:
        pass


@main.remover
def remove(me: Twig):
    if is_installed(me):
        _run(me, BIN_RUSTUP, 'self', 'uninstall')


def crate(
    *,
    name: Optional[str]=None,
    from_repository: Optional[str]=None,
    features: List[str]=[],
    completions: Optional[List[str]]=None,
    globals: Optional[Dict[str, Any]]=None,
    **kwargs,
) -> Twig:
    """Defines a *Rust crate* twig.

    This twig type requires a stored version.

    :param name: The name of the crate. If not specified, the name of the
    calling module is used.

    :param from_repository: If provided, the crate will be installed from a git
    repository instead of from ``crates.io``.

    :param features: Any additional features to enable.

    :param completions: A shell command to generate completions for this
    application. If specified, the command is expected to generate a
    completions description on ``STDOUT``. This data will be written to a file
    loaded by ``bash``.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.

    :return: the twig
    """
    @lru_cache
    def versions(me: Twig) -> Optional[str]:
        if from_repository is None:
            data = me.web.json(VERSIONS_URL_FORMAT.format(me.name))
            return [
                version
                for version in (
                    Version(description['num'])
                    for description in data['versions']
                    if not description['yanked']
                        and _version() >= Version(
                            description['rust_version'] or '0'))]
        else:
            return None

    def completions_path(me: Twig) -> Path:
        return bash.RC_PATH / 'completions.{}'.format(me.name)

    @twig(
        name=name,
        globals=globals or caller_context(),
        **kwargs)
    def main(me: Twig):
        if from_repository is None:
            source_args = ('${crate}@${version}',)
        else:
            source_args = ('--git=${repository}', '--tag=${tag}')
        feature_args = ('--features=${features}',) if features else ()
        me.run_progress(
            _qualify(BIN_CARGO), 'install',
            '--config', 'term.progress.when="always"',
            '--config', 'term.progress.width=100',
            *source_args, *feature_args,
            progress_re=INSTALL_PROGRESS,
            crate=me.name,
            version=me.stored_version,
            repository=from_repository,
            tag=me.stored_version,
            features=','.join(features))


    @main.completer
    def completer(me: Twig):
        if completions is not None:
            path = completions_path(me)
            if not path.exists():
                path.write_text(_run(
                    me,
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
                    me,
                    BIN_CARGO, 'uninstall', me.name,
                    check=True,
                    silent=True)
            except FileNotFoundError:
                pass
        if completions is not None:
            path = completions_path(me)
            path.unlink(missing_ok=True)

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        if from_repository is None:
            current = Version(me.stored_version)
            return [
                str(v)
                for v in versions(me)
                if v > current]
        else:
            return []

    @main.update_applier
    def update_applier(me: Twig) -> Optional[str]:
        me.stored_version = str(max(versions(me)))
        me.install()
        if completions is not None:
            completions_path(me).unlink(missing_ok=True)
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
            me,
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
                    me,
                    BIN_RUSTUP, 'component', 'remove', me.name,
                    check=True)
            except FileNotFoundError:
                pass

    return main


def _run(me: Twig, binary: str, *args: str, **kwargs: str):
    """Executes a Rust binary.

    This function ensures that the absolute path to the binary is passed, to
    ensure that it can be found without sourcing the cargo configuration file.

    :param me: The twig running the command. This will be used to print an
    error message if the command fails.

    :param binary: The binary name.

    :param args: Additional command arguments.

    :param kwargs: Additional arguments.
    """
    return me.run(binary, env_path=[str(CARGO_DIR / 'bin')], *args, **kwargs)


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
            crate: tag if tag is not None else version
            for (crate, version, tag) in (
                m.groups()
                for m in (
                    CRATE_EXTRACTOR.match(line)
                    for line in _run(
                        main,
                        BIN_CARGO, 'install', '--list',
                        capture=True, interactive=False).splitlines())
                if m)}
    except (FileNotFoundError, NestException):
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
                main,
                BIN_RUSTUP, 'component', 'list', '--installed',
                capture=True, interactive=False).splitlines()}
    except (FileNotFoundError, NestException):
        return set()


@lru_cache
def _version() -> Version:
    """The version of Rust installed.

    If Rust is not installed, the version ``0.0.0`` will be returned.

    :return: the Rust version
    """
    try:
        return Version(_run(
            main,
            BIN_RUSTC, '--version',
            capture=True).split()[1])
    except FileNotFoundError:
        return Vecsion('0.0.0')


@lru_cache
def _component_metadata() -> Dict[str, str]:
    """A subset of the component metadata available from rust-lang.org.
    """
    result = {}
    with main.web.open(COMPONENT_METADATA_URL) as f:
        current = None
        for line in (line.decode(f.encoding).strip() for line in f):
            if line and line[0] == '[':
                m = METADATA_KEY_EXTRACTOR_RE.match(line)
                current = m.group(1) if m else None
            elif current is not None and '=' in line:
                s = result.get(current, {})
                key, val = line.split('=', 1)
                s[key.strip()] = json.loads(val.strip())
                result[current] = s
    return result


def twig_main(me: Twig, **kwargs):
    def crate(**kwargs):
        def add(
                name: str, description: str, version: str, crate: str,
                repository: Optional[str]=None):
            path = TWIG_PATH / name
            if path.exists():
                raise nest.NestException('Directory {} already exists!', path)

            me.template(
                Path(__file__).parent / 'crate.__init__.py.template',
                path / '__init__.py',
                name=name,
                description=description,
                version=version,
                crate=crate,
                repository=repr(repository))
            me.template(
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
    actions = actions.add_parser(me.name, help='manage Rust') \
        .add_subparsers(required=True, dest='rust_command')

    crate = actions.add_parser('crate', help='manage Rust crates') \
        .add_subparsers(required=True, dest='rust_crate_command')
    add = crate.add_parser(
        'add',
        help='add a Rust crate')
    add.add_argument(
        '--name',
        help='the name of the crate twig',
        required=True)
    add.add_argument(
        '--description',
        help='the description of the crate twig',
        default='A Rust crate.')
    add.add_argument(
        '--version',
        help='the version of the crate',
        required=True)
    add.add_argument(
        '--repository',
        help='a git repository to use as source instead of crates.io',
        required=False)
    add.add_argument(
        'crate',
        help='the name of the crate')

    return {
        me.name: lambda **args: twig_main(me, **args)}
