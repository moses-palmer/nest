"""Lingering user sessions.
"""

import re
import os
import pwd

from .. import Twig, twig


#: The name of the current user.
USER = pwd.getpwuid(os.getuid()).pw_name


@twig()
def main(me: Twig):
    me.run('sudo', 'loginctl', 'enable-linger', USER)


@main.checker
def is_installed(me: Twig) -> bool:
    regex = re.compile(r'^\s*Linger\s*=\s*yes\s*$')
    return any(
        regex.match(line)
        for line in me.run(
            'loginctl', 'show-user', USER,
            capture=True,
            interactive=False).splitlines())
