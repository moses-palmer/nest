import math
import os
import shutil
import sys

from contextlib import contextmanager
from typing import Any, Callable, List, Optional, Tuple, Union


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


def tree(
    root: Any, leaves: Callable[[Any], List[Any]],
    string: Callable[[int, Any], str],
):
    """Displays a tree of nodes.

    :param root: The root node. If this is ``None``, no root is displayed.
    :param leaves: A function generating the leaves of a node.
    :param string: A function converting a level and a node to a string.
    """
    def display(item, is_last, level, stops):
        if level == 0:
            log(string(level, item))
        else:
            log('{} {}'.format(
                ''.join(
                    '   ' if i not in stops else '│  '
                    for i in range(level)) + (
                        '├╼' if not is_last else '└╼'),
                    string(level, item))[3:])
        items = leaves(item)
        for (i, item) in enumerate(items):
            display(
                item,
                i == len(items) - 1,
                level + 1,
                stops + ([level] if not is_last else []))

    display(root, True, 0, [])


@contextmanager
def progress():
    """Draws a progress bar at the bottom of the terminal.
    """
    previous = 0

    def clear():
        sys.stdout.write('\33[2K\r')

    def inner(v: float):
        if v > 1.0:
            v = 1.0
        elif v < 0.0:
            v = 0.0

        # Clear only when regressing
        nonlocal previous
        if v < previous:
            clear()
        else:
            sys.stdout.write('\r')
        previous = v

        width = v * (shutil.get_terminal_size().columns - 1)

        sys.stdout.write('\033[0;32m')
        sys.stdout.write('█' * math.floor(width))
        fract = width % 1
        if fract > 0:
            partials = '▏▎▍▌▋▊▉'
            sys.stdout.write(partials[math.floor(fract * len(partials))])
        sys.stdout.write('\033[0m')
        sys.stdout.flush()

    sys.stdout.write('\033[?25l')
    try:
        clear()
        yield inner
    finally:
        clear()
        sys.stdout.write('\033[?25h')



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
