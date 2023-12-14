import re

from functools import lru_cache
from typing import List, Optional

from nest.platforms import Version


#: The base host.
HOST = 'github.com'

#: The Github API base URL.
API_BASE = 'https://api.{}'.format(HOST)


def api_url(repository: str) -> str:
    """Generates the API URL for a repository.

    :param repository: The repository name.
    """
    return '{}/repos/{}'.format(API_BASE, repository)


def source(repository: str, path: str):
    """Generates a source URL generator for the file ``path`` that is part of a
    release.

    :param repository: The repository name.
    """
    return 'https://{}/{}/releases/download/{{0}}/{}'.format(
        HOST,
        repository,
        path).format


@lru_cache
def tags(twig, repository: str) -> List[str]:
    """Extracts tags from a Github repository.

    :param twig: The twig reading tags.
    :param repository: The repository name.
    """
    query_url = api_url(repository) + '/git/refs/tags'
    return [
        tag
        for tag in (
            ref['ref'].rsplit('/', 1)[-1]
            for ref in twig.web.json(query_url)
            if ref['ref'].startswith('refs/tags/'))]


def versions(twig, repository: str, pattern: re.Pattern) -> List[Version]:
    """Extracts version from tags from a repository.

    :param twig: The twig reading tags.
    :param repository: The repository name.
    :param pattern: The pattern used to extract versions from tags. The first
    group is used as version string.
    """
    return sorted(
        (
            Version(m.group(1))
            for m in (
                pattern.match(tag)
                for tag in tags(twig, repository))
            if m is not None),
        reverse=True)


def latest_version(repository: str) -> Optional[str]:
    """Lists updates from a Github repository.

    The update candidates are collected from the published releases.

    :param repository: The repository name.
    """
    from nest.twigs import Twig

    query_url = api_url(repository) + '/releases'

    @lru_cache
    def inner(me: Twig):
        try:
            return me.web.json(query_url)[0]['tag_name']
        except (IndexError, KeyError):
            return None

    return inner
