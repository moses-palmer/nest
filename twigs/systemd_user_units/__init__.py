"""Systemd user units.
"""

import os

from typing import Sequence

from .. import TWIGS, Twig, twig


@twig()
def main(me: Twig):
    pass

@main.checker
def is_enabled(me: Twig) -> bool:
    return all(
        enabled(me, unit)
        for unit in units())


@main.completer
def complete(me: Twig):
    for unit in (
            unit
            for unit in units()
            if not enabled(me, unit)):
        enable(me, unit)


def units() -> Sequence[str]:
    """Lists the names of all user units.

    :return: a list of unit names, including extension
    """
    return {
        p.name
        for t in TWIGS
        if t.enabled and (
            t.user_source / '.config' / 'systemd' / 'user').is_dir()
        for p in (t.user_source / '.config' / 'systemd' / 'user').iterdir()
        if p.is_file()}


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
