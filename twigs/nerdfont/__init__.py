"""Iconic font aggregator, collection, and patcher.
"""

from .. import archive, directories, ext


#: The name of the repository.
REPO = 'ryanoasis/nerd-fonts'


main = archive(
    source=ext.github.source(REPO, 'FiraCode.zip'),
    extract_to=str(directories.DATA / 'fonts').format,
    latest_version=ext.github.latest_version(REPO))
