#!/usr/bin/env python3

import contextlib
import os
import subprocess
import sys
import tempfile
import termios
import tty

from pathlib import Path

import ui


def main(prompt: str, output_file: Path, *alternatives: str):
    width = termios.tcgetwinsize(sys.stdin.fileno())[1]
    alternative_map = alternatives_map(*alternatives)
    _, text, separator, prompt_line = prompt_text(prompt, width, *alternatives)
    sys.stdout.write(text)
    sys.stdout.write('\n' + separator)
    sys.stdout.write('\033[1m{}\033[0m'.format(prompt_line))
    sys.stdout.write('\033[?25l')
    sys.stdout.flush()
    with _raw_terminal() as stdin:
        while True:
            r = stdin.read(1)
            if r in alternative_map:
                with output_file.open('w', encoding='utf-8') as f:
                    f.write(alternative_map[r])
                    f.flush()
                break
            elif r == '\x1b':
                break


@contextlib.contextmanager
def _raw_terminal():
    """Sets the TTY to raw mode and yields a file object."""
    old_mode = termios.tcgetattr(0)
    tty.setraw(0)
    try:
        yield sys.stdin
    finally:
        termios.tcsetattr(0, termios.TCSAFLUSH, old_mode)


def alternatives_map(*alternatives: str) -> dict[str, str]:
    """Extractor for the alternatives argument."""
    result = {a[0]: a for a in alternatives}
    if len(result) == len(alternatives):
        return result
    else:
        raise ValueError('conflicting alternatives')


def prompt_text(
    prompt: str,
    width: int,
    *alternatives: str,
) -> tuple[int, str, str, str]:
    """Generates information about the prompt text.

    :param prompt: The prompt.
    :param anternatives: The alternatives map.

    :return: the tuple ``(width, prompt_text, separator, alternatives)``, where
    ``width`` is the new width, which may be altered by a long list of
    alternatives
    """
    alternatives_text = '[{}]'.format(
        ' / '.join(
            '\033[4m{}\033[24m{}'.format(v[0], v[1:]) for v in alternatives
        )
    )
    alternatives_length = (
        2 + sum(len(a) for a in alternatives) + 2 * (len(alternatives))
    )
    width = max(width, alternatives_length)
    prompt_text = '\n'.join(ui.reflow(prompt, width, ('', ''))) + '\n'
    separator = '╾' + '─' * (width - 2) + '╼'
    return (width, prompt_text, separator, alternatives_text)


if __name__ == '__main__':
    try:
        main(sys.argv[1], Path(sys.argv[2]), *sys.argv[3:])
    except ValueError as e:
        sys.stderr.write('Error: {}'.format(e))
        sys.exit(1)
