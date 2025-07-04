import argparse
import inspect
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from types import MethodType, ModuleType
from typing import Any, Callable, Dict, IO, List, Optional, Set, Tuple, Union

from .. import ROOT, NestException, ui, makedir
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
PresentCallback = Callable[['Self'], bool]

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
            dependencies: Set[str], source: Path,
            version_path: str=VERSION_PATH):
        self._installer = MethodType(installer, self)
        self._arguments = MethodType(lambda *_: {}, self)
        self._checker = MethodType(lambda *_: True, self)
        self._preparer = MethodType(lambda *_: None, self)
        self._completer = MethodType(lambda *_: None, self)
        self._remover = MethodType(lambda *_: None, self)
        self._update_lister = MethodType(lambda *_: [], self)
        self._update_applier = MethodType(lambda *_: None, self)

        self._name = name
        self._description = description
        self._dependencies = dependencies
        self._provides = set()
        self._source = source
        self._copy_files = not any(
            twig.source == source
            for twig in TWIGS)
        self._version_path = version_path
        self._web = Web(self)

        self._configuration = Configuration(Path(''))
        self._present = None

        if any(twig.name == name for twig in TWIGS):
            raise NestException('Twig "{}" added twice'.format(name))
        else:
            TWIGS.append(self)

    @classmethod
    def empty(cls) -> 'Self':
        """A function that generates a no-op twig that is always considered to
        be installed.

        The twig attributes are deduced like in :func:`twig`.

        :return: a twig
        """
        context = inspect.currentframe().f_back.f_globals

        twig = cls(
            lambda _: None,
            _extract_name(context),
            _extract_description(context),
            _extract_dependencies(context),
            _extract_files(context))

        return twig

    @staticmethod
    def interpolate(s: str, mapper: Callable[[str], Optional[str]]) -> str:
        """Interpolates tokens on the form ``${token.name}`` in a string.

        :param s: The string to interpolate.

        :param mapper: A function mapping token names to replacements. If this
        function returns ``None``, no replacement is performed.

        :return: an interpolated string
        """
        def replace(m):
            r = mapper(m.group(1))
            return str(r) if r is not None else m.group(0)
        return TOKEN_RE.sub(replace, str(s))

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
        previous = self._checker
        def wrapper(me):
            return previous() and f(me)
        self._checker = MethodType(wrapper, self)
        return f

    def preparer(self, f: PrepareCallback) -> PrepareCallback:
        """A decorator to mark a callable as the preparer callback for this
        twig.
        """
        previous = self._preparer
        def wrapper(me):
            previous()
            f(me)
        self._preparer = MethodType(wrapper, self)
        return f

    def completer(self, f: CompleteCallback) -> CompleteCallback:
        """A decorator to mark a callable as the completer callback for this
        twig.
        """
        previous = self._completer
        def wrapper(me):
            previous()
            f(me)
        self._completer = MethodType(wrapper, self)
        return f

    def remover(self, f: RemoveCallback) -> RemoveCallback:
        """A decorator to mark a callable as the remover callback for this
        twig.
        """
        previous = self._remover
        def wrapper(me):
            previous()
            f(me)
        self._remover = MethodType(wrapper, self)
        return f

    def update_lister(self, f: UpdateListerCallback) -> UpdateListerCallback:
        """A decorator to mark a callable as the update lister callback for
        this twig.
        """
        previous = self._update_lister
        def wrapper(me):
            return previous() + f(me)
        self._update_lister = MethodType(wrapper, self)
        return f

    def update_applier(self, f: UpdateListerCallback) -> UpdateApplierCallback:
        """A decorator to mark a callable as the update applier callback for
        this twig.
        """
        previous = self._update_applier
        def wrapper(me):
            return (previous() or '') + (f(me) or '') or None
        self._update_applier = MethodType(wrapper, self)
        return f

    def depends(self, other: 'Self') -> 'Self':
        """Adds an explicit dependency on another twig.

        :param other: The other twig.
        """
        self._dependencies.add(other.name)
        return self

    def provides(self, name: str) -> 'Self':
        """Adds an additional twig name whose features are also provided by
        this twig.

        :param name: The name of the twig.
        """
        self._provides.add(name)
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
                'The file {} must contain the twig version',
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
        self._configuration = value

    @property
    def enabled(self) -> bool:
        """Whether this twig is enabled for the current configuration.
        """
        def alternative_available(name):
            return any(
                name in twig._provides and twig.enabled
                for twig in TWIGS)
        return (self.name not in self.configuration.disable
            or self.name in self.configuration.enable) \
            and all(
                dependency.enabled or alternative_available(dependency.name)
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

    @property
    def web(self) -> 'Web':
        """A :class:`Web` instance for this twig.
        """
        return self._web

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
            self, *args, check=False, capture=False, stream=False, cwd=None,
            interactive=True, silent=False, **kwargs) -> Union[
                bool,
                str,
                subprocess.Popen,
            ]:
        """Runs a command.

        :param check: Whether to capture errors and return ``False`` instead of
        aborting the process.

        :param capture: Whether to capture output. If this is true, this
        function will return the output data.

        :param stream: Whether to stream captured output. If this is specified,
        the return value is the child process, which should be waited on
        eventually. This requires that ``capture`` is ``True``.

        :param cwd: The current working directory for the execution.

        :param interactive: Whether to run the command interactively. If this
        is not true, no input can be passed, otherwise ``stdin`` will be
        connected to the current ``stdin``.

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
        assert not (stream and not capture)

        # Override stdin to /dev/null if not interactive to force immediate
        # error
        ins = (
            subprocess.DEVNULL
            if not interactive else
            None)

        # Allow reading stdout if capturing, hide if silent, otherwise just
        # display it
        outs = (
            subprocess.PIPE
            if capture else
            subprocess.DEVNULL
            if silent else
            None)

        # Perform string interpolation on kwargs for all command arguments
        args = [
            Twig.interpolate(arg, kwargs.get)
            for arg in args]

        try:
            p = subprocess.Popen(
                args, stdin=ins, stdout=outs, stderr=subprocess.STDOUT, cwd=cwd)
            if stream:
                return p
            else:
                stdout, _ = p.communicate()
                if p.returncode == 0:
                    return stdout.decode('utf-8') if capture else True
                elif check:
                    return False
        except FileNotFoundError:
            if check:
                return False
            else:
                raise

        # We failed
        raise NestException(
            'Command {} for {} failed with code {}', ' '.join(args), self.name,
            p.returncode)

    def run_progress(self, *args, progress_re: re.Pattern=None, **kwargs):
        """Runs a command in stream mode, outputting progress.

        The progress meter is updated when lines matching ``progress_re`` are
        encountered. The regular expression must have either the two named
        capture groups ``current`` and ``max``, or the single ``percent`` used
        to determine the current progress.

        All other arguments are passed on to :meth:`run`.
        """
        if progress_re is None:
            pass

        elif 'current' in progress_re.groupindex:
            assert len(progress_re.groupindex) == 2
            assert 'current' in progress_re.groupindex
            assert 'max' in progress_re.groupindex
            def progress_value(m):
                return int(m.group('current')) / int(m.group('max'))

        elif 'percent' in progress_re.groupindex:
            assert len(progress_re.groupindex) == 1
            assert 'percent' in progress_re.groupindex
            def progress_value(m):
                return float(m.group('percent')) / 100


        child = self.run(
            *args, **kwargs, capture=True, stream=True, interactive=False)
        output = b''
        with ui.progress() as progress:
            for line in child.stdout:
                output += line
                try:
                    m = next(progress_re.finditer(line.decode('utf-8')))
                    progress(progress_value(m))
                except StopIteration:
                    pass
        code = child.wait()
        if code != 0:
            os.write(sys.stdout.fileno(), output)
            sys.exit(code)


class Web:
    """A simple HTTP client.
    """
    def __init__(self, twig: Twig):
        self._twig = twig

    @contextmanager
    def open(self, url: str, encoding_default: Optional[str]='utf-8') -> IO:
        """Opens a web resource

        :param url: The URL to read.
        :param encoding_default: The default text encoding if none is specified.

        :return: the response

        :raise NestException: if the request fails or status code indicates
        failure
        """
        def encoding(content_type) -> str:
            try:
                return next(re.finditer(
                    r'charset=([^ ;]+)',
                    content_type or '')).group(1)
            except StopIteration:
                return encoding_default

        try:
            with urllib.request.urlopen(url) as c:
                if c.status in range(200, 300):
                    c.content_type = c.headers.get(
                        'content-type', encoding_default)
                    c.encoding = encoding(c.content_type)
                    yield c
                else:
                    raise NestException(
                        'failed to retrieve "{}" for twig {}: HTTP status {}',
                        url,
                        self._twig.name,
                        c.code)
        except urllib.error.HTTPError as e:
            raise NestException(
                'failed to retrieve "{}" for twig {}: HTTP status {}',
                url,
                self._twig.name,
                e.code)

    @contextmanager
    def resource(self, url: str) -> Path:
        """Fetches a resource, writes it to a temporary file and returns the
        path.

        This function works as a context manager: once the context is exited,
        the temporary file is removed.

        :param url: The source URL.

        :return: the path to a temporary file

        :raise NestException: if the status code indicates failure
        """
        data = self.get(url, True)
        target = tempfile.mktemp()
        try:
            with open(target, 'wb') as f:
                f.write(data)
            yield target
        finally:
            os.unlink(target)

    def get(self, url: str, progress: bool=False) -> bytes:
        """Retrieves a resource.

        :param url: The URL to read.

        param progress: Whether to display a progress bar. This is only
        possible if the remote server provides a ``Content-Length``.

        :return: the response

        :raise NestException: if the status code indicates failure
        """
        with self.open(url) as c:
            if not progress or 'Content-Length' not in c.headers:
                return c.read()
            else:
                buffer = io.BytesIO()
                total = int(c.headers['Content-Length'])
                with ui.progress() as update:
                    while buffer.tell() < total:
                        buffer.write(c.read(1024))
                        update(buffer.tell() / total)
                    return buffer.getvalue()

    def string(self, url: str) -> str:
        """Retrieves a string resource.

        :param url: The URL to read.

        :return: the response

        :raise NestException: if the status code indicates failure or the
        response type is not text
        """
        return self._text(url, 'text/plain', 'text/')

    def json(self, url: str) -> Any:
        """Retrieves a JSON resource.

        :param url: The URL to read.

        :return: the response

        :raise NestException: if the status code indicates failure or the
        response type is not JSON
        """
        return json.loads(self._text(url, 'application/json'))

    def _text(
            self,
            url: str,
            content_type_default: str,
            content_type_check: str=None,
        ) -> str:
        """Retrieves a text resource.

        :param url: The URL to read.
        :param content_type_default: The default Content Type if none is
        specified.
        :param content_type_check: A string with which the content type must
        start.

        :return: a text

        :raise NestException: if the status code indicates failure or the
        response type is invalid
        """
        with self.open(url, 'utf-8') as c:
            if content_type_check is None or c.content_type.startswith(
                    content_type_check):
                return c.read().decode(c.encoding)
            else:
                raise NestException(
                    'failed to read "{}" for twig {}: expected text, found {}',
                    url,
                    self._twig.name,
                    c.content_type)


def twig(
        *,
        name: Optional[str]=None,
        description: Optional[str]=None,
        dependencies: Optional[Set[str]]=None,
        files: Optional[Path]=None,
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

    version_path
        If the name of the file in which the twig is installed is
        ``'__init__.py'`` the string ``'VERSION'``, otherwise that string with
        a dot and the base name of the defining module name appended.

    :param name: The twig name.

    :param description: The twig description.

    :param dependencies: Thw twig dependencies.

    :param files: The twig files.

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
        version_path or _extract_version_path(context(f)))


def downloadable(
    *,
    source: Callable[[str], str],
    target: Callable[[str], str],
    latest_version: Optional[Callable[[Twig], Optional[str]]]=None,
    globals: Optional[Dict[str, Any]]=None,
) -> Twig:
    """Defines a twig that is a downloaded file.

    This twig generator requires a stored version.

    :param source: A callable taking the version, as a string, as its argument
    and returning the source URL.

    :param target: A callable taking the version, as a string, as its argument
    and returning the target path..

    :param latest_version: A callable returning the latest version, if
    applicable. This will be called repeatedly.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.
    """
    @twig(globals=globals or caller_context())
    def main(me: Twig):
        with me.web.resource(source(me.stored_version)) as path:
            target_path = Path(target(me.stored_version))
            makedir(target_path.parent)
            shutil.copy(path, target_path)

    @main.checker
    def is_installed(me: Twig):
        return Path(target(me.stored_version)).exists()

    @main.remover
    def remove(me: Twig):
        Path(target(me.stored_version)).unlink(missing_ok=True)

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        if latest_version is not None and latest_version(me) is not None \
                and latest_version(me) != me.stored_version:
            return [latest_version(me)]
        else:
            return []

    @main.update_applier
    def update_applier(me: Twig) -> List[str]:
        if latest_version is not None and latest_version(me) is not None:
            me.remove()
            me.stored_version = latest_version(me)
            me.install()

    return main


def normalize(s: str) -> str:
    """Normalises a twig name.

    This function converts dots and underscores to dashes.

    :param s: The string to normalise.

    :return: a normalised string
    """
    return s.replace('.', '-').replace('_', '-')


def as_mod(s: str) -> str:
    """Converts a twig name to its corresponding module directory.

    This function converts everything except ASCII letters and digits and
    underscore to and underscore.

    :param s: The name to convert to a directory name.

    :return: an module name
    """
    return re.sub(r'[^a-zA-Z0-9_]', '_', s)


def caller_context() -> Dict[str, Any]:
    """Inspects the global variables of the caller of the caller of this
    function.

    :return: the globals up the strack from the caller of this function
    """
    return inspect.currentframe().f_back.f_back.f_globals


def _extract_name(context: Dict[str, Any]) -> str:
    try:
        return normalize(context['__name__'].rsplit('.', 1)[-1])
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


def _extract_version_path(context: Dict[str, Any]) -> Optional[Path]:
    name = Path(context['__file__']).name
    if name == '__init__.py':
        return VERSION_PATH
    else:
        return '{}.{}'.format(VERSION_PATH, name.rsplit('.', 1)[0])
