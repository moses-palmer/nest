import re
import subprocess

from pathlib import Path

from . import Distribution, Version

#: The regular expression used to extract values from lines in the information
#: file.
LINE_RE = re.compile(r'^([a-zA-Z][a-zA-Z0-9_]*)\s*:\s*(.*?)\s*$')


#: The file containing the software license.
LICENSE_FILE = (
    Path('/')
    / 'System'
    / 'Library'
    / 'Templates'
    / 'Data'
    / 'Library'
    / 'Documentation'
    / 'License.lpdf'
    / 'Contents'
    / 'Resources'
    / 'English.lproj'
    / 'License.html'
)

#: The regular expression used to extract values from lines in the license
#: file.
FRIENDLY_NAME_RE = re.compile(
    r'.*?SOFTWARE LICENSE AGREEMENT FOR macOS ([^\s]*).*'
)


def information():
    values = {
        m.group(1): m.group(2)
        for m in (
            LINE_RE.match(line)
            for line in subprocess.check_output(['sw_vers'])
            .decode('utf-8')
            .splitlines()
            if LINE_RE.match(line)
        )
    }

    try:
        friendly_name = (
            values['ProductName']
            + ' '
            + next(
                m.group(1)
                for line in LICENSE_FILE.read_text().splitlines()
                if (m := FRIENDLY_NAME_RE.match(line))
            )
        )
    except:
        friendly_name = values['ProductName']

    return (
        Distribution(friendly_name, 'macos'),
        Version(values['ProductVersion']),
    )
