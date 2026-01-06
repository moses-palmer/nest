"""Iconic font aggregator, collection, and patcher.
"""

import platform

from nest import directories

from .. import archive, ext


#: The name of the repository.
REPO = 'ryanoasis/nerd-fonts'


def _extract_to(version):
    if platform.system() == 'Darwin':
        return str(directories.HOME / 'Library' / 'Fonts')
    else:
        return str(directories.DATA / 'fonts')


main = archive(
    source=ext.github.source(REPO, 'FiraCode.zip'),
    extract_to=_extract_to,
    latest_version=ext.github.latest_version(REPO))
