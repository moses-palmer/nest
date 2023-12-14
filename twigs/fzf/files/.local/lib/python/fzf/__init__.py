import base64
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


def select(
    values: Iterable[str],
    title: str = None,
    display: Callable[[str], str] = str,
    preview: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """Interactively selects a value from a list.

    :param values: The source values.
    :param title: The window title.
    :param display: A function to map values to a display string. The strings
    cannot include newlines; any newline in the returned string will be
    replaced by whitespace.
    :param preview: A shell command used to generate previews.
    :return: maybe a string, if the user selected one
    """
    try:
        if preview is not None:
            ipc_dir = Path(tempfile.mkdtemp())
            preview = (
                preview,
                ipc_dir / 'command',
                ipc_dir / 'output',
            )

        return _select(
            values,
            title=title,
            display=display,
            preview=preview,
        )
    finally:
        if preview is not None:
            shutil.rmtree(ipc_dir)


def _select(
    values: Iterable[str],
    display: Callable[[str], str],
    title: str,
    preview: Optional[tuple[Callable[[str], str], Path, Path]],
) -> Optional[str]:
    args = [
        BIN,
        '--read0',
        '--accept-nth=1',
        '--with-nth=2',
        '--popup',
        '--delimiter=\n',
    ]
    if title is not None:
        args += ['--border-label', title]
    if preview is not None:
        mapper, commands, outputs = preview

        def previewer():
            def fifo(p):
                os.mkfifo(p)
                r = open(p, 'r')
                w = open(p, 'w')
                return (r, w)

            command = fifo(commands)
            try:
                for line in command[0]:
                    c, data = line.strip().split(':', 1)
                    match c:
                        case 'preview':
                            with open(outputs, 'w') as output:
                                data = base64.decodebytes(
                                    data.encode(ENCODING)
                                ).decode(ENCODING)
                                try:
                                    mapped = mapper(data)
                                except Exception as e:
                                    mapped = str(e)
                                output.write(
                                    base64.b64encode(
                                        mapped.encode(ENCODING),
                                    ).decode(ENCODING)
                                    + '\n'
                                )
                        case 'exit':
                            break
            finally:
                for f in command:
                    f.close()

        args += [
            '--preview',
            f"""
            sh -c " \
                ( printf preview: && echo {{1}} ) >>{commands} ;\
                head -n1 '{outputs}' | base64 -d"
            """,
        ]
        thread = threading.Thread(target=previewer)
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
            with open(preview[1], 'w') as f:
                f.write('exit:\n')
            thread.join()
