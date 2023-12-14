"""Local files for this computer only.
"""

import importlib

from pathlib import Path

from .. import empty


main = empty()


for p in (
        p
        for p in Path(__file__).parent.iterdir()
        if p.is_file() and p.suffix == '.py' and p.name[0] != '_'):
    importlib.import_module('.' + p.name.rsplit('.', 1)[0], __package__)
