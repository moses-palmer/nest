import os

from pathlib import Path


def _xdg_dir(name: str, default: Path) -> Path:
    env = 'XDG_' + name + '_HOME'
    if env in os.environ:
        result = Path(os.environ[env])
        if result.is_relative_to(HOME):
            return result.relative_to(HOME)
        else:
            return default
    else:
        return default


#: The nest root.
ROOT = Path(__file__).parent.parent.parent

HOME = Path.home()
LOCAL = Path('.local')

BIN = LOCAL / 'bin'
LIB = LOCAL / 'lib'
VAR = Path('.var')

CACHE = _xdg_dir('CACHE', Path('.cache'))
CONFIG = _xdg_dir('CONFIG', Path('.config'))
DATA = _xdg_dir('DATA', LOCAL / 'share')
