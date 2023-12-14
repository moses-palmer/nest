"""Command line tool for transferring data with URL syntax.
"""

import contextlib
import os
import shutil
import tempfile

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .. import Twig, caller_context, run, system, twig


main = system.package()


def read(me: Twig, url: str) -> bytes:
    """Fetches a text resource and returns it.

    :param me: The twig retrieving a file.

    :param url: The source URL.

    :return: the path to a temporary file
    """
    return run(
        me.name,
        'curl',
        '--location',
        url,
        capture=True)


@contextlib.contextmanager
def get(me: Twig, url: str) -> str:
    """Fetches a resource, writes it to a temporary file and returns the path.

    This function works as a context manager: once the context is exited, the
    temporary file is removed.

    :param me: The twig retrieving a file.

    :param url: The source URL.

    :return: the path to a temporary file
    """
    target = tempfile.mktemp()
    try:
        run(
            me.name,
            'curl',
            '--output', target,
            '--location',
            url,
            check=True,
            interactive=False,
            silent=True)
        yield target
    finally:
        os.unlink(target)


def downloadable(
    *,
    source: Callable[[str], str],
    target: Callable[[str], str],
    latest_version: Optional[Callable[[Twig], Optional[str]]]=None,
    globals: Optional[Dict[str, Any]]=None,
) -> Twig:
    """Defines a twig that is a downloaded file.

    This twig generator requires a stored version.

    :param source: A callable taking the version, as a string, as its argument
    and returning the source URL.

    :param target: A callable taking the version, as a string, as its argument
    and returning the target path..

    :param latest_version: A callable returning the latest version, if
    applicable. This will be called repeatedly.

    :param globals: A value of the ``globals`` parameter pass on to ``twig``.
    """
    @twig(globals=globals or caller_context())
    def main(me: Twig):
        with get(me, source(me.stored_version)) as path:
            target_path = Path(target(me.stored_version))
            os.makedirs(target_path.parent, exist_ok=True)
            shutil.copy(path, target_path)

    @main.checker
    def is_installed(me: Twig):
        return Path(target(me.stored_version)).exists()

    @main.remover
    def remove(me: Twig):
        try:
            Path(target(me.stored_version)).unlink()
        except FileNotFoundError:
            pass

    @main.update_lister
    def update_lister(me: Twig) -> List[str]:
        if latest_version is not None and latest_version(me) is not None \
                and latest_version(me) != me.stored_version:
            return [latest_version(me)]
        else:
            return []

    @main.update_applier
    def update_applier(me: Twig) -> List[str]:
        if latest_version is not None and latest_version(me) is not None:
            me.remove()
            me.stored_version = latest_version(me)
            me.install()

    return main
