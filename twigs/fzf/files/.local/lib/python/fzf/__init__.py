import base64
import functools
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading

from pathlib import Path

from typing import Iterable, Optional, Callable

#: The fzf binary name.
BIN = 'fzf'

#: The encoding to use.
ENCODING = sys.stdout.encoding

#: The field delimiter.
DELIMITER = '\n'

#: The field delimiter as a binary string.
_DELIMITER = DELIMITER.encode(ENCODING)

#: The fzf version that introduced the --popup argument
_POPUP_VERSION = (0, 74)


def select(
    values: Iterable[str],
    title: str = None,
    display: Callable[[str], str] = str,
    preview: Optional[Callable[[str], bytes]] = None,
) -> Optional[str]:
    """Interactively selects a value from a list.

    :param values: The source values.
    :param title: The window title.
    :param display: A function to map values to a display string. The strings
    cannot include newlines; any newline in the returned string will be
    replaced by whitespace.
    :param preview: A function used to generate previews.
    :return: maybe a string, if the user selected one
    """
    args = [
        BIN,
        '--read0',
        '--accept-nth=1',
        '--with-nth=2',
        '--delimiter=\n',
    ]
    if _version() >= _POPUP_VERSION:
        args += ['--popup']
    if title is not None:
        args += ['--border-label', title]
    if preview is not None:
        ipc_dir = Path(tempfile.mkdtemp())
        commands, outputs = (
            ipc_dir / 'command',
            ipc_dir / 'output',
        )
        args += [
            '--preview',
            f"""
            sh -c " \
                ( printf preview: && echo {{1}} ) >>{commands} ;\
                head -n1 '{outputs}' | base64 -d"
            """,
        ]
        thread = threading.Thread(target=_previewer(preview, commands, outputs))
        thread.start()
    else:
        args += ['--no-preview']
        thread = None
    try:
        p = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        stdout, _ = p.communicate(
            b'\x00'.join(
                base64.b64encode(v.encode(ENCODING))
                + _DELIMITER
                + display(v).replace(DELIMITER, ' ').encode(ENCODING)
                for v in values
            )
        )
        return base64.decodebytes(stdout).decode(ENCODING)
    except subprocess.CalledProcessError:
        return None
    finally:
        if thread is not None:
            with open(commands, 'w') as f:
                f.write('exit:\n')
            thread.join()
            shutil.rmtree(ipc_dir)


def _previewer(
    mapper: Callable[[str], bytes],
    commands: Path,
    outputs: Path,
) -> Callable[[], None]:
    """Adds a string mapper as a preview callback.

    :param mapper: A map function to convert values to a preview string.
    :param commands: A path used to communicate commands to the previewer.
    :param outputs: A path for the previewer to output results.
    """

    def fifo(p):
        os.mkfifo(p)
        r = open(p, 'r')
        w = open(p, 'w')
        return (r, w)

    def inner():
        command = fifo(commands)
        try:
            for line in command[0]:
                c, data = line.strip().split(':', 1)
                match c:
                    case 'preview':
                        with open(outputs, 'w') as output:
                            try:
                                data = base64.decodebytes(
                                    data.encode(ENCODING)
                                ).decode(ENCODING)
                                mapped = mapper(data)
                            except Exception as e:
                                print(e)
                                mapped = str(e).encode(ENCODING)
                            output.write(
                                base64.b64encode(mapped).decode(ENCODING) + '\n'
                            )
                    case 'exit':
                        break
        finally:
            for f in command:
                f.close()

    return inner


@functools.lru_cache
def _version() -> tuple[int, int]:
    version_tuple = tuple(
        int(p)
        for p in subprocess.check_output(
            [BIN, '--version'],
            encoding=ENCODING,
        )
        .strip()
        .split()[0]
        .split('.')
    )
    return (version_tuple[0], version_tuple[1])
