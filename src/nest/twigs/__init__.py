import argparse
import inspect
import os
import re
import shlex
import subprocess

from functools import lru_cache
from pathlib import Path
from types import MethodType, ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from .. import ROOT, NestException
from .configuration import Configuration

#: The path to twig modules.
TWIG_PATH = (ROOT / 'twigs').absolute()

#: The path to the files of a twig, relative to its directory.
FILES_PATH = Path('files')

#: A file containing  the version of a twig, relative to its directory.
VERSION_PATH = Path('VERSION')

#: The regex used to extract interpolation tokens.
TOKEN_RE = re.compile(r'\${([^}]+)}')

#: A function to add actions for a twig to the command line arguments.
#:
#: The return value is a listing of actions and the function responsible for
#: running the action.
ArgumentsCallback = Callable[
    ['Self', argparse._SubParsersAction],
    Dict[str, Callable[[Dict[str, Any]], None]]]

#: A function to determine whether a twig is already present.
PresentCallback = Callable[['Self'], None]

#: A function to prepare the twig for being installed.
PrepareCallback = Callable[['Self'], None]

#: A function to actually install a twig.
InstallCallback = Callable[['Self'], None]

#: A function to complete installation of this twig.
CompleteCallback = Callable[['Self'], None]

#: A function to remove this twig.
RemoveCallback = Callable[['Self'], None]

#: A function to list updates for this twig.
UpdateListerCallback = Callable[['Self'], List[str]]

#: A function to apply updates for this twig.
UpdateApplierCallback = Callable[['Self'], Optional[str]]

#: The registered twigs.
TWIGS = []


# Let ``from nest.twigs import *`` import all twigs
__path__ = [
    str(TWIG_PATH)]
__all__ = tuple(
    p.name
    for p in TWIG_PATH.iterdir()
    if p.is_dir())


