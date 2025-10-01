import shutil

from contextlib import contextmanager
from typing import Any, Callable, List, Tuple


#: Queued messages to print if another message follows.
__QUEUE = []


def queue(s: str):
    """Enqueues a string to be printed if another string is later printed.

    :param s: The string to enqueue.
    """
    __QUEUE.append(s)


def log_if_queued(s: str):
    """Prints a log message only if any messages are enqueued for logging.

    Any queued messages will be discarded.

    :param s: The message to log.
    """
    if __QUEUE:
        __QUEUE.clear()
        log(s)


def log(s: str=''):
    """Prints a log message.

    If any messages are enqueued, those will be printed first.

    :param s: The message to log.
    """
    for m in __QUEUE:
        print(m)
    __QUEUE.clear()
    print(s)


@contextmanager
def progress():
    """Draws a progress bar at the bottom of the terminal.

    The value yielded is a callable that will update the progress with a value
    between 0 and 1.
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


def tree(
    root: Any,
    leaves: Callable[[Any], List[Any]],
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
