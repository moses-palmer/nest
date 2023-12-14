import os

from pathlib import Path

def _xdg_dir(name: str, default: Path) -> Path:
    env = 'XDG_' + name + '_HOME'
    if env in os.environ:
        return Path(os.environ[env])
    else:
        return default


#: The nest root.
ROOT = Path(__file__).parent.parent.parent

HOME = Path.home()

BIN = HOME / '.local' / 'bin'
LIB = HOME / '.local' / 'lib'
VAR = HOME / '.var'

CACHE = _xdg_dir('CACHE', HOME / '.cache')
CONFIG = _xdg_dir('CONFIG', HOME / '.config')
DATA = _xdg_dir('DATA', HOME / '.local' / 'share')
