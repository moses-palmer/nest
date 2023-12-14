import os

from pathlib import Path


#: The nest root.
ROOT = Path(__file__).parent.parent.parent


class NestException(Exception):
    """A non-recoverable exception occurring during a run.
    """
    pass


def template(source: Path, target: Path, **kwargs):
    """Creates a new file from a template.

    All occurrences of ``'{key}'`` in the source file are replaced by
    ``kwargs['key']``.

    The target directory is created if it does not exist.

    :param source: The template file.

    :param target: The target file.
    """
    try:
        os.makedirs(target.parent)
    except:
        pass
    target.write_text(source.read_text().format(**kwargs))