class Twig:
    def __init__(
            self, installer: InstallCallback, name: str, description: str,
            dependencies: Set[str], source: Path, copy_files: bool,
            version_path: str=VERSION_PATH):
        self._installer = MethodType(installer, self)
        self._arguments = MethodType(lambda *_: {}, self)
        self._checker = MethodType(lambda *_: False, self)
        self._preparer = MethodType(lambda *_: None, self)
        self._completer = MethodType(lambda *_: None, self)
        self._remover = MethodType(lambda *_: None, self)
        self._update_lister = MethodType(lambda *_: [], self)
        self._update_applyer = MethodType(lambda *_: None, self)

        self._name = name
        self._description = description
        self._dependencies = dependencies
        self._source = source
        self._copy_files = copy_files
        self._version_path = version_path

        self._configuration = Configuration(Path(''))
        self._present = None

        if any(twig.name == name for twig in TWIGS):
            raise NestException('Twig "{}" added twice'.format(name))
        else:
            TWIGS.append(self)

    def __str__(self):
        return '{} - {}'.format(self.name, self.description)

    def arguments(self, f: ArgumentsCallback) -> ArgumentsCallback:
        """A decorator to mark a callable as a command line argument generator.
        """
        self._arguments = MethodType(f, self)
        return f

    def checker(self, f: PresentCallback) -> PresentCallback:
        """A decorator to mark a callable as the availability checker for this
        twig.
        """
        self._checker = MethodType(f, self)
        return f

    def preparer(self, f: PrepareCallback) -> PrepareCallback:
        """A decorator to mark a callable as the preparer callback for this
        twig.
        """
        self._preparer = MethodType(f, self)
        return f

    def completer(self, f: CompleteCallback) -> CompleteCallback:
        """A decorator to mark a callable as the completer callback for this
        twig.
        """
        self._completer = MethodType(f, self)
        return f

    def remover(self, f: RemoveCallback) -> RemoveCallback:
        """A decorator to mark a callable as the remover callback for this
        twig.
        """
        self._remover = MethodType(f, self)
        return f

    def update_lister(self, f: UpdateListerCallback) -> UpdateListerCallback:
        """A decorator to mark a callable as the update lister callback for
        this twig.
        """
        self._update_lister = MethodType(f, self)
        return f

    def update_applier(self, f: UpdateListerCallback) -> UpdateApplierCallback:
        """A decorator to mark a callable as the update applier callback for
        this twig.
        """
        self._update_applier = MethodType(f, self)
        return f

    def depends(self, other: 'Self') -> 'Self':
        """Adds an explicit dependency on another twig.

        :param other: The other twig.
        """
        self._dependencies.add(other.name)
        return self

    @property
    def name(self) -> str:
        """The name of this twig.
        """
        return self._name

    @property
    def description(self) -> str:
        """The description of this twig.

        If none has been set, this will fall back on :attr:`name`.
        """
        return self._description

    @property
    def stored_version(self) -> str:
        """A version for this twig stored in a file.

        :raise NestException: if the file cannot be read
        """
        path = (self.source.parent / self._version_path).absolute()
        try:
            return path.read_text().strip()
        except FileNotFoundError:
            raise NestException(
                'The file {} must contain the crate version',
                str(path))

    @stored_version.setter
    def stored_version(self, value: str):
        (self.source.parent / self._version_path).absolute().write_text(
            value + '\n')

    @property
    def dependencies(self) -> Set['Self']:
        """The dependencies of this twig.
        """
        try:
            return {
                next(
                    f
                    for f in TWIGS
                    if f.name == dependency)
                for dependency in self._dependencies}
        except StopIteration:
            raise NestException(
                    'Twig {} has unmet dependencies: {} '
                    '(available twigs: {})',
                    str(self),
                    ', '.join(
                        n
                        for n in self._dependencies
                        if not any(
                            f.name == n
                            for f in TWIGS)),
                    ', '.join(f.name for f in TWIGS))

    @property
    def source(self) -> Path:
        """The source directory
        """
        return self._source

    @property
    @lru_cache
    def files(self) -> List[Path]:
        """Iterates over the source files.

        All files returned are relative to the source directory, and the files
        are sorted alphabetically.

        Generally, this method will only list files, but if any directory
        listed in ``submodules`` is encountered, it will be returned and its
        content will be ignored.

        :return: a list of files and possibly directories.
        """
        result = []

        if self.source is not None and self._copy_files:
            for root, dirs, filenames in os.walk(self.source):
                root = Path(root)
                a, b = [], []
                for path in ((root / d).absolute() for d in dirs):
                    (a if path in self.configuration.submodules else b).append(
                        path)
                result.extend(
                    (root / dir).relative_to(self._source)
                    for dir in a)
                result.extend(
                    (root / filename).relative_to(self._source)
                    for filename in filenames)
                dirs[:] = b

        return sorted(result)

    @property
    def configuration(self) -> Configuration:
        """The current configuration.
        """
        return self._configuration

    @configuration.setter
    def configuration(self, value: Configuration):
        self.configuration.clear()
        self.configuration.update(value.items())
        self.configuration.submodules = value.submodules

    @property
    def enabled(self) -> bool:
        """Whether this twig is enabled for the current configuration.
        """
        return (self.name not in self.configuration.get('disable', set())
            or self.name in self.configuration.get('enable', set())) \
            and all(
                dependency.enabled
                for dependency in self.dependencies)

    @property
    def present(self) -> bool:
        """Whether the twig is currently present.

        Once this method is called, the value is only updated after
        :meth:`install` has been called.
        """
        if self._present is None:
            self._present = self._checker()
        return self._present

    @property
    def updates(self) -> List[str]:
        """A list of descriptions for the updates.

        This may be an empty list.
        """
        return self._update_lister()

    def list_actions(self, parser: argparse._SubParsersAction) -> Dict[
            str,
            Callable[[Dict[str, Any]], None]]:
        """Generates additional command line arguments.
        """
        return self._arguments(parser)

    def install(self):
        """Installs this twig.

        This method does not check whether this twig is already installed.
        """
        self._installer()
        self._present = None

    def prepare(self):
        """Prepares this twig for being installed.

        This method of all twigs is called in order before installing.
        """
        self._preparer()

    def complete(self):
        """Runs the complete callback.

        This method of all twigs is called in reversed order after installing.
        """
        self._completer()

    def remove(self):
        """Runs the remove callback.

        This method of all twigs is called in reversed order when uninstalling.
        """
        self._remover()

    def update(self) -> Optional[str]:
        """Runs the update callback.

        This method of all twigs is called in order when updating.

        The return value, if present, contains instructions to display to the
        user.
        """
        return self._update_applier()


