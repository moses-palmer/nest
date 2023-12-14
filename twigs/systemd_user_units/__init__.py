"""Systemd user units.
"""

import os

from typing import Sequence

from .. import Twig, twig


@twig()
def main(me: Twig):
    pass

@main.checker
def is_enabled(me: Twig) -> bool:
    return all(
        enabled(me, unit)
        for unit in units(me))


@main.completer
def complete(me: Twig):
    for unit in (
            unit
            for unit in units(me)
            if not enabled(me, unit)):
        enable(me, unit)


def units(me: Twig) -> Sequence[str]:
    """Lists the names of all user units.

    :param me: The currently handled twig.

    :return: a list of unit names, including extension
    """
    return (
        p.name
        for p in (me.source / '.config' / 'systemd' / 'user').iterdir()
        if p.is_file())


def enabled(me: Twig, unit: str) -> bool:
    """Determines whether a user unit file is enabled.

    This function will return ``False`` if the unit name is invalid.

    :param me: The currently handled twig.

    :param unit: The unit name.

    :return: whether the unit is enabled
    """
    return me.run(
        'systemctl', '--user', 'is-enabled', unit,
        check=True,
        silent=True)


def enable(me: Twig, unit: str):
    """Enables a user unit.

    :param me: The currently handled twig.

    :param unit: The unit name.
    """
    return me.run(
        'systemctl', '--user', 'enable', unit)
