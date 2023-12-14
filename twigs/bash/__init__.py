"""GNU Bourne Again SHell.
"""

from pathlib import Path

from .. import system


#: A directory containing additional RC files read by bash on startup.
RC_PATH = Path('~/.config/bash/rc.d').expanduser()


main = system.package()
