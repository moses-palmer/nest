import difflib
import errno
import os
import shutil

from pathlib import Path
from typing import Optional


#: The nest root.
ROOT = Path(__file__).parent.parent.parent


class NestException(Exception):
    """A non-recoverable exception occurring during a run.
    """
    pass


def copy():
    pass
