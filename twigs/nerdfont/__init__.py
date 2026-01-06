"""Iconic font aggregator, collection, and patcher."""

import platform

from nest import directories

from .. import archive, ext


#: The name of the repository.
REPO = 'ryanoasis/nerd-fonts'

#: The archive extension.
EXTENSION = 'zip'

#: The default font name to download.
DEFAULT_NAME = 'FiraCode'


def _source(version):
    return ext.github.source(
        REPO,
        f'{main.c.font_name(DEFAULT_NAME)}.{EXTENSION}',
    )(version)


def _extract_to(version):
    if platform.system() == 'Darwin':
        # Use an absolute path, macOS fails to list symlinked fonts
        return str(directories.HOME / 'Library' / 'Fonts')
    else:
        return str(directories.DATA / 'fonts')


main = archive(
    source=_source,
    extract_to=_extract_to,
    extension='zip',
    latest_version=ext.github.latest_version(REPO),
)