def run(
        name: str, *args, check=False, capture=False, interactive=True,
        silent=False, **kwargs) -> Union[bool, str]:
    """Runs a command.

    :param name: The name of the twig running the command. This will be used
    to print an error message is the command fails.

    :param check: Whether to capture errors and return ``False`` instead of
    aborting the process.

    :param capture: Whether to capture output. If this is true, this
    function will return the output data.

    :param interactive: Whether to run the command interactively. If this
    is not true, no input can be passed, otherwise ``stdin`` will be connected
    to the current ``stdin``.

    :param silent: Whether to suppress all output.

    :param args: The command and arguments as a sequence of strings.

    :param kwargs: Any token values used as replacements for strings on the
    form ``'${token_name}'``.

    :returns: whether the command succeeded if ``capture`` is ``False``,
    otherwise the command output

    :raise NestException: if the command returns a non-zero exit code and
    ``check`` is ``False``
    """
    assert not (check and capture)
    assert not (capture and silent)

    # Override stdin to /dev/null if not interactive to force immediate error
    ins = (
        subprocess.DEVNULL
        if not interactive else
        None)

    # Allow reading stdout if capturing, hide if silent, otherwise just display
    # it
    outs = (
        subprocess.PIPE
        if capture else
        subprocess.DEVNULL
        if silent else
        None)

    # Perform string interpolation on kwargs for all command arguments
    args = [
        TOKEN_RE.sub(
            lambda m: (
                shlex.quote(str(kwargs[m.group(1)]))
                if m.group(1) in kwargs else
                m.group(0)),
            str(arg))
        for arg in args]

    p = subprocess.Popen(args, stdin=ins, stdout=outs, stderr=outs)
    stdout, _ = p.communicate()
    if p.returncode == 0:
        return stdout.decode('utf-8') if capture else True
    elif check:
        return False

    # We failed
    raise NestException(
        'Command {} for {} failed with code {}', ' '.join(args), name,
        p.returncode)


def twig(
        *,
        name: Optional[str]=None,
        description: Optional[str]=None,
        dependencies: Optional[Set[str]]=None,
        files: Optional[Path]=None,
        copy_files: Optional[bool]=None,
        version_path: Optional[str]=None,
        globals: Dict[str, Any]=None) -> Twig:
    """A decorator that registers a callable as a twig.

    If no arguments are provided, the twig attributes are deduced as
    follows:

    name
        The last part of the name of the module in which the twig is
        defined.

    description
        The docstring of the module in which the twig is defined.

    dependencies
        The list of imported twig modules in the module in which the twig
        is defined.

    files
        The directory :attr:`FILES_PATH` under the directory containing the
        module in which the twig is defined.

    copy_files
        Whether the name of the file in which the twig is defined is
        ``'__init__.py'``.

    version_path
        If the name of the file in which the twig is installed is
        ``'__init__.py'`` the string ``'VERSION'``, otherwise that string with
        a dot and the base name of the defining module name appended.

    :param name: The twig name.

    :param description: The twig description.

    :param dependencies: Thw twig dependencies.

    :param files: The twig files.

    :param copy_files: Whether to copy the files.

    :param version_path: The name of a file sibling to ``files`` where the
    version is stored.

    :param globals: The globals in the context of the twig. If not specified,
    the ``__globals__`` attribute of the annotated function will be used.

    :return: a twig
    """
    def context(f):
        return globals or f.__globals__

    return lambda f: Twig(
        f,
        name or _extract_name(context(f)),
        description or _extract_description(context(f)),
        dependencies or _extract_dependencies(context(f)),
        files or _extract_files(context(f)),
        copy_files or _extract_copy_files(context(f)),
        version_path or _extract_version_path(context(f)))


def empty() -> Twig:
    """A function that generates a no-op twig that is always considered to be
    installed.

    The twig attributes are deduced like in :func:`twig`.

    :return: a twig
    """
    context = inspect.currentframe().f_back.f_globals

    twig = Twig(
        lambda _: None,
        _extract_name(context),
        _extract_description(context),
        _extract_dependencies(context),
        _extract_files(context),
        _extract_copy_files(context))

    @twig.checker
    def is_installed(_):
        return True

    return twig


def caller_context() -> Dict[str, Any]:
    """Inspects the global variables of the caller of the caller of this
    function.

    :return: the globals up the strack from the caller of this function
    """
    return inspect.currentframe().f_back.f_back.f_globals


def _extract_name(context: Dict[str, Any]) -> str:
    try:
        return context['__name__'].rsplit('.', 1)[-1].replace('_', '-')
    except:
        raise NestException('Object does not have __name__: {}', context)


def _extract_description(context: Dict[str, Any]) -> str:
    try:
        return ' '.join((context['__doc__']).split())
    except:
        raise NestException('Object does not have __doc__: {}', context)


def _extract_dependencies(context: Dict[str, Any]) -> Set[str]:
    return {
        t.name
        for m in context.values()
        if isinstance(m, ModuleType)
            and Path(getattr(m, '__file__', '')).is_relative_to(TWIG_PATH)
        for t in m.__dict__.values()
        if isinstance(t, Twig)}


def _extract_files(context: Dict[str, Any]) -> Optional[Path]:
    return Path(context['__file__']).parent / FILES_PATH


def _extract_copy_files(context: Dict[str, Any]) -> Optional[Path]:
    return Path(context['__file__']).name == '__init__.py'


def _extract_version_path(context: Dict[str, Any]) -> Optional[Path]:
    name = Path(context['__file__']).name
    if name == '__init__.py':
        return VERSION_PATH
    else:
        return '{}.{}'.format(VERSION_PATH, name.rsplit('.', 1)[0])
