"""Linux apps that run anywhere.
"""

import os
import platform
import shlex
import shutil
import tempfile

from pathlib import Path

from nest import directories

from .. import Twig, directories, system, twig


#: The name of the extracted directory.
SQUASHFS_ROOT = 'squashfs-root'

#: The name of the extracted executable.
BIN_NAME = 'AppRun'


def _is_installed(me: Twig, appimage: Twig) -> bool:
    """Returns whether an appimage is present on the system.

    :param me: This twig.
    :param appimage: The appimage twig.

    :returns: whether the appimage exists
    """
    binary = _binary(me, appimage)
    lib = _lib(me, appimage)

    return binary.exists() \
        and (not _should_extract(me, appimage) or lib.exists())


def _install(me: Twig, appimage: Twig):
    """Installs an appimage.

    :param me: This twig.
    :param appimage: The appimage twig.
    """
    binary = _binary(me, appimage)
    lib = _lib(me, appimage)

    with me.web.resource(_source(me, appimage)) as path:
        if _should_extract(me, appimage):
            directory = Path(tempfile.mkdtemp())
            os.chmod(path, 0o700)
            appimage.run(
                str(path), '--appimage-extract',
                check=True,
                silent=True,
                cwd=directory)
            if binary.exists() or binary.is_symlink():
                binary.unlink()
            if lib.exists():
                shutil.rmtree(lib)
            shutil.move(directory / SQUASHFS_ROOT, lib)
            binary.symlink_to(lib / BIN_NAME)
        else:
            shutil.copy(path, binary)
            binary.chmod(0o770)


def _remove(me: Twig, appimage: Twig):
    """Removes an appimage.

    :param me: This twig.
    :param appimage: The appimage twig.
    """
    binary = _binary(me, appimage)
    lib = _lib(me, appimage)

    binary.unlink(missing_ok=True)
    if _should_extract(me, appimage):
        shutil.rmtree(lib)


main = system.provider(Twig.empty(), _is_installed, _install, _remove)


def _should_extract(me: Twig, appimage: Twig) -> bool:
    """Whether the appimage should be extracted after it has been downloaded.

    :param me: This twig.
    :param appimage: The appimage twig.

    :return: whether extraction is required
    """
    return me.configuration.appimage.packages[appimage.name].extract() == 'true'


def _source(me: Twig, appimage: Twig) -> str:
    """The source URL.

    :param me: This twig.
    :param appimage: The appimage twig.

    :return: the download URL
    """
    return me.configuration.appimage.packages[appimage.name].url().format(
        version=me.configuration.appimage.packages[appimage.name].version(),
        **{
            attr: me.configuration.appimage.packages[appimage.name]
                .platform[getattr(platform, attr)()](attr)
            for attr in ('machine', 'system')
        })


def _binary(me: Twig, appimage: Twig):
    """The path to the binary used to launch this app.

    :param me: This twig.
    :param appimage: The appimage twig.

    :return: a path
    """
    return directories.BIN / appimage.name


def _lib(me: Twig, appimage: Twig):
    """The path to the extracted appimage.

    :param me: This twig.
    :param appimage: The appimage twig.

    :return: a path
    """
    return directories.LIB / appimage.name
