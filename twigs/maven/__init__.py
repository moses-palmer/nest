"""Java software project management and comprehension tool.
"""

import os

import nest

from functools import lru_cache
from pathlib import Path

from .. import Twig, caller_context, downloadable, java, system, twig


#: The URL format of a module JAR.
#:
#: The first formatting round takes the group and artifact IDs, and the second
#: round takes the version.
SOURCE_FORMAT = 'https://repo1.maven.org/maven2/{0}/{1}/{{0}}/{1}-{{0}}.jar'

#: The target directory for maven modules.
TARGET_DIR = Path('~/.m2/repository').expanduser()

#: The URL to query the latest version.
QUERY_FORMAT = 'https://search.maven.org/solrsearch/select?q=g:{}+AND+a:{}'


main = system.package(binary='mvn')


def module(
    *,
    group: str,
    artifact: str,
    target_format: str,
    **kwargs,
) -> Twig:
    """Defines a downloaded *maven module* twig.

    This twig type requires a stored version.

    :param group: The group ID of the module.

    :param artifact: The artifact ID of the module.

    :param target_format: A format string taking the current version that
    resolves to the target file.

    :return: the twig
    """
    @lru_cache
    def latest_version(me: Twig) -> str:
        data = me.web.json(QUERY_FORMAT.format(group, artifact))
        return data['response']['docs'][0]['latestVersion']

    repo_format = str(
        TARGET_DIR.joinpath(*group.split('.'))
        / artifact
        / '{0}'
        / '{}-{{0}}.jar'.format(artifact))

    main = downloadable(
        source=SOURCE_FORMAT.format(
            group.replace('.', '/'),
            artifact).format,
        target=repo_format.format,
        latest_version=latest_version,
        globals=caller_context(),
        **kwargs)

    @main.completer
    def completer(me: Twig):
        me.link(
            Path(repo_format.format(me.stored_version)),
            Path(target_format.format(me.stored_version)))

    return main
