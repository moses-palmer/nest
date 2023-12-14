import ast
import configparser

from functools import reduce
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union


class Container:
    def __init__(self, path: Optional[str], values: dict={}):
        from . import normalize
        self._path = path
        self._values = {
            normalize(k): v
            for (k, v) in values.items()} if values else None

    def __call__(self, default: str=None) -> str:
        if default is not None:
            return default
        else:
            return self._values

    def __iter__(self):
        if self._values is not None:
            return iter(self._values)
        else:
            return iter(())

    def __contains__(self, k: str):
        from . import normalize
        return self._values is not None and normalize(k) in self._values

    def __getattr__(self, key: str) -> Any:
        from . import normalize
        key = normalize(key)
        if self._path is not None:
            path = '{}.{}'.format(self._path, key)
        else:
            path = key
        try:
            v = self._values[key]
            if not isinstance(v, dict) or v is None:
                return Value(v)
            else:
                return Container(path, v)
        except (KeyError, TypeError):
            return Container(path)

    def __getitem__(self, key: str) -> Any:
        return self.__getattr__(key)

    def __repr__(self) -> str:
        return repr(self._values)


class Value:
    def __init__(self, value: Any):
        self._value = value

    def __call__(self, default: Any=None) -> Any:
        return self._value

    def __iter__(self):
        return iter(self._value)

    def __repr__(self) -> str:
        return repr(self._value)


class Configuration:
    #: The string separating a section name from its predicates.
    SEPARATOR = '::'

    #: A section added to all configurations containing the original values
    #: passed.
    ENV_SECTION = 'env'

    #: A section added to all configurations containing the paths to
    #: submodules.
    SUBMODULES_SECTION = 'submodules'

    def __init__(self, gitmodules: Path, *filenames: Path, **env):
        """Initialises a configuration object.

        A configuration object is a collection of sections and corresponding
        values. The format of a configuration file resembles a plain INI file,
        but it supports additional metadata in the section headers.

        :param gitmodules: A file containing a listing of submodules.

        :param filenames: The source files. Non-existing files are simply
            ignored: it is not an error to pass invalid file names as per the
            specification in :meth:`configparser.ConfigParser.read`.

        :param values: Distribution specific values.
        """
        def merge(a, b):
            for k, v in b.items():
                if isinstance(v, dict):
                    a[k] = merge(a.get(k, {}), v)
                else:
                    a[k] = v
            return a

        submodules = configparser.ConfigParser()
        submodules.read(gitmodules)
        data = {
            self.ENV_SECTION: {
                k: v
                for k, v in env.items()
                if k[0] != '_'},
            self.SUBMODULES_SECTION: [
                gitmodules.parent / submodules[section]['path']
                for section in submodules.sections()]}
        for filename in filenames:
            try:
                values = self._extract_values(filename, env)
            except ValueError as e:
                raise ValueError('in "{}": {}'.format(filename, e))
            for (section, values) in values.items():
                if section in (self.ENV_SECTION, self.SUBMODULES_SECTION):
                    raise ValueError('the section {} is reserved'.format(
                        section))
                else:
                    data[section] = merge(data.get(section, {}), values)

        self._data = Container(None, data)

    def __getattr__(self, key: str) -> Union[Container, Any]:
        return self._data[key]

    def __getitem__(self, key: str) -> Any:
        from . import normalize
        return self.__getattr__(normalize(key))

    def __repr__(self) -> str:
        return repr(self._data)

    def _extract_values(
            self, filename: str, values: Dict[str, Any]) -> Dict[str, str]:
        """Extracts all applicable sections from a file.

        :param filename: The configuration file to parse.

        :param values: Distribution specific values used to filter the sections
            to return.

        :return: a mapping from normalised section name to entries
        """
        def recurse(a, b):
            a[b] = a.get(b, {})
            return a[b]
        result = {}
        for (section, expression, entries) in self._extract_sections(filename):
            if expression(values):
                target = reduce(recurse, section.split('.'), result)
                target.update(entries)

        return result

    def _extract_sections(
            self, filename: str) -> Sequence[Tuple[str, str, str]]:
        """Extracts all section from a file.

        This method yields the tuple ``(section, expression, entries)``, where
        ``section`` is the normalised name of the section, ``expression`` is a
        code object that can be evaluated to determine whether to include the
        section, and ``entries`` are the actual values.

        If ``filename`` cannot be read, this method does not raise an error;
        rather, it yields an empty sequence.

        :param filename: The configuration file to read.
        """
        from . import normalize
        configuration = configparser.ConfigParser(allow_no_value=True)
        configuration.optionxform = str
        configuration.read(filename)
        for (key, entries) in configuration.items():
            try:
                section, expression = key.split(self.SEPARATOR, 1)
            except ValueError:
                section, expression = key, str(True)
            yield (
                section.strip(),
                compile_expression(expression.strip()),
                {
                    normalize(k): v
                    for (k, v) in entries.items()})


try:
    from ._expression import compile_expression
except SyntaxError:
    def compile_expression(expression: str) -> Callable[[Dict[str, Any]], bool]:
        """A simplified, insecure version of ``compile_expression`` that is
        compatible with older versions of Python.
        """
        node = compile(expression, '<string>', 'eval')

        def inner(args):
            return eval(node, args)

        return inner
