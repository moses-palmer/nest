"""The stupid content tracker.
"""

import nest

from pathlib import Path
from typing import Any

from .. import Twig, run, system


#: The git directory.
GIT_DIR = nest.ROOT / '.git'

#: The work tree.
WORK_TREE = nest.ROOT


main = system.package()


def command(me: Twig, *args, **kwargs) -> Any:
    """Runs git in this repository.
    """
    return run(
        me.name,
        'git',
        '--git-dir={}'.format(GIT_DIR),
        '--work-tree={}'.format(WORK_TREE),
        *args, **kwargs)
