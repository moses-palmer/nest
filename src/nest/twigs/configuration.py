import configparser

from pathlib import Path
from typing import Any, Dict, Sequence, Tuple


class Configuration(dict):
    #: The string separating a section name from its predicates.
    SEPARATOR = '::'

    #: A section added to all configurations containing the original values
    #: passed.
    ENV_SECTION = 'env'

    def __init__(self, gitmodules: Path, *filenames: Path, **values):
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
        submodules = configparser.ConfigParser()
        submodules.read(gitmodules)
        self.submodules = [
            gitmodules.parent / submodules[section]['path']
            for section in submodules.sections()]

        data = {
            self.ENV_SECTION: values}
        self._values = values
        for filename in filenames:
            values = self._extract_values(filename, values)
            for (section, values) in values.items():
                if section == self.ENV_SECTION:
                    raise ValueError('the section {} is reserved'.format(
                        self.ENV_SECTION))
                try:
                    data[section].update(values)
                except KeyError:
                    data[section] = dict(values)

        super().__init__(data)

    def __getattr__(self, key: str) -> str:
        try:
            return self._values[key]
        except KeyError:
            raise AttributeError(key)

    def _extract_values(
            self, filename: str, values: Dict[str, Any]) -> Dict[str, str]:
        """Extracts all applicable sections from a file.

        :param filename: The configuration file to parse.

        :param values: Distribution specific values used to filter the sections
            to return.

        :return: a mapping from normalised section name to entries
        """
        result = {}
        for (section, expression, entries) in self._extract_sections(filename):
            if eval(expression, values):
                try:
                    result[section].update(entries)
                except KeyError:
                    result[section] = dict(entries)

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
                compile(expression.strip(), filename, 'eval'),
                entries)
