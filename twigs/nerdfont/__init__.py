"""Iconic font aggregator, collection, and patcher.
"""

import zipfile

from functools import lru_cache
from pathlib import Path

from .. import Twig, downloadable, twig


#: The repository host.
REPO_HOST = 'github.com'

#: The name of the repository.
REPO = 'ryanoasis/nerd-fonts'

#: The name of the font archive.
ARCHIVE_NAME = 'FiraCode.zip'

#: The name of the font file in the archive.
FILE_NAME = 'FiraCodeNerdFont-Regular.ttf'

#: The source URL for the font.
SOURCE = 'https://{}/{}/releases/download/{{0}}/{}'.format(
    REPO_HOST,
    REPO,
    ARCHIVE_NAME)

#: The target file.
TARGET = Path.home() / '.cache' / 'nerdfont' / ARCHIVE_NAME

#: The local font file.
FONT_TARGET = Path.home() / '.local' / 'share' / 'fonts' / FILE_NAME

#: The URL to query the latest version.
QUERY_URL = 'https://api.github.com/repos/{}/releases'.format(REPO)


@lru_cache
def latest_version(me: Twig) -> str:
    data = me.web.json(QUERY_URL)
    return data[0]['tag_name']


main = downloadable(
    source=SOURCE.format,
    target=str(TARGET).format,
    latest_version=latest_version)


@main.checker
def is_installed(me: Twig) -> bool:
    return FONT_TARGET.exists()


@main.completer
def complete(me: Twig):
    archive = zipfile.ZipFile(TARGET)
    archive.extract(FILE_NAME, FONT_TARGET.parent)


@main.remover
def remove(me: Twig):
    FONT_TARGET.unlink(missing_ok=True)
