"""Another Java Decompiler.
"""

import os

from functools import lru_cache

from .. import Twig, downloadable, java, twig


#: The repository host.
REPO_HOST = 'github.com'

#: The name of the repository.
REPO = 'leibnitz27/cfr'

#: The source URL for the library.
SOURCE = 'https://{}/{}/releases/download/{{0}}/cfr-{{0}}.jar'.format(
    REPO_HOST,
    REPO)

#: The directory containing the library file.
TARGET = os.path.join(
        os.path.expanduser('~/.local/lib/cfr/'),
        'cfr-{}.jar')

#: The URL to query the latest version.
QUERY_URL = 'https://api.github.com/repos/{}/releases'.format(REPO)


@lru_cache
def latest_version(me: Twig) -> str:
    data = me.web.json(QUERY_URL.format(me.name))
    return data[0]['tag_name']


main = downloadable(
    source=SOURCE.format,
    target=TARGET.format,
    latest_version=latest_version)
