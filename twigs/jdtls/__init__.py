"""Eclipse JDT Language Server.
"""

import os
import shutil

from functools import lru_cache
from pathlib import Path
from typing import Optional

from nest import ui
from nest.platforms import Version
from .. import Twig, downloadable, java, twig, vim_vim_lsp


#: The format string used to generate the source URL.
SOURCE = 'https://www.eclipse.org/downloads/download.php?' \
    'file=/jdtls/milestones/{0}/jdt-language-server-{0}-{1}.tar.gz'

#: The format string used to generate the target path.
TARGET = os.path.expanduser('~/.local/lib/jdt-language-server-{0}.tar.gz')

#: The target directory for extracted files.
TARGET_DIR = Path(TARGET).parent / 'jdtls'

#: The directory containing plugins.
PLUGINS_DIR = TARGET_DIR / 'plugins'

#: The URL providing tags for the source repository.
TAGS_URL = 'https://api.github.com/repos/eclipse-jdtls/eclipse.jdt.ls/' \
    'git/refs/tags'

#: A format string to generate the URL of a file containing the filename of the
#: latest release.
LATEST_URL = 'https://download.eclipse.org/jdtls/milestones/{}/latest.txt'


@lru_cache
def latest_version(me: Twig) -> Optional[str]:
    try:
        versions = sorted(
            (
                Version(version_string)
                for version_string in (
                    ref['ref'].rsplit('/', 1)[-1][1:]
                    for ref in me.web.json(TAGS_URL)
                    if ref['ref'].startswith('refs/tags/v'))
                if all(
                    len(p) > 0 and all(
                        c == '.' or c.isdigit()
                        for c in p)
                    for p in version_string.split('.'))),
            reverse=True)
        for version in versions:
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


main = downloadable(
    source=lambda version: SOURCE.format(*version.rsplit('@', 1)),
    target=lambda version: TARGET.format(version.rsplit('@', 1)[0]),
    latest_version=latest_version)


@main.completer
def completer(me: Twig):
    if not (PLUGINS_DIR / 'org.eclipse.jdt.ls.core_{}.{}.jar'.format(
            *me.stored_version.rsplit('@', 1))).exists():
        archive = TARGET.format(me.stored_version.rsplit('@', 1)[0])
        shutil.rmtree(TARGET_DIR, ignore_errors=True)
        os.makedirs(TARGET_DIR, exist_ok=True)
        me.run(
            'tar', '--extract', '--file', archive, '--directory', TARGET_DIR)
