import os

from contextlib import contextmanager
from typing import List, Optional, Tuple, Union


#: The current indentation level.
__INDENT = 0

#: Delayed section headers.
__HEADERS: List[Tuple[int, str]] = []


def query(prompt: str, *args) -> Optional[int]:
    """Queries the user for a string.

    :param prompt: The prompt. The options lowercased will be appended.

    :param args: The options. The index of the selected one will be returned.

    :return: one of the options, or ``None`` if running non-interactively
    """
    while os.isatty(0):
        options = [arg.lower() for arg in args]
        prompt = '{} [{}] '.format(prompt, '/'.join(options))
        r = input(prompt).lower()
        if r:
            alternatives = [
                i
                for (i, o) in enumerate(options)
                if o.startswith(r)]
            if len(alternatives) == 1:
                return alternatives[0]
            else:
                print('Please select one of {}'.format(', '.join(args)))


@contextmanager
def indent():
    """A context manager to add indent to following messages.
    """
    global __INDENT
    try:
        __INDENT += 1
        yield
    finally:
        __INDENT -= 1


@contextmanager
def section(s: Optional[str]=None, delay: bool=False):
    """A context manager to start a new section with increased indentation.

    :param section: A text for the section. If not specified, the section will
    only increase the indentation.

    :param delay: If ``True``
    """
    global __HEADER
    if not delay:
        log(s)
    else:
        __HEADERS.append((__INDENT, s))
    headers_len = len(__HEADERS)
    with indent():
        yield
    if delay and headers_len == len(__HEADERS):
        __HEADERS.pop()


def item(s) -> str:
    """Itemises a string.

    :param s: The string to itemise.

    :return: a string
    """
    return '• {}'.format(s)

def bold(s: str) -> str:
    """Generates a bold string.

    :param s: The message.
    """
    return '\033[1m{}\033[0m'.format(s)


def disabled(s: str) -> str:
    """Generates a colorised string to indicate that an item is disabled.

    :param s: The message.
    """
    return '\033[0;90m{}\033[0m'.format(s)


def ignoring(s: str):
    """Generates a colorised string to indicate that an item is ignored.

    :param s: The message.
    """
    return '\033[0;94m{}\033[0m'.format(s)


def installing(s: str):
    """Generates a colorised string to indicate that an item is being installed.

    :param s: The message.
    """
    return '\033[0;32m{}\033[0m'.format(s)


def removing(s: str):
    """Generates a colorised string to indicate that an item is being removed.

    :param s: The message.
    """
    return '\033[0;31m{}\033[0m'.format(s)


def log(s: str):
    """Displays an item.

    If a header has been queued, it will be shown first.

    :param s: The item to display.
    """
    global __INDENT, __HEADERS
    for item in __HEADERS:
        if item is not None:
            i, header = item
            print('{}{}'.format('  ' * i, header))
    __HEADERS = []
    print('{}{}'.format('  ' * __INDENT, s))
