"""Eclipse JDT Language Server.
"""

import os
import re
import shutil

import nest

from functools import lru_cache
from pathlib import Path
from typing import Optional

from nest import directories, ui
from nest.platforms import Version

from .. import Twig, archive, ext, java, nvim_lsp_config, twig


#: The format string used to generate the source URL.
SOURCE = 'https://www.eclipse.org/downloads/download.php?' \
    'file=/jdtls/milestones/{0}/jdt-language-server-{0}-{1}.tar.gz'

#: The target directory for extracted files.
TARGET_DIR = directories.LIB / 'jdtls'

#: The directory containing plugins.
PLUGINS_DIR = TARGET_DIR / 'plugins'

#: The Github repository.
REPO = 'eclipse-jdtls/eclipse.jdt.ls'

#: A regular expression used to extract a version from a tag.
VERSION_RE = re.compile(r'v([0-9]+(\.[0-9]+)*)')

#: A format string to generate the URL of a file containing the filename of the
#: latest release.
LATEST_URL = 'https://download.eclipse.org/jdtls/milestones/{}/latest.txt'


@lru_cache
def latest_version(me: Twig) -> Optional[str]:
    try:
        for version in ext.github.versions(me, REPO, VERSION_RE):
            try:
                return '{}@{}'.format(
                    version,
                    me.web.string(LATEST_URL.format(version))
                        .rsplit('-', 1)[-1]
                        .split('.')[0])
            except:
                ui.log(ui.removing(
                    'Failed to get release date of JDTLS {}!'.format(
                        version)))
    except StopIteration:
        return None


def source(version: str):
    try:
        version, timestamp = version.split('@', 1)
        return SOURCE.format(version, timestamp)
    except ValueError:
        return SOURCE


main = archive(
    source=source,
    extract_to=str(TARGET_DIR).format,
    latest_version=latest_version,
    exclusive=True)
