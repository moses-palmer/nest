"""Iconic font aggregator, collection, and patcher."""

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


main = archive(
    source=_source,
    extract_to=str(directories.DATA / 'fonts').format,
    extension='zip',
    latest_version=ext.github.latest_version(REPO),
)
