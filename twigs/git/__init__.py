"""The stupid content tracker.
"""

import nest

from pathlib import Path
from typing import Any, List

from .. import Twig, system, twig


#: The git directory.
GIT_DIR = nest.ROOT / '.git'

#: The work tree.
WORK_TREE = nest.ROOT


main = system.package()


def with_submodules(me: Twig) -> Twig:
    """Generates a twig that is updated by updating submodules.
    """
    @me.update_lister
    def update_lister(me: Twig) -> List[str]:
        return [
            l.rstrip()
            for repopath in submodules(me)
            for l in command(
                me,
                'submodule', '--quiet', 'foreach',
                'if [ "$displaypath" = "${path}" ]; then '
                '   git fetch --quiet; '
                '   git log --format=format:%s '
                '       HEAD.."$(git default-remote)/$(git default-branch)"; '
                'fi',
                capture=True,
                path=repopath.relative_to(nest.ROOT),
            ).splitlines()]


    @me.update_applier
    def update_applier(me: Twig) -> List[str]:
        for repopath in submodules(me):
            command(
                me,
                'submodule', '--quiet', 'foreach',
                'if [ "$displaypath" = "${path}" ]; then '
                '   git checkout "$(git default-branch)"; '
                '   git pull; '
                'fi',
                silent=True,
                path=repopath.relative_to(nest.ROOT))


    def submodules(me: Twig) -> List[Path]:
        return [
            nest.ROOT / p
            for p in command(
                me,
                'submodule', 'foreach', '--quiet', 'echo "$displaypath"',
                capture=True).splitlines()
            if (nest.ROOT / p).is_relative_to(me.user_source)]

    return me


def command(me: Twig, *args, **kwargs) -> Any:
    """Runs git in this repository.
    """
    return me.run(
        'git',
        '--git-dir={}'.format(GIT_DIR),
        '--work-tree={}'.format(WORK_TREE),
        *args, **kwargs)
