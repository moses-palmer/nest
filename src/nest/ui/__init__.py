import math
import os
import shutil
import sys

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union

from nest.twigs import Twig


#: An ellipsis to indicate too long lines.
ELLIPSIS = '…'

#: The string used for a single level of indentation.
INDENT = '  '

#: The current indentation level.
__INDENT = 0

#: Delayed section headers.
__HEADERS: List[Tuple[int, str]] = []


def link(twig: Twig, source: Path, target: Path, rel: Path):
    """Attempts to link a file.

    This is an interactive function.

    If the link already exists and points to the correct file, no action is
    taken.

    If the file already exists, the user is queried whether to continue.

    :param twig: The twig performing the linking.
    :param source: The source directory.
    :param target: The target directory for files.
    :param rel: The file name, relative to the source directory.
    """
    source = (source / rel).absolute()
    target = (target / rel).absolute()

    if not target.exists() or (False
            or not target.is_symlink()
            or target.readlink() != source):
        log(item(installing(rel)))

        # Make sure the source exists
        if not source.exists() and source.is_symlink():
            raise NestException(
                'The source file {} is an invalid symlink to {}',
                source.relative_to(ROOT),
                source.readlink())

        # Make sure we do not overwrite files
        while target.exists() or target.is_symlink():
            r = query(
                '{} already exists. Overwrite? '.format(target),
                 'yes', 'no', 'diff')
            if r is None:
                return
            elif r == 0:
                twig.unlink(target)
                break
            elif r == 1:
                return
            elif r == 2:
                try:
                    with open(source, encoding='utf-8') as f:
                        sdata = f.readlines()
                    try:
                        with open(target, encoding='utf-8') as f:
                            tdata = f.readlines()
                    except FileNotFoundError:
                        # The target file may be an invalid link
                        tdata = ''
                    for line in difflib.unified_diff(
                            sdata,
                            tdata,
                            fromfile=str(source),
                            tofile=str(target)):
                        if line[0] == '+':
                            log(installing(line.rstrip()))
                        elif line[0] == '-':
                            log(removing(line.rstrip()))
                        else:
                            log(line.rstrip())
                except Exception:
                    log('Failed to read file.')

        twig.link(source, target)


def unlink(twig: Twig, source: Path, target: Path, rel: Path):
    """Attempts to unlink a file.

    If the file does not exist, no action is taken.

    If the file does exist, but is not a link to the expected target, no action
    is taken.

    :param twig: The twig performing the linking.
    :param source: The source directory.
    :param target: The target directory for files.
    :param rel: The file name, relative to the source directory.
    """
    source = (source / rel).absolute()
    target = (target / rel).absolute()

    if target.is_symlink() and target.readlink() == source:
        log(item(removing(
            rel if target.is_relative_to(twig.user_source) else target)))
        twig.unlink(target)


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
    columns = shutil.get_terminal_size().columns

    def display(item, is_last, level, stops):
        items = leaves(item)
        if level == 0:
            log(string(level, item))
        else:
            knob = '╼' if not items else '┮'
            indentation = (
                (''.join(
                    '  ' if i not in stops else '│ '
                    for i in range(level)) + (
                        f'├─{knob}' if not is_last else f'└─{knob}'))[2:],
                (''.join(
                    '  ' if i not in stops else '│ '
                    for i in range(level)) + (
                        '│ ' if not is_last else '  ') + ' ')[2:],
            )
            _print(columns, indentation, string(level, item))
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
def section(
    s: Optional[str]=None,
    delay: bool=False,
    length: Optional[int]=None,
):
    """A context manager to start a new section with increased indentation.

    :param section: A text for the section. If not specified, the section will
    only increase the indentation.

    :param delay: If ``True``, printing the section text will be delayed until
    an item is logged.

    :param length: The printable length of ``s``. If the text contains ANSI
    escape sequences, ``len(s)`` will not reflect the number of columns
    required for the header.
    """
    length = length if length is not None else len(s) if s is not None else 0
    columns = shutil.get_terminal_size().columns - len(INDENT) * __INDENT
    if s is not None and length >= columns:
        s = s[:-length + columns - 1] + ELLIPSIS + '\033[0m'

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
            print('{}{}'.format(INDENT * i, header))
    __HEADERS = []
    print('{}{}'.format(INDENT * __INDENT, s))


def _print(
    columns: int,
    indentation: Tuple[str, str],
    text: str,
):
    """Prints text with an indentation.

    Care is taken to not write past ``columns`` number of columns, and for each
    line an indentation is added; for the first line, ``indentation[0]`` and
    for subsequent lines ``indentation[1]``.

    Paragraphs are separated by ``'\n\n'``.

    :param columns: The maximum number of columns to use.

    :param indentation: The indentation to add.

    :param text: The text to print.
    """
    indentation = tuple(INDENT * __INDENT + i for i in indentation)
    indent = indentation[0]

    for i, block in enumerate(text.split('\n\n')):
        if i != 0:
            # Make sure to separate blocks
            print(indent)

        current = ''
        words = 0
        for word in block.split():
            if words == 0:
                # We are at the first word of the block
                current = indent
                indent = indentation[1]

            remaining = columns - len(current) - int(words > 0)
            if len(word) >= remaining:
                # The line is full
                if words == 0:
                    # ...from only one word; print it
                    s, word = word[:remaining], word[remaining:]
                    print(current + ' ' + s)
                    words = int(bool(current))
                    current = indent * int(words > 0) + word
                else:
                    # ...but we already have a line; print it and continue
                    print(current)
                    current = indent + ' ' + word
                    words = 1

            else:
                # There is still room for a new word; add it
                current += ' ' + word
                words += 1

        if current:
            # Print the remaining text
            print(current)
            current = ''
